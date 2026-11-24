"""Long-context coding eval: tasks on a small project (shopkit) whose rules sit far above the request.

    python eval/run_longctx.py --check                    # every reference answer must pass its tests (no model)
    python eval/run_longctx.py --models inkling-q4,iq3    # both variants, both modes, all tasks
    python eval/run_longctx.py --summarize eval/out/<run>

Each task is asked twice: "short" (the project's files only, ~3K tokens) and "long" (the same files with ~18K tokens of
unrelated standard-library code between the rules and the request). The rules the task depends on (money rounding,
discount codes, tax, shipping, line limits) are in the files at the top; stock.py sits in the middle of the filler;
orders.py and the request come last. The difference between a model's short and long scores is what distance costs it.

The answer gives whole files (```python blocks starting with "# file: shopkit/<name>.py"). They are written into a
copy of the project and the task's hidden tests run against it, one test per process, as in run_eval.py.
"""
import argparse
import importlib.util
import json
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import run_eval as E

HERE = Path(__file__).resolve().parent / "longctx"
PROJECT = HERE / "project"
VENDOR = HERE / "vendor"

# The order the files appear in, top to bottom. "@name" is a filler file from vendor/, left out of the short variant.
LAYOUT = ["shopkit/events.py", "shopkit/money.py", "shopkit/codes.py", "shopkit/config.py", "@textwrap.py",
          "shopkit/stock.py", "@shlex.py", "@calendar.py", "shopkit/orders.py"]
VARIANTS = ("short", "long")

HEAD = ("You are working on the Python project below. Each file starts with a line `### FILE: <path>`. The files "
        "under vendor/ are third-party code that shopkit does not use.\n\n")
TAIL = ("\n\nReply with one ```python code block for each file you create or change. The first line of each block "
        "must be `# file: <path>`, and the block must hold the complete new contents of that file. Use only the "
        "standard library.")
FILE_RE = re.compile(r"^\s*#\s*file:\s*(\S+)\s*$", re.I)
SAFE_PATH = re.compile(r"shopkit/[a-z_][a-z0-9_]*\.py")


def load_tasks(filter_ids=None):
    out = []
    for p in sorted((HERE / "tasks").glob("[0-9][0-9]_*.py")):
        if filter_ids and p.stem[:2] not in filter_ids and p.stem not in filter_ids:
            continue
        spec = importlib.util.spec_from_file_location(f"lc_{p.stem}", p)
        src = p.read_text(encoding="utf-8")
        meta = {}
        # read PROMPT, DEFAULT_FILE, REPLACE and PATCHES without importing the tests (they import shopkit)
        head = src.split("\nfrom shopkit", 1)[0].split("\nfrom datetime", 1)[0].split("\nimport re\n", 1)[0] \
            .split("\nfrom pathlib", 1)[0]
        exec(compile(head, str(p), "exec"), meta)
        out.append({"id": p.stem, "path": p, "prompt": meta["PROMPT"].strip(), "default": meta["DEFAULT_FILE"],
                    "replace": meta.get("REPLACE", {}), "patches": meta.get("PATCHES", {})})
    return out


def project_files(task):
    """The project as this task sees it: {path: text}, with the task's replacements and patches applied."""
    files = {p: (PROJECT / p).read_text(encoding="utf-8") for p in LAYOUT if not p.startswith("@")}
    files["shopkit/__init__.py"] = ""
    for path, text in task["replace"].items():
        files[path] = (HERE / "variants" / text[1:]).read_text(encoding="utf-8") if text.startswith("@") else text
    for path, pairs in task["patches"].items():
        for old, new in pairs:
            if old not in files[path]:
                raise SystemExit(f"{task['id']}: patch text not found in {path}")
            files[path] = files[path].replace(old, new, 1)
    return files


def build_prompt(task, variant):
    files = project_files(task)
    parts = []
    for entry in LAYOUT:
        if entry.startswith("@"):
            if variant == "long":
                parts.append(f"### FILE: vendor/{entry[1:]}\n{(VENDOR / entry[1:]).read_text(encoding='utf-8')}")
        else:
            parts.append(f"### FILE: {entry}\n{files[entry]}")
    return HEAD + "\n\n".join(parts) + "\n\n### TASK\n" + task["prompt"] + TAIL


