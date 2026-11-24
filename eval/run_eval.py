"""Single-shot coding eval: each task is one chat request; the code in the answer runs against the task's hidden tests.

    python eval/run_eval.py --check                       # run every reference solution against its tests (no model)
    python eval/run_eval.py                               # all models x both modes x all tasks
    python eval/run_eval.py --models inkling --modes off --tasks 01,05
    python eval/run_eval.py --summarize eval/out/<run>    # rebuild summary.md from a run's results.jsonl

Each model's server is started on --port with its setup run config, used for every task and mode, then stopped (the
server and its engine), so only one model is on the GPU at a time. Model code runs in a child Python (-I) in a work
folder under the run's output, one test per process with a time limit. It is not sandboxed beyond that.
"""
import argparse
import importlib.util
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TERM = ROOT / "terminal"
PY = TERM / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

MODELS = {   # name -> setup's run config
    "inkling": TERM / "strata-inkling-ud-q2_k_xl.json",
    "coder": TERM / "strata-coder-iq1_m.json",
    "iq3": TERM / "strata-iq3_xxs.json",
}
ENGINES = ("strata.exe", "strata-poly.exe") if os.name == "nt" else ("strata", "strata-poly")

# The two modes. "minimum" is the local reasoning effort: 0.1 on Inkling 2, low on the Qwen models.
MODES = {
    "off": {"chat_template_kwargs": {"enable_thinking": False}},
    "minimum": {"reasoning_effort": "minimum"},
}

INSTRUCTIONS = ("Solve the following programming task in Python 3.12, using only the standard library. Reply with "
                "one ```python code block that holds the complete module (imports included), and nothing after it.\n")

DRIVER = r'''
import builtins, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I leaves the script's folder off the path

def raises(exc, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc:
        return
    except BaseException as e:
        raise AssertionError(f"expected {exc.__name__}, got {type(e).__name__}: {e}") from None
    raise AssertionError(f"expected {exc.__name__}, nothing was raised")

builtins.raises = raises
out = {}
try:
    import task_tests as t
except BaseException as e:
    out["import_error"] = f"{type(e).__name__}: {e}"[:500]
else:
    names = [n for n, f in vars(t).items() if n.startswith("test_") and callable(f)]
    if sys.argv[1] == "--list":
        out["tests"] = names
    else:
        try:
            getattr(t, sys.argv[1])()
            out["ok"] = True
        except BaseException as e:
            out["ok"] = False
            out["error"] = (f"{type(e).__name__}: {e}"[:300] or type(e).__name__)
print("@@RESULT@@" + json.dumps(out))
'''


def tasks(filter_ids=None):
    out = []
    for p in sorted((HERE / "tasks").glob("[0-9][0-9]_*.py")):
        if filter_ids and p.stem[:2] not in filter_ids and p.stem not in filter_ids:
            continue
        spec = importlib.util.spec_from_file_location("prompt_only", p)
        src = p.read_text(encoding="utf-8")
        prompt = re.search(r"PROMPT = r'''(.*?)'''", src, re.S).group(1).strip()
        out.append({"id": p.stem, "path": p, "prompt": prompt})
    return out


def run_driver(work, arg, timeout):
    try:
        r = subprocess.run([str(PY), "-I", "driver.py", arg], cwd=work, capture_output=True, text=True,
                           timeout=timeout, encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timeout after {timeout} s"}
    for line in r.stdout.splitlines()[::-1]:
        if line.startswith("@@RESULT@@"):
            return json.loads(line[len("@@RESULT@@"):])
    return {"ok": False, "error": ("no result; " + (r.stderr or r.stdout)[-300:]).strip()}


def test_code(task, code, work, timeout):
    """Run every test of `task` against `code`: {"passed", "total", "failures", "import_error"}."""
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    (work / "solution.py").write_text(code, encoding="utf-8")
    shutil.copy(task["path"], work / "task_tests.py")
    (work / "driver.py").write_text(DRIVER, encoding="utf-8")
    listed = run_driver(work, "--list", timeout)
    if "tests" not in listed:
        return {"passed": 0, "total": None, "failures": {},
                "import_error": listed.get("import_error") or listed.get("error")}
    failures = {}
    for name in listed["tests"]:
        r = run_driver(work, name, timeout)
        if not r.get("ok"):
            failures[name] = r.get("error") or r.get("import_error") or "failed"
    n = len(listed["tests"])
    return {"passed": n - len(failures), "total": n, "failures": failures, "import_error": None}


def extract_code(text):
    blocks = re.findall(r"```(?:python|py|python3)?[ \t]*\n(.*?)```", text or "", re.S)
    if blocks:
        return max(blocks, key=len)
    m = re.search(r"```(?:python|py|python3)?[ \t]*\n(.*)", text or "", re.S)   # an unclosed block (cut off)
    return m.group(1) if m else (text or "")


def check(args):
    bad = 0
    for t in tasks(args.tasks):
        ref = HERE / "reference" / (t["id"] + ".py")
        r = test_code(t, ref.read_text(encoding="utf-8"), HERE / "out" / "_check" / t["id"], args.test_timeout)
        ok = r["total"] and r["passed"] == r["total"]
        bad += not ok
        print(f"  {'ok ' if ok else 'BAD'} {t['id']}: {r['passed']}/{r['total']} "
              f"{r['import_error'] or ''}{'' if ok else json.dumps(r['failures'])}")
    shutil.rmtree(HERE / "out" / "_check", ignore_errors=True)
    print("every reference passes" if not bad else f"{bad} reference(s) fail")
    return 1 if bad else 0


# ---- the server -------------------------------------------------------------------------------------------------

def engines_running():
    if os.name != "nt":
        return []
    r = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True)
    return [l.split(",")[0].strip('"') for l in r.stdout.splitlines() if l.split(",")[0].strip('"') in ENGINES]


