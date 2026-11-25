# Where this work stands (2026-11-24)

Notes for resuming. This isn't part of PolyStrata's docs. It lives only on the `local-setup` branch (pushed to `origin`), so keep it out of pull requests to `upstream`.

## The decision

**Plain PolyStrata is the base.** It replaces both porting UnbiasedStrata 2 to Windows (`PSPLAN.md`) and keeping the old UnbiasedStrata 1 fork (`D:\UnbiasedStrata`). The target is Qwen3.8 Flash-Next **Coder IQ1_M** and **IQ3_XXS** on Windows with an **RTX 5070 Ti (16 GB)** and 64 GB of RAM. Qwen3.6 isn't needed.

Why: weekly upstream releases with Windows and RTX 50 support, ~20% faster prompt reading, and token-by-token streaming. Together they outweigh the old fork's ~18% decode lead.

The full comparison, method and every run are in `mtnrbq/UnbiasedStrataPS` (`D:\UnbiasedStrataPS`): see `plainpolySQ.md` (start with the "Head-to-head so far" section), with the benchmark scripts in `bench/`.

## This checkout

- **The clone:** `D:\polystrata`.
  - `origin` is `mtnrbq/PolyStrata` (your fork) and `upstream` is `simplexai-labs/PolyStrata`. The repo moved there from `VecSzn/PolyStrata`, which redirects.
  - `main` is at `v0.2.19-poly.1` (`d1f711e11`), with no local commits, and matches `origin/main`.
  - The working branch is **`local-setup`**, which tracks `origin/local-setup`. It's `main` plus this file, the `justfile` and one local server change (the `minimum` reasoning effort, below). Put changes meant for upstream on their own small branches off `main`, not here.
  - **`coding-eval`** (local only) is where the coding evals were started. It has been merged into `local-setup`, which now holds them (see "Coding eval" below). It can be deleted.
  - Setup's outputs are ignored by git.