def answer_files(text, default):
    """{path: contents} from the answer's code blocks. A block without a `# file:` line goes to the task's file."""
    return answer_files_how(text, default)[0]


def answer_files_how(text, default):
    """(files, how): how is "fenced", "unfenced" (the files as `# file:` sections with no ``` fences, the way the
    prompt lays them out) or "none"."""
    out = {}
    blocks = re.findall(r"```(?:python|py|python3)?[ \t]*\n(.*?)```", text or "", re.S)
    how = "fenced"
    if not blocks:
        m = re.search(r"```(?:python|py|python3)?[ \t]*\n(.*)", text or "", re.S)   # cut off before the fence
        blocks = [m.group(1)] if m else []
    if not blocks:
        parts = re.split(r"(?im)^(?=\s*#\s*file:\s*\S+\s*$)", text or "")
        blocks = [p for p in parts if FILE_RE.match(p.split("\n", 1)[0])]
        how = "unfenced" if blocks else "none"
    for b in blocks:
        lines = b.split("\n")
        first = next((i for i, l in enumerate(lines) if l.strip()), None)
        m = FILE_RE.match(lines[first]) if first is not None else None
        if m:
            path = m.group(1).strip("`'\"").replace("\\", "/").lstrip("./")
            body = "\n".join(lines[first + 1:])
        else:
            path, body = default, b
        if SAFE_PATH.fullmatch(path) and (path not in out or len(body) > len(out[path])):
            out[path] = body
    return out, (how if out else "none")


def grade(task, answer_text, work, timeout):
    import shutil
    shutil.rmtree(work, ignore_errors=True)
    files = project_files(task)
    changed, how = answer_files_how(answer_text, task["default"])
    files.update(changed)
    for path, text in files.items():
        (work / path).parent.mkdir(parents=True, exist_ok=True)
        (work / path).write_text(text, encoding="utf-8")
    res = E.run_tests(task, work, timeout)
    res["files"] = sorted(changed)
    res["format"] = how
    return res


def regrade(run_dir, timeout):
    """Grade a run's saved answers again (after a change to the answer parser), rewriting results.jsonl."""
    run_dir = Path(run_dir)
    tasks = {t["id"]: t for t in load_tasks()}
    path = run_dir / "results.jsonl"
    recs = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l]
    for r in recs:
        work = run_dir / "work" / r["model"] / r["mode"] / r["variant"] / r["task"]
        if not (work / "answer.md").exists():
            continue
        saved = (work / "answer.md").read_text(encoding="utf-8")
        content = saved.split("</reasoning>\n\n", 1)[1] if saved.startswith("<reasoning>") else saved
        res = grade(tasks[r["task"]], content, work, timeout)
        (work / "answer.md").write_text(saved, encoding="utf-8")
        r.update(passed=res["passed"], total=res["total"], failures=res["failures"],
                 import_error=res["import_error"], files=res["files"], format=res["format"])
    path.write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")
    summarize(run_dir)


def check(args):
    bad = 0
    for t in load_tasks(args.tasks):
        ref = (HERE / "reference" / (t["id"] + ".md")).read_text(encoding="utf-8")
        r = grade(t, ref, E.HERE / "out" / "_lccheck" / t["id"], args.test_timeout)
        ok = r["total"] and r["passed"] == r["total"]
        # the unfixed project must fail, or the task tests nothing
        r0 = grade(t, "", E.HERE / "out" / "_lccheck" / (t["id"] + "-unfixed"), args.test_timeout)
        broken = not (r0["total"] and r0["passed"] == r0["total"])
        bad += not (ok and broken)
        sizes = {v: len(build_prompt(t, v)) for v in VARIANTS}
        print(f"  {'ok ' if ok and broken else 'BAD'} {t['id']}: reference {r['passed']}/{r['total']}, "
              f"unfixed {r0['passed']}/{r0['total']}; prompt {sizes['short']:,} / {sizes['long']:,} chars "
              f"{r['import_error'] or ''}{'' if ok else json.dumps(r['failures'])}")
    import shutil
    shutil.rmtree(E.HERE / "out" / "_lccheck", ignore_errors=True)
    print("every task checks out" if not bad else f"{bad} task(s) are wrong")
    return 1 if bad else 0