def stop_server(proc):
    if proc and proc.poll() is None:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
        else:
            proc.kill()
    for exe in ENGINES:            # an engine the tree kill missed
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/IM", exe], capture_output=True)
    time.sleep(3)


def start_server(model, port, log_dir):
    if engines_running():
        sys.exit(f"an engine is already running ({', '.join(engines_running())}): stop it first")
    cfg = MODELS[model]
    if not cfg.exists():
        sys.exit(f"no run config for {model}: {cfg}")
    log = open(log_dir / f"server-{model}.log", "w", encoding="utf-8")
    proc = subprocess.Popen([str(PY), str(TERM / "serve" / "server.py"), "--engine", "strata", "--config", str(cfg),
                             "--port", str(port)], cwd=TERM, stdout=log, stderr=subprocess.STDOUT)
    t0 = time.time()
    while time.time() - t0 < 900:
        if proc.poll() is not None:
            sys.exit(f"the {model} server exited ({proc.returncode}): see {log.name}")
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=3) as r:
                if r.status == 200:
                    return proc, time.time() - t0
        except OSError:
            pass
        time.sleep(3)
    stop_server(proc)
    sys.exit(f"the {model} server was not ready after 15 minutes")


def ask(port, prompt, mode, max_tokens, timeout):
    body = {"messages": [{"role": "user", "content": INSTRUCTIONS + "\n" + prompt}], "max_tokens": max_tokens,
            "temperature": 0, **MODES[mode]}
    req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        out = json.load(r)
    return out, time.time() - t0


# ---- the run ----------------------------------------------------------------------------------------------------