- **The `justfile`** (`just --list`) holds this PC's shortcuts: `serve`, `serve-lan` (needs `$env:STRATA_API_KEY`), `serve-iq3`, `serve-inkling`, `setup-coder`, `setup-iq3`, `setup-inkling`, `check`, `update`, `log`, `bench`, `eval` and `eval-long`. Any of them can take another port, e.g. `just port=8093 serve-inkling`. `just` and `uv` are in `%LOCALAPPDATA%\Microsoft\WinGet\Links`, which has to be on the user PATH.
- **Python:** `terminal\.venv` (Python 3.12.13). It was made with `uv venv --seed --python 3.12`, and `requirements.txt` was installed with `uv pip`. `START-HERE.bat` uses it instead of installing Python.
- **Setup has been run for both Qwen models,** non-interactively with `just setup-coder` and `just setup-iq3`. Both use 64K context, an 8-bit KV cache, no vision, experimental "speed projection" off (it's a refusal-direction control vector, not a speed setting) and **`--vram-reserve-mib 700`**.
  - **Coder IQ1_M:** it reused every file, with no downloads and no pack rebuilt. It wrote `terminal\strata-coder-iq1_m.json` (the earlier one is `.json.bak`) and `terminal\run-coder-iq1_m.bat`. The engine arguments match the `-r700` test config exactly.
  - **IQ3_XXS:** it checked both shards (SHA-256) without downloading, and built its own pack, `C:\Strata-data\packs\iq3_xxs` (1.5 GB). It wrote `terminal\strata-iq3_xxs.json` and `terminal\run-iq3_xxs.bat`. It uses the general expert profile, `terminal\data\expert-profile.bin`, and the Coder's draft head.
- **Inkling 2 Mini UD-Q4_K_XL** (experimental) is set up with `just setup-inkling` and served with `just serve-inkling`.
  - Settings: 64K context (32K until 2026-11-24, setup's choice for 16 GB), no vision, setup's own VRAM reserve (700 hasn't been tried on this engine).
  - It downloaded 17.6 GB (SHA-256 checked) to `C:\Strata-data\models\inkling-UD-Q4_K_XL\`, with its tokenizer pack in `C:\Strata-data\packs\inkling-ud-q4_k_xl`.
  - It wrote `terminal\strata-inkling-ud-q4_k_xl.json` and `terminal\run-inkling-ud-q4_k_xl.bat`. They take one request at a time (`"parallel": 1`) and keep a conversation cache in RAM of up to 8 GB.
  - 2,499 of its 3,072 experts fit in VRAM (12.0 GiB); the rest are computed on the CPU. Setup therefore added its small-card settings: `--attn-requant q5_0 --loop-bf16 --tail-skip 4 --expert-swaps 0`.
- **UD-Q2_K_XL was tried first, then removed (2026-11-24),** because Q4 codes better (see "Coding eval").
  - All of Q2's experts fit in VRAM (7.3 GiB), with no small-card settings.
  - Its model, pack, run config, start script and log were deleted. `just setup-inkling --model UD-Q2_K_XL` would bring it back (9.1 GB).
- **The engines:**
  - Qwen runs on `terminal\engine\strata.exe`, Strata **0.1.66**. It's a prebuilt, signed package from the update feed, built for sm_75/86/89/120 plus PTX with **CUDA 13.0**, and needs driver 580.65 or newer (installed: 617.42). The CUDA runtime comes from the venv (`nvidia-cuda-runtime` 13.0.96).
  - Inkling runs on `terminal\engine-poly\strata-poly.exe`, PolyStrata's second engine. It's the ready-made release build for this checkout's source (`strata-poly-windows-x64-605522f294c7a21a.zip`, checksum verified), CUDA 13.0, sm_75 to sm_120. When the source changes, setup fetches a new one.
- **Local server change: a `minimum` reasoning effort** (`terminal\serve\frontend.py`, `server.py`, with tests).
  - Inkling 2's template takes an effort from 0 to 0.99: none 0.0, minimal 0.1, low 0.2, medium 0.7, high 0.9, xhigh/max 0.99. The server only accepts names, and it reads "minimal" as thinking off.
  - `"reasoning_effort": "minimum"` sends 0.1 to Inkling, and acts as `low` on the other models.
  - What a client gets on Inkling: nothing sent = 0.9; `low` = 0.2; `medium` = 0.7; `high` = 0.99; `none`/`minimal`/`enable_thinking: false` = thinking off; a number = HTTP 400.
  - On one question, lower effort did *not* give shorter reasoning (692 characters at minimum, 474 at low, 370 at the default). It hasn't been measured over several prompts.
  - `serve.test_server`'s `SharingTheGpu.test_before_load_reason_is_made_safe` fails on this PC with or without the change (400 instead of 503).

## Model data (shared with the old fork, so be careful)

| Model | Files | Pack | Draft head |
|---|---|---|---|
| Coder IQ1_M | `D:\Strata-data\models\coder-IQ1_M\` | `D:\Strata-data\packs\coder-iq1_m` | `D:\Strata-data\mtp\rt` (+ `mtp-q2_0.gguf`) |
| IQ3_XXS | `C:\Strata-data\models\IQ3_XXS\` | `C:\Strata-data\packs\iq3_xxs`; the old fork's `iq3-xxs` is a junction to it | the Coder's `rt` |
| Inkling 2 Mini UD-Q4_K_XL | `C:\Strata-data\models\inkling-UD-Q4_K_XL\` | `C:\Strata-data\packs\inkling-ud-q4_k_xl` (tokenizer only; the GGUF is read in place) | none |

- All four shards match PolyStrata's pinned sizes, and the packs are complete.
- **One IQ3_XXS pack for both:** `C:\Strata-data\packs\iq3-xxs` is a directory junction to PolyStrata's `iq3_xxs`. The two packs were byte-identical except for two things:
  - The old pack had `expert-profile.bin`, which the old fork reads from the pack when no `--expert-profile` is given. It was copied into `iq3_xxs`. It's identical to `terminal\data\expert-profile.bin`.
  - PolyStrata's `tokenizer\tokenizer.json` adds `"pre_sequence": null` and `"ignore_merges": false`. The old fork doesn't read those keys, but it hasn't been run through the link yet.
  - The old fork's own copy, `iq3-xxs.old`, was deleted on 2026-11-24. If the old fork ever fails through the link, remove it (`cmd /c rmdir C:\Strata-data\packs\iq3-xxs`) and rebuild the pack with the old fork's own tools.
- `mtp\tensors` (the 5 GB download the draft head was built from) has been deleted. It isn't needed.
- **If setup offers to move models into its data folder, answer "keep".**
- The old fork, `D:\UnbiasedStrata`, reads the same files, and it holds uncommitted work on its `inkling` branch. Don't change anything there.

## Best configuration measured

Setup's defaults **plus `--vram-reserve-mib 700`**, which is now in both setup run configs. Coder IQ1_M at 64K, greedy (measured with the test copy `terminal\strata-coder-iq1_m-r700.json`):

| | Decode tok/s | Prompt tok/s (~20K) | Expert slots |
|---|---|---|---|
| PolyStrata, setup's defaults | 100.6 | 3,693 | 3,543 |
| **PolyStrata + reserve 700** | **104.8** | **3,711** | 3,842 |
| Old fork (engine 0.1.58), for reference | ~129 | ~3,085 | 4,171 |

**IQ3_XXS** (2026-11-23, one run): setup's `strata-iq3_xxs.json` (reserve 700, 64K, 8-bit KV, the Coder's draft head), `just bench iq3-r700 D:\PolyStrata\terminal\strata-iq3_xxs.json` with `bench_greedy.py`:

| | Decode tok/s | Prompt tok/s (~20K) | Expert slots |
|---|---|---|---|
| PolyStrata IQ3_XXS + reserve 700 | 113.0 (99.9–130.7) | 3,364 | 4,788 |

- Against the Coder on the same settings, IQ3_XXS is ~8% faster at decode and ~9% slower at reading prompts.
- The hit rate was 80–87% on the coding prompts and 67% on one long prompt. The draft head was accepted for 257–281 of each 400 tokens.
- It hasn't been measured on the old fork. The output is in `D:\UnbiasedStrataPS\bench\out\bench-iq3-r700.txt`.

**Inkling 2 Mini** (2026-11-24, one run each): setup's run config (32K, setup's reserve), thinking off, `bench_greedy.py`. Q2 has since been removed:

| | Decode tok/s | Prompt tok/s (~23K) | Experts in VRAM |
|---|---|---|---|
| Inkling 2 Mini UD-Q2_K_XL | 121.7 (118.8–123.4) | 2,658 | all 3,072 (7.3 GiB) |
| Inkling 2 Mini UD-Q4_K_XL (setup's small-card settings) | 109.1 mean; 117.7–124.7 after the first two prompts | 2,618 | 2,499 of 3,072 (12.0 GiB) |

- It's the fastest of the three at decode, and steadier, because nothing is fetched from RAM. It reads prompts 20–30% slower than the Qwen models.
- Its tokenizer makes the long prompts ~23K tokens instead of ~20K, so prompt speeds don't compare exactly. It writes one token at a time, with no draft head.
- Chat, separate reasoning, and an OpenAI tool call (`finish_reason: tool_calls`) all worked.
- **Q4's first two prompts were slow** (47.9 and 96.1 tok/s), probably while its 17.6 GB file was first read into the OS file cache. Its median decode in the coding eval, which ran after that, was ~128 tok/s. Output: `bench-inkling-q4.txt`.
- It was run with the client pointed at `just port=8093 serve-inkling`, not through `ab-polystrata.ps1`, which only stops `strata.exe` and would leave `strata-poly.exe` running. The output is in `D:\UnbiasedStrataPS\bench\out\bench-inkling-q2.txt`.

**Inkling Q4 at a 64K context** (2026-11-24; `just setup-inkling` now passes `--context 65536`; the run config differs from the 32K one only in `--max-context`):

| | Decode tok/s | Prompt tok/s | Experts in VRAM |
|---|---|---|---|
| 32K (above) | 109.1 mean; 117.7–124.7 warm | 2,618 (~23K) | 2,499–2,599 at load (the log shows both), ~2,450–2,600 in use |
| 64K, first run | 93.5 mean; 113.9–118.4 after the first three prompts | 2,618 (~23K) | 2,597 at load, down to 2,343 during the long prompts |
| 64K, second run (same server) | 118.0 (115.2–121.5) | (cached, not measured) | 2,336–2,457 |
| 64K, one 48,944-token prompt | 74.6 after it (127 tokens only) | 2,505 | 2,359 |

- **A 64K context costs no measurable speed** at the benchmark's ~23K prompts: warm decode is 115–122 tok/s against 118–125 at 32K, within the run-to-run spread. Prompt reading is the same, 2,618 tok/s.
- The engine resizes the expert cache to the VRAM left as requests run; nothing is set aside for the extra 32K at load (2,597 experts either way). With the same ~23K prompts, though, the cache went ~100–250 experts lower at 64K than at 32K. Why isn't known; it didn't show in decode speed.
- **A 48,944-token prompt worked:** read at 2,505 tok/s (19.5 s), and the answer correctly summed up the first files. Decode after it was 74.6 tok/s, but over only 127 tokens.
- The first run's slow start (three prompts at 44–72 tok/s) was most likely the model file being read into the OS file cache again: the load took 18.9 s against ~8 s before.
- Output: `bench-inkling-q4-64k.txt`, `bench-inkling-q4-64k-run2.txt` and `bench-inkling-q4-64k-long.txt` (the 49K-token prompt, sent by a small one-off script from the session's scratchpad).

What else was tried:
- **Keep the 12 sm_120 speed switches on.** Turning them off (`STRATA_SM120_PERF=0`) cost 12% decode. `ADAPT_FETCH` alone (`STRATA_ADAPT_FETCH=0` to disable) is worth about 10%.
- **The old fork's tuning doesn't help on 0.1.66,** and `STRATA_ADAPT_OVERLAP=1` disables `ADAPT_FETCH`. That tuning was `--adapt-every 1 --adapt-swaps 80 --adapt-decay 0.97`, `--spec-min-p 0.70` and `STRATA_ADAPT_OVERLAP=1`.
- **Why decode is slower:** engine 0.1.66 holds a 1,280 MiB VRAM reserve on Windows (the WDDM floor), against 700 MiB on 0.1.58, and uses more memory around the cache. That means fewer expert slots, a 76–85% hit rate instead of 86–92%, and more PCIe reads.
- **The display was fine at 700 MiB,** though the 5070 Ti drives it. Setup's fallback if it freezes or goes black is `--vram-reserve-mib 1500`.
- **The Python server adds ~10–20 ms per request** (<1%). Streaming starts after ~93 ms, at the engine's full rate.

### Things to know

- **Sampling defaults:** when a request sets no `temperature`, the server applies the model card's settings: temperature 0.7, top_p 0.8, top_k 20, presence_penalty 1.5. `"temperature": 0` makes it fully greedy and drops the penalties.
- **Not bit-exact:** greedy output isn't identical from run to run, because the default `ADAPT_FETCH` isn't bit-exact. One benchmark prompt also ends at 105 tokens here, against 400 on the old fork.
- **Network access:** by default the server listens on `127.0.0.1:8080` only. For other machines, use `--host 0.0.0.0 --api-key <secret>`.
- **Engine log:** `terminal\strata-<model>.log`. It records each request's own speed ("400 generated in N ms"), the expert-cache hit rate, the slot count and the VRAM budget.

## Coding eval (2026-11-24)

`eval\run_eval.py` (`just eval`; how it works is in `eval\README.md`):
- **Tasks:** 18 Python tasks with 122 hidden tests. Every reference solution passes (`just eval --check`).
- **Method:** one greedy request per task (`temperature: 0`). The longest code block in the answer is run against the tests.
- **Modes:** thinking off (up to 3,000 tokens) and `reasoning_effort: "minimum"` (up to 8,000 tokens; 0.1 on Inkling, `low` on the Qwen models).
- **Run:** one run of each, 108 requests in ~36 minutes. The output is in `eval\out\20261124-121032\` (`summary.md`, every answer in `work\`).

| Model | Thinking off | Minimum effort | Off: median tokens, time | Minimum: median tokens, time |
|---|---|---|---|---|
| **IQ3_XXS** | **18/18** (117/117 tests) | 16/18 | 480, 1.8 min | 3,240, 11.8 min |
| Coder IQ1_M | 17/18 | 15/18 | 388, 1.6 min | 4,588, 13.0 min |
| Inkling 2 Mini UD-Q2_K_XL (since removed) | 13/18 | 15/18 | 377, 1.1 min | 1,116, 6.1 min |
| **Inkling 2 Mini UD-Q4_K_XL** (a separate run, `eval\out\20261124-130004\`) | 16/18 | **17/18** | 384, 1.5 min | 1,042, **4.8 min** |

- **Thinking made the Qwen models worse.** Neither passed anything with it that it failed without.
  - Every minimum-effort failure on all three models was reasoning that went in circles until it hit the token limit, with no code written: Inkling 06, 08 and 15, the Coder's 06 and 18, and IQ3's 06. The exception is IQ3's 15, which was a working algorithm with a docstring it couldn't decode (a non-raw backslash escape).
  - On the Qwen models the server's guard ended three loops early, after one token was repeated 256 times (`repeat_stop_tokens`).
  - The Qwen models' "minimum" is `low`, and they still thought for a median 10,000–16,000 characters, against ~2,700 for Inkling at 0.1.
- **Inkling is the reverse: thinking helps it.** With thinking off it wrote real bugs: a missing `nonlocal` (06), a mostly wrong glob matcher (15, 1 of 8), and valid versions with build metadata rejected (11). Minimum effort fixed 01, 11 and 08's escaping, but looped on the three hardest parsing tasks. It's the fastest, at ~135 tok/s against 93–110.
- **Inkling Q4 fixed most of Q2's bugs.** It passed 01, 06 and 11 with thinking off, and 06, 08 and 15 at minimum effort. Its three failures:
  - 08 with thinking off: one test, the same escaped-quote handling Q2 got wrong.
  - 15 with thinking off: still writing comments when it hit the 3,000-token limit, so the code was cut off.
  - 01 at minimum effort: a reasoning loop.

  At minimum effort it's the best Inkling setting: 17/18 at ~1,000 tokens per answer.
- **The Coder failed 04 (Roman numerals) the same way in both modes:** two tests of `to_roman`.
- **Every model passed 11 of the 18 tasks in both modes,** so those tasks don't separate them. Harder tasks would make the next run more telling.
- **Limits of this run:**
  - It's one greedy run, so a difference of 1–2 tasks isn't significant.
  - With no sampling penalties and a token limit, a reasoning loop costs the whole task. The model card's sampling (temperature 0.7, presence penalty 1.5) might change the minimum-effort results.
- **Conclusion for now:** for coding, use **IQ3_XXS with thinking off**. **Inkling Q4 at minimum effort** is close behind (see also the long-context eval below), and is faster and much cheaper when it thinks.

### Long-context eval (2026-11-24; xl 2026-11-25)

`eval\run_longctx.py` (`just eval-long`; details in `eval\README.md`) asks whether a model uses facts far above the request. Only 8 of Inkling's 48 layer passes see the whole context, against all of the Qwen models' layers.
- **The project:** `shopkit`, a small fictional shop, so neither model knows it. Its rules (rounding, line limit, tax, shipping, codes, events) are in files at the top, `stock.py` is in the middle, and the request comes last.
- **The tasks:** 7, among them two bug fixes. Every reference answer passes, and the unfixed project fails every task.
- **Two variants of each task:**
  - **short:** ~2,700 tokens.
  - **long:** ~59,000 characters of standard-library code inserted between the rules and the request, giving 21,481 tokens on Inkling and 17,393 on IQ3.

  The rules are ~18K tokens from the request in the long variant.
  - **xl** (added 2026-11-25, `--variants xl`): ~90,000 more characters (heapq, pprint, gettext, graphlib, string), split above and below `stock.py`. ~156,000 characters: 48,354–48,811 tokens on Inkling, 39,770–40,191 on IQ3. Inkling needs its 64K context for it.
- **Runs:** one greedy run each. short and long: `eval\out\lc-20261124-133140\` (56 requests). xl: `eval\out\lc-xl-20261125\` (28 requests).

| Model | Mode | Short | Long (~18–21K tokens) | XL (~40–49K tokens) |
|---|---|---|---|---|
| Inkling Q4 | thinking off | 6/7 | 6/7 (4 answers without ``` fences) | 6/7 (6 without fences) |
| Inkling Q4 | minimum | 6/7 | 6/7 | 6/7 |
| IQ3_XXS | thinking off | 6/7 | 7/7 | **7/7** |
| IQ3_XXS | minimum | **7/7** | **7/7** | **7/7** |

- **Distance cost neither model any correctness**, at ~18K tokens or at ~49K. Inkling used the rules from the top of the prompt and found the bug in the middle file. At xl its only failure was the same US-OR rule as at every other size (below), with thinking off and at minimum.
- **Inkling's format slips more as the prompt grows:** with thinking off, 0 of 7 answers had no fences at short, 4 at long and 6 at xl. With thinking, none.
  - They're whole files laid out like the prompt's own files. This is the clearest difference found, and it matters for agents and clients that expect fenced code. IQ3 fenced every answer.
  - The harness first scored unfenced answers as failures. It now reads them, and `--regrade` regraded the saved answers.
  - At xl, two of them also started each file with the prompt's own `### FILE: shopkit/orders.py` header instead of `# file:`. The harness now accepts any number of `#` before `file:`. Both runs were regraded: the xl run went from 5/7 to 6/7 with thinking off, and the earlier run didn't change.
- **Inkling's one failure, in every variant and mode:** in `order_total` it treated the "collected in store, asking for a shipping price is an error" region as an error instead of as no shipping. That's how it read the rule, not distance, and the rule could be read either way.
- **IQ3's one failure** (short, thinking off) was a misplaced parenthesis in the rounding fix: it rounded the 15% rate instead of the product.
- **Ignore the prompt tok/s column in `summary.md`:** the tasks share most of the prompt, and the conversation cache skips that part.
- **To separate them further:**
  - Make retrieval harder: near-duplicate rules, a later file overriding a constant.
  - Try the multi-turn repair test.

## Benchmarking

The scripts are in `D:\UnbiasedStrataPS\bench\`, and their output goes to `bench\out\`, which git ignores. They need the GPU to themselves.
- **`ab-polystrata.ps1`:** starts PolyStrata's server with a run config (`-Config`) on port 8093, runs a client, then stops the server and engine. It only knows `strata.exe`: for Inkling, stop `strata-poly.exe` yourself. Example: `.\bench\ab-polystrata.ps1 -Label x -Config D:\polystrata\terminal\strata-coder-iq1_m-r700.json -Client bench_greedy.py`
- **`ab-oldfork.ps1`:** the same for the old fork (`-Exe` chooses the build).
- **Clients:**
  - `bench.py`: the old fork's original; it sends no temperature, so don't use it against PolyStrata.
  - `bench_greedy.py`: the same with `temperature: 0`. Use this one.
  - `bench_overhead.py`: wall-clock time against engine time, with whole and streamed requests.

Each client sends 8 coding prompts × 400 tokens and 2 prompts of ~20K tokens cut from `D:\UnbiasedStrata\src\program\generate.cpp`.

## Next steps

1. ~~Make the best config permanent~~: done for both models (see "This checkout"). For other machines, use `just serve-lan` with `$env:STRATA_API_KEY` set.
2. **Decide on default sampling.** Do your clients send `temperature`? If not, consider a `sampling` block in the run config.
3. ~~Benchmark IQ3_XXS~~: done, 113.0 tok/s decode (see "Best configuration measured"). A second run would show how much the decode figure moves.
4. **Inkling 2 Mini:** measure whether the reasoning efforts (`minimum`, `low`, `medium`, the default) change thinking length and answers over several prompts. Then decide whether clients should send one. The coding eval (above) covered off and minimum only.
   - **Next for the eval:** add a `--sampling card` option, to run thinking with the model card's sampling instead of greedy. Also add harder tasks, since 11 of the 18 don't separate the models.
5. **Try the real coding clients:** tool calls (streamed and not), long sessions, and recovery after an engine failure. Note anything the old fork's front-end fixes used to cover: malformed tool calls, retry on non-finite output, control-token literals, stall detection.
6. **Fork workflow:** keep local changes as small branches on `mtnrbq/PolyStrata`, and pull `upstream` releases. `just update` (`UPDATE.bat`) updates without starting the model. After each release, re-check whether it wins back the expert-cache VRAM.
7. **Tidy up:**
   - Remove the test run configs in `terminal\`: `*-tuned*.json`, `*-r700*.json`, `*-fetch0.json`, `*-sm120off.json`. The daily configs are now setup's own `strata-coder-iq1_m.json` and `strata-iq3_xxs.json`.
   - Mark `PSPLAN.md` in `UnbiasedStrataPS` as superseded.
   - Remove `D:\UnbiasedStrata-stream` (~2.6 GB build) once the old fork isn't needed as a fallback.

## The old fork, as a fallback

`mtnrbq/UnbiasedStrata` `main` now streams properly: [PR #18](https://github.com/mtnrbq/UnbiasedStrata/pull/18), merge commit `4491ac4e5`. A build of it is at `D:\UnbiasedStrata-stream\build\win\unbiased-strata.exe`, branch `stream-content`. The local `D:\UnbiasedStrata` checkout hasn't been fetched since.

## This PC

- **Disk:** `D:` has ~7.5 GB free and `C:` ~20 GB (after removing Inkling Q2 and the old IQ3_XXS pack). They're two partitions on the same SSD. `D:` is tight, so a local engine build (several GB) may not fit there.
- **The user PATH was overwritten** to just `Adom Bridge`, probably by the Adom Bridge installer. Python and cargo aren't on PATH until it's restored. `uv` and `just` are in `%LOCALAPPDATA%\Microsoft\WinGet\Links`; add that folder to the user PATH if it isn't there.
- **uv's cache** is on `C:` (~8 GB), so venvs on `D:` get copies instead of hardlinks (a harmless warning). `UV_LINK_MODE=copy` silences it. Don't move the cache to `D:`, because there isn't room.
- **CUDA toolkit 13.0** (V13.0.88) and **VS 2022 Build Tools** are installed. Avoid CUDA 13.2.0 and 13.2.1, which miscompile sm_120.