def ask(port, content, mode, max_tokens, timeout):
    body = {"messages": [{"role": "user", "content": content}], "max_tokens": max_tokens, "temperature": 0,
            **E.MODES[mode]}
    req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        out = json.load(r)
    return out, time.time() - t0


def run(args):
    run_dir = Path(args.out) if args.out else E.HERE / "out" / ("lc-" + time.strftime("%Y%m%d-%H%M%S"))
    run_dir.mkdir(parents=True, exist_ok=True)
    results = run_dir / "results.jsonl"
    todo = load_tasks(args.tasks)
    (run_dir / "run.json").write_text(json.dumps({
        "kind": "longctx", "models": args.models, "modes": args.modes, "variants": args.variants,
        "tasks": [t["id"] for t in todo], "temperature": 0, "started": time.strftime("%Y-%m-%d %H:%M:%S"),
        "max_tokens": {"off": args.max_tokens_off, "minimum": args.max_tokens_think}}, indent=1), encoding="utf-8")
    print(f"run folder: {run_dir}")
    for model in args.models:
        print(f"== {model}: starting the server ...", flush=True)
        proc, ready_s = E.start_server(model, args.port, run_dir)
        print(f"   ready after {ready_s:.0f} s", flush=True)
        try:
            for mode in args.modes:
                for variant in args.variants:
                    for t in todo:
                        rec = {"model": model, "mode": mode, "variant": variant, "task": t["id"]}
                        max_tokens = args.max_tokens_off if mode == "off" else args.max_tokens_think
                        try:
                            out, wall = ask(args.port, build_prompt(t, variant), mode, max_tokens, args.request_timeout)
                        except (urllib.error.URLError, OSError, ValueError) as e:
                            detail = e.read().decode(errors="replace")[:300] if hasattr(e, "read") else ""
                            rec.update(error=f"request failed: {e} {detail}"[:400], passed=0, total=None)
                            print(f"   {mode:8s} {variant:5s} {t['id']:20s} request failed: {e} {detail[:150]}",
                                  flush=True)
                            with results.open("a", encoding="utf-8") as f:
                                f.write(json.dumps(rec) + "\n")
                            if proc.poll() is not None:
                                print("   the server died: restarting it", flush=True)
                                E.stop_server(proc)
                                proc, _ = E.start_server(model, args.port, run_dir)
                            continue
                        msg = out["choices"][0]["message"]
                        content, reasoning = msg.get("content") or "", msg.get("reasoning_content") or ""
                        work = run_dir / "work" / model / mode / variant / t["id"]
                        res = grade(t, content, work, args.test_timeout)
                        usage, tim = out.get("usage") or {}, out.get("timings") or {}
                        rec.update(passed=res["passed"], total=res["total"], failures=res["failures"],
                                   import_error=res["import_error"], files=res["files"], format=res["format"],
                                   finish=out["choices"][0].get("finish_reason"),
                                   prompt_tokens=usage.get("prompt_tokens"),
                                   completion_tokens=usage.get("completion_tokens"), reasoning_chars=len(reasoning),
                                   decode_tps=tim.get("predicted_per_second"),
                                   prompt_tps=tim.get("prompt_per_second"), wall_s=round(wall, 2))
                        (work / "answer.md").write_text((f"<reasoning>\n{reasoning}\n</reasoning>\n\n" if reasoning
                                                         else "") + content, encoding="utf-8")
                        with results.open("a", encoding="utf-8") as f:
                            f.write(json.dumps(rec) + "\n")
                        flag = "PASS" if res["total"] and res["passed"] == res["total"] else "fail"
                        print(f"   {mode:8s} {variant:5s} {t['id']:20s} {flag} {res['passed']}/{res['total']}  "
                              f"prompt {rec['prompt_tokens']}, {rec['completion_tokens']} tok, {wall:.1f} s, "
                              f"finish={rec['finish']}, files={','.join(res['files']) or '-'}"
                              f"{'  ' + res['import_error'][:70] if res['import_error'] else ''}", flush=True)
        finally:
            E.stop_server(proc)
    summarize(run_dir)


