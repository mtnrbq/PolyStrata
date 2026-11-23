# Where this work stands (2026-11-23)

Notes for resuming. This isn't part of PolyStrata's docs. It lives only on the `local-setup` branch (pushed to `origin`), so keep it out of pull requests to `upstream`.

## The decision

**Plain PolyStrata is the base.** It replaces both porting UnbiasedStrata 2 to Windows (`PSPLAN.md`) and keeping the old UnbiasedStrata 1 fork (`D:\UnbiasedStrata`). The target is Qwen3.8 Flash-Next **Coder IQ1_M** and **IQ3_XXS** on Windows with an **RTX 5070 Ti (16 GB)** and 64 GB of RAM. Qwen3.6 isn't needed.

Why: weekly upstream releases with Windows and RTX 50 support, ~20% faster prompt reading, and token-by-token streaming. Together they outweigh the old fork's ~18% decode lead.

The full comparison, method and every run are in `mtnrbq/UnbiasedStrataPS` (`D:\UnbiasedStrataPS`): see `plainpolySQ.md` (start with the "Head-to-head so far" section), with the benchmark scripts in `bench/`.

## This checkout

- **The clone:** `D:\polystrata`.
  - `origin` is `mtnrbq/PolyStrata` (your fork) and `upstream` is `simplexai-labs/PolyStrata`. The repo moved there from `VecSzn/PolyStrata`, which redirects.
  - `main` is at `v0.2.19-poly.1` (`d1f711e11`), with no local commits, and matches `origin/main`.
  - The working branch is **`local-setup`**, which tracks `origin/local-setup`. It's `main` plus this file and the `justfile`. Put changes meant for upstream on their own small branches off `main`, not here.
  - Setup's outputs are ignored by git.
