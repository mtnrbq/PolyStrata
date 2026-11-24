# Coding eval

A local test of how well each installed model writes code. It compares Inkling 2 Mini, Qwen3.8 Flash-Next Coder IQ1_M
and Qwen3.8 Flash-Next IQ3_XXS on 18 Python tasks, with thinking off and at minimum effort. It's not part of
PolyStrata's docs.

## How it works

- Each task in `tasks/` has a prompt (`PROMPT`) and hidden tests (`test_*` functions). `reference/` holds a solution
  for each one, used only to check that the tests are right.
- A task is one chat request, greedy (`temperature: 0`). The longest Python code block in the answer is saved as
  `solution.py` and run against the tests. Each test runs in its own Python process, with a 30-second limit.
- A model is started with setup's run config on port 8093, used for every task and mode, then stopped (the server and
  its engine). Only one model is on the GPU at a time.
- The two modes:
  - `off`: `chat_template_kwargs.enable_thinking: false`, up to 3,000 tokens.
  - `minimum`: `reasoning_effort: "minimum"`, up to 8,000 tokens. That's effort 0.1 on Inkling 2, and `low` on the
    Qwen models, which have nothing lower.

The model's code is run as it is, with no sandbox beyond its own process and the time limit.

## Running it

From the repository root, with no other model running:

```powershell
just eval --check                         # every reference must pass its tests
just eval                                 # all three models, both modes, all tasks
just eval --models inkling --modes off --tasks 01,05
just eval --summarize eval\out\<run>      # rebuild a run's summary
```

`just eval` runs `terminal\.venv\Scripts\python.exe eval\run_eval.py`.

## Output

Each run gets a folder `eval\out\<date-time>\`, which git ignores:

- `summary.md`: per model and mode, the tasks passed, the tests passed, answers cut off at `max_tokens`, answers with
  no usable code, median tokens, reasoning length and decode speed, and the total time. Then a table per task.
- `results.jsonl`: one line per request, with each failing test's error.
- `work\<model>\<mode>\<task>\`: the full answer (`answer.md`, reasoning included) and the code that was tested.
- `server-<model>.log`: the server's output.

## The tasks

| # | Task | What it tests |
|---|---|---|
| 01 | `parse_duration` | parsing, strict error handling |
| 02 | `merge_intervals` | sorting, edge cases (touching, nested) |
| 03 | `LRUCache` | a class with an O(1) contract |
| 04 | Roman numerals | both directions, rejecting non-canonical forms |
| 05 | `justify` | fiddly text layout |
| 06 | `evaluate` | a recursive-descent parser with unary minus |
| 07 | `topo_sort` | Kahn's algorithm with alphabetical tie-breaks, cycles |
| 08 | `parse_csv_line` | a quoting state machine |
| 09 | `find_first` | fixing a buggy binary search |
| 10 | `shortest_path` | Dijkstra, checked against Floyd-Warshall |
| 11 | `compare_versions` | SemVer 2.0.0 precedence and validation |
| 12 | `flatten` / `unflatten` | recursion, conflict detection |
| 13 | `TokenBucket` | a rate limiter with an injected clock |
| 14 | `lcs` | dynamic programming at 1,000 x 1,000 |
| 15 | `glob_match` | sets, escapes, no exponential backtracking |
| 16 | `min_meeting_rooms` | a sweep line, checked against brute force |
| 17 | `spiral_order` | matrix boundaries |
| 18 | `json_pointer_get` | RFC 6901, escape order, error types |