def summarize(run_dir):
    run_dir = Path(run_dir)
    recs = [json.loads(l) for l in (run_dir / "results.jsonl").read_text(encoding="utf-8").splitlines() if l]
    meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    full = lambda r: bool(r.get("total")) and r["passed"] == r["total"]
    keys = list(dict.fromkeys((r["model"], r["mode"], r["variant"]) for r in recs))
    lines = [f"# Long-context coding eval: {run_dir.name}", "",
             f"Started {meta['started']}. Greedy, one request per task and variant. max_tokens: "
             f"{meta['max_tokens']['off']} with thinking off, {meta['max_tokens']['minimum']} at minimum effort.", "",
             "| Model | Mode | Variant | Tasks passed | Tests passed | Prompt tokens (median) | Cut off | "
             "Files without ``` fences | Tokens out (median) | Prompt tok/s (median) | Time |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for k in keys:
        rs = [r for r in recs if (r["model"], r["mode"], r["variant"]) == k]
        med = lambda f: statistics.median([r[f] for r in rs if r.get(f) is not None] or [0])
        lines.append(f"| {k[0]} | {k[1]} | {k[2]} | {sum(map(full, rs))}/{len(rs)} | "
                     f"{sum(r['passed'] for r in rs)}/{sum(r.get('total') or 0 for r in rs)} | "
                     f"{med('prompt_tokens'):,.0f} | {sum(r.get('finish') == 'length' for r in rs)} | "
                     f"{sum(r.get('format') == 'unfenced' for r in rs)} | "
                     f"{med('completion_tokens'):,.0f} | {med('prompt_tps'):,.0f} | "
                     f"{sum(r.get('wall_s') or 0 for r in rs) / 60:.1f} min |")
    tasks = list(dict.fromkeys(r["task"] for r in recs))
    lines += ["", "Per task (tests passed / total):", "",
              "| Task | " + " | ".join(f"{m} {d} {v}" for m, d, v in keys) + " |", "|---|" + "---|" * len(keys)]
    for tid in tasks:
        cells = []
        for k in keys:
            r = next((x for x in recs if (x["model"], x["mode"], x["variant"]) == k and x["task"] == tid), None)
            cells.append("-" if r is None else ("**" if full(r) else "") + f"{r['passed']}/{r.get('total') or '?'}"
                         + ("**" if full(r) else ""))
        lines.append(f"| {tid} | " + " | ".join(cells) + " |")
    (run_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="check every task's reference and unfixed project, and exit")
    ap.add_argument("--summarize", metavar="RUN_DIR")
    ap.add_argument("--regrade", metavar="RUN_DIR", help="grade a run's saved answers again and rebuild its summary")
    ap.add_argument("--show-prompt", metavar="TASK", help="print a task's long prompt and exit")
    ap.add_argument("--models", default="inkling-q4,iq3", help="comma-separated: " + ", ".join(E.MODELS))
    ap.add_argument("--modes", default="off,minimum", help="comma-separated: " + ", ".join(E.MODES))
    ap.add_argument("--variants", default="short,long")
    ap.add_argument("--tasks", default=None)
    ap.add_argument("--port", type=int, default=8093)
    ap.add_argument("--out", default=None)
    ap.add_argument("--max-tokens-off", type=int, default=4000)
    ap.add_argument("--max-tokens-think", type=int, default=8000)
    ap.add_argument("--request-timeout", type=float, default=900)
    ap.add_argument("--test-timeout", type=float, default=30)
    args = ap.parse_args()
    args.tasks = set(args.tasks.split(",")) if args.tasks else None
    if args.check:
        sys.exit(check(args))
    if args.summarize:
        summarize(args.summarize)
        return
    if args.regrade:
        regrade(args.regrade, args.test_timeout)
        return
    if args.show_prompt:
        print(build_prompt(load_tasks({args.show_prompt})[0], "long"))
        return
    split = lambda s: [x.strip() for x in s.split(",") if x.strip()]
    args.models, args.modes, args.variants = split(args.models), split(args.modes), split(args.variants)
    for m in args.models:
        if m not in E.MODELS:
            sys.exit(f"unknown model {m!r}")
    for v in args.variants:
        if v not in VARIANTS:
            sys.exit(f"unknown variant {v!r}")
    run(args)


if __name__ == "__main__":
    main()