- **The `justfile`** (`just --list`) holds this PC's shortcuts: `serve`, `serve-lan` (needs `$env:STRATA_API_KEY`), `serve-iq3`, `setup-coder`, `setup-iq3`, `check`, `update`, `log` and `bench`. `just` and `uv` are in `%LOCALAPPDATA%\Microsoft\WinGet\Links`, which has to be on the user PATH.
- **Python:** `terminal\.venv` (Python 3.12.13). It was made with `uv venv --seed --python 3.12`, and `requirements.txt` was installed with `uv pip`. `START-HERE.bat` uses it instead of installing Python.
- **Setup has been run for both models,** non-interactively with `just setup-coder` and `just setup-iq3`. Both use 64K context, an 8-bit KV cache, no vision, experimental "speed projection" off (it's a refusal-direction control vector, not a speed setting) and **`--vram-reserve-mib 700`**.
  - **Coder IQ1_M:** it reused every file, with no downloads and no pack rebuilt. It wrote `terminal\strata-coder-iq1_m.json` (the earlier one is `.json.bak`) and `terminal\run-coder-iq1_m.bat`. The engine arguments match the `-r700` test config exactly.
  - **IQ3_XXS:** it checked both shards (SHA-256) without downloading, and built its own pack, `C:\Strata-data\packs\iq3_xxs` (1.5 GB). It wrote `terminal\strata-iq3_xxs.json` and `terminal\run-iq3_xxs.bat`. It uses the general expert profile, `terminal\data\expert-profile.bin`, and the Coder's draft head.
- **The engine:** `terminal\engine\strata.exe`, Strata **0.1.66**. It's a prebuilt, signed package from the update feed, built for sm_75/86/89/120 plus PTX with **CUDA 13.0**, and needs driver 580.65 or newer (installed: 617.42). The CUDA runtime comes from the venv (`nvidia-cuda-runtime` 13.0.96).

## Model data (shared with the old fork, so be careful)

| Model | Files | Pack | Draft head |
|---|---|---|---|
| Coder IQ1_M | `D:\Strata-data\models\coder-IQ1_M\` | `D:\Strata-data\packs\coder-iq1_m` | `D:\Strata-data\mtp\rt` (+ `mtp-q2_0.gguf`) |
| IQ3_XXS | `C:\Strata-data\models\IQ3_XXS\` | `C:\Strata-data\packs\iq3_xxs`; the old fork's `iq3-xxs` is a junction to it | the Coder's `rt` |

- All four shards match PolyStrata's pinned sizes, and the packs are complete.
- **One IQ3_XXS pack for both:** `C:\Strata-data\packs\iq3-xxs` is a directory junction to PolyStrata's `iq3_xxs`. The two packs were byte-identical except for two things:
  - The old pack had `expert-profile.bin`, which the old fork reads from the pack when no `--expert-profile` is given. It was copied into `iq3_xxs`. It's identical to `terminal\data\expert-profile.bin`.
  - PolyStrata's `tokenizer\tokenizer.json` adds `"pre_sequence": null` and `"ignore_merges": false`. The old fork doesn't read those keys, but it hasn't been run through the link yet.
  - The old pack is kept as `C:\Strata-data\packs\iq3-xxs.old` (1.5 GB) until it has. To undo the link: `cmd /c rmdir C:\Strata-data\packs\iq3-xxs`, then rename `iq3-xxs.old` back.
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

## Benchmarking

The scripts are in `D:\UnbiasedStrataPS\bench\`, and their output goes to `bench\out\`, which git ignores. They need the GPU to themselves.
- **`ab-polystrata.ps1`:** starts PolyStrata's server with a run config (`-Config`) on port 8093, runs a client, then stops the server and engine. Example: `.\bench\ab-polystrata.ps1 -Label x -Config D:\polystrata\terminal\strata-coder-iq1_m-r700.json -Client bench_greedy.py`
- **`ab-oldfork.ps1`:** the same for the old fork (`-Exe` chooses the build).
- **Clients:**
  - `bench.py`: the old fork's original; it sends no temperature, so don't use it against PolyStrata.
  - `bench_greedy.py`: the same with `temperature: 0`. Use this one.
  - `bench_overhead.py`: wall-clock time against engine time, with whole and streamed requests.

Each client sends 8 coding prompts × 400 tokens and 2 prompts of ~20K tokens cut from `D:\UnbiasedStrata\src\program\generate.cpp`.

## Next steps

1. ~~Make the best config permanent~~: done for both models (see "This checkout"). For other machines, use `just serve-lan` with `$env:STRATA_API_KEY` set.
2. **Decide on default sampling.** Do your clients send `temperature`? If not, consider a `sampling` block in the run config.
3. **Benchmark IQ3_XXS:** setup is done, but neither the server nor a benchmark has run it yet. `just bench iq3 D:\PolyStrata\terminal\strata-iq3_xxs.json`.
4. **Try the real coding clients:** tool calls (streamed and not), long sessions, and recovery after an engine failure. Note anything the old fork's front-end fixes used to cover: malformed tool calls, retry on non-finite output, control-token literals, stall detection.
5. **Fork workflow:** keep local changes as small branches on `mtnrbq/PolyStrata`, and pull `upstream` releases. `just update` (`UPDATE.bat`) updates without starting the model. After each release, re-check whether it wins back the expert-cache VRAM.
6. **Tidy up:**
   - Remove the test run configs in `terminal\`: `*-tuned*.json`, `*-r700*.json`, `*-fetch0.json`, `*-sm120off.json`. The daily configs are now setup's own `strata-coder-iq1_m.json` and `strata-iq3_xxs.json`.
   - Once the old fork's `just serve-iq3` has worked through the junction, delete `C:\Strata-data\packs\iq3-xxs.old` (1.5 GB).
   - Mark `PSPLAN.md` in `UnbiasedStrataPS` as superseded.
   - Remove `D:\UnbiasedStrata-stream` (~2.6 GB build) once the old fork isn't needed as a fallback.

## The old fork, as a fallback

`mtnrbq/UnbiasedStrata` `main` now streams properly: [PR #18](https://github.com/mtnrbq/UnbiasedStrata/pull/18), merge commit `4491ac4e5`. A build of it is at `D:\UnbiasedStrata-stream\build\win\unbiased-strata.exe`, branch `stream-content`. The local `D:\UnbiasedStrata` checkout hasn't been fetched since.

## This PC

- **Disk:** `D:` has ~10 GB free and `C:` ~25 GB. They're two partitions on the same SSD. `D:` is tight, so a local engine build (several GB) may not fit there.
- **The user PATH was overwritten** to just `Adom Bridge`, probably by the Adom Bridge installer. Python and cargo aren't on PATH until it's restored. `uv` and `just` are in `%LOCALAPPDATA%\Microsoft\WinGet\Links`; add that folder to the user PATH if it isn't there.
- **uv's cache** is on `C:` (~8 GB), so venvs on `D:` get copies instead of hardlinks (a harmless warning). `UV_LINK_MODE=copy` silences it. Don't move the cache to `D:`, because there isn't room.
- **CUDA toolkit 13.0** (V13.0.88) and **VS 2022 Build Tools** are installed. Avoid CUDA 13.2.0 and 13.2.1, which miscompile sm_120.