def run(args):
    run_dir = Path(args.out) if args.out else HERE / "out" / time.strftime("%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    results = run_dir / "results.jsonl"
    todo = tasks(args.tasks)
    meta = {"models": args.models, "modes": args.modes, "tasks": [t["id"] for t in todo],
            "max_tokens": {"off": args.max_tokens_off, "minimum": args.max_tokens_think}, "temperature": 0,
            "started": time.strftime("%Y-%m-%d %H:%M:%S"),
            "configs": {m: json.loads(MODELS[m].read_text()).get("args") for m in args.models if MODELS[m].exists()}}
    (run_dir / "run.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"run folder: {run_dir}")
    for model in args.models:
        print(f"== {model}: starting the server ...", flush=True)
        proc, ready_s = start_server(model, args.port, run_dir)
        print(f"   ready after {ready_s:.0f} s", flush=True)
        try:
            for mode in args.modes:
                for t in todo:
                    max_tokens = args.max_tokens_off if mode == "off" else args.max_tokens_think
                    rec = {"model": model, "mode": mode, "task": t["id"]}
                    try:
                        out, wall = ask(args.port, t["prompt"], mode, max_tokens, args.request_timeout)
                    except (urllib.error.URLError, OSError, ValueError) as e:
                        rec.update(error=f"request failed: {e}"[:300], passed=0, total=None)
                        print(f"   {mode:8s} {t['id']:22s} request failed: {e}", flush=True)
                        with results.open("a", encoding="utf-8") as f:
                            f.write(json.dumps(rec) + "\n")
                        if proc.poll() is not None:
                            print("   the server died: restarting it", flush=True)
                            stop_server(proc)
                            proc, _ = start_server(model, args.port, run_dir)
                        continue
                    msg = out["choices"][0]["message"]
                    content, reasoning = msg.get("content") or "", msg.get("reasoning_content") or ""
                    code = extract_code(content)
                    work = run_dir / "work" / model / mode / t["id"]
                    res = test_code(t, code, work, args.test_timeout)
                    tim, usage = out.get("timings") or {}, out.get("usage") or {}
                    rec.update(passed=res["passed"], total=res["total"], failures=res["failures"],
                               import_error=res["import_error"], finish=out["choices"][0].get("finish_reason"),
                               completion_tokens=usage.get("completion_tokens"),
                               prompt_tokens=usage.get("prompt_tokens"), reasoning_chars=len(reasoning),
                               content_chars=len(content), decode_tps=tim.get("predicted_per_second"),
                               wall_s=round(wall, 2))
                    (work / "answer.md").write_text((f"<reasoning>\n{reasoning}\n</reasoning>\n\n" if reasoning
                                                     else "") + content, encoding="utf-8")
                    with results.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(rec) + "\n")
                    total = res["total"] if res["total"] is not None else "?"
                    flag = "PASS" if res["total"] and res["passed"] == res["total"] else "fail"
                    print(f"   {mode:8s} {t['id']:22s} {flag} {res['passed']}/{total}  "
                          f"{rec['completion_tokens']} tok, {wall:.1f} s, finish={rec['finish']}"
                          f"{'  ' + res['import_error'][:80] if res['import_error'] else ''}", flush=True)
        finally:
            stop_server(proc)
    summarize(run_dir)


def summarize(run_dir):
    run_dir = Path(run_dir)
    recs = [json.loads(l) for l in (run_dir / "results.jsonl").read_text(encoding="utf-8").splitlines() if l]
    meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    keys = list(dict.fromkeys((r["model"], r["mode"]) for r in recs))
    task_ids = list(dict.fromkeys(r["task"] for r in recs))
    full = lambda r: bool(r.get("total")) and r["passed"] == r["total"]
    lines = [f"# Coding eval: {run_dir.name}", "",
             f"Started {meta['started']}. Greedy (temperature 0), one request per task. max_tokens: "
             f"{meta['max_tokens']['off']} with thinking off, {meta['max_tokens']['minimum']} with minimum effort.", "",
             "| Model | Mode | Tasks passed | Tests passed | Cut off (length) | No code / import error | "
             "Tokens (median) | Reasoning chars (median) | Decode tok/s (median) | Time (total) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for model, mode in keys:
        rs = [r for r in recs if r["model"] == model and r["mode"] == mode]
        tests_p = sum(r["passed"] for r in rs)
        tests_t = sum(r["total"] or 0 for r in rs)
        med = lambda k: statistics.median([r[k] for r in rs if r.get(k) is not None] or [0])
        lines.append(f"| {model} | {mode} | {sum(map(full, rs))}/{len(rs)} | {tests_p}/{tests_t} | "
                     f"{sum(r.get('finish') == 'length' for r in rs)} | "
                     f"{sum(bool(r.get('import_error') or r.get('error')) for r in rs)} | "
                     f"{med('completion_tokens'):.0f} | {med('reasoning_chars'):.0f} | {med('decode_tps'):.1f} | "
                     f"{sum(r.get('wall_s') or 0 for r in rs) / 60:.1f} min |")
    lines += ["", "Per task (tests passed / total):", "",
              "| Task | " + " | ".join(f"{m} {d}" for m, d in keys) + " |",
              "|---|" + "---|" * len(keys)]
    for tid in task_ids:
        cells = []
        for k in keys:
            r = next((x for x in recs if (x["model"], x["mode"]) == k and x["task"] == tid), None)
            cells.append("-" if r is None else ("**" if full(r) else "") + f"{r['passed']}/{r.get('total') or '?'}"
                         + ("**" if full(r) else ""))
        lines.append(f"| {tid} | " + " | ".join(cells) + " |")
    (run_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="run the reference solutions against their tests and exit")
    ap.add_argument("--summarize", metavar="RUN_DIR", help="rebuild summary.md from a run folder and exit")
    ap.add_argument("--models", default="inkling,coder,iq3", help="comma-separated: " + ", ".join(MODELS))
    ap.add_argument("--modes", default="off,minimum", help="comma-separated: " + ", ".join(MODES))
    ap.add_argument("--tasks", default=None, help="comma-separated task numbers or names (default: all)")
    ap.add_argument("--port", type=int, default=8093)
    ap.add_argument("--out", default=None, help="run folder (default: eval/out/<date-time>)")
    ap.add_argument("--max-tokens-off", type=int, default=3000)
    ap.add_argument("--max-tokens-think", type=int, default=8000)
    ap.add_argument("--request-timeout", type=float, default=900)
    ap.add_argument("--test-timeout", type=float, default=30, help="seconds per test")
    args = ap.parse_args()
    args.tasks = set(args.tasks.split(",")) if args.tasks else None
    if args.check:
        sys.exit(check(args))
    if args.summarize:
        summarize(args.summarize)
        return
    args.models = [m.strip() for m in args.models.split(",") if m.strip()]
    args.modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    for m in args.models:
        if m not in MODELS:
            sys.exit(f"unknown model {m!r}: {', '.join(MODELS)}")
    for m in args.modes:
        if m not in MODES:
            sys.exit(f"unknown mode {m!r}: {', '.join(MODES)}")
    run(args)


if __name__ == "__main__":
    main()
