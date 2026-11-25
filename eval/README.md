# Coding eval

A local test of how well each installed model writes code. It compares Inkling 2 Mini UD-Q4_K_XL (`inkling-q4`; the first run also had UD-Q2_K_XL, since removed), Qwen3.8 Flash-Next Coder IQ1_M
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
just eval --models inkling-q4 --modes off --tasks 01,05
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

## The long-context eval

`run_longctx.py` (`just eval-long`) tests whether a model uses facts that sit far above the request. It's meant to
separate models that tie on the short tasks, such as Inkling 2 Mini (40 of its 48 layer passes see only the last
1,024 tokens) and the Qwen models (every layer sees the whole context).

- **The project:** `longctx/project/shopkit` is a small shop: money, discount codes, config, events, stock and orders.
  The rules the tasks depend on are in the files at the top: half-to-even rounding, a 24-unit line limit, NZ tax at
  15%, shipping bands, which codes combine, and the region that isn't shipped to. `stock.py` is in the middle.
  `orders.py` and the request come last.
- **Two variants of each task:**
  - **short:** the project only, about 7,000 characters (~2,500 tokens).
  - **long:** about 59,000 characters of unrelated standard-library code (`longctx/vendor`: textwrap, shlex,
    calendar) between the rules and the request. That's about 66,000 characters, ~21,400 tokens on Inkling.

  - **xl** (`--variants xl`, not run by default): another ~90,000 characters (heapq, pprint, gettext, graphlib,
    string) above and below `stock.py`. That's about 156,000 characters: ~48,700 tokens on Inkling, which needs a 64K
    context for it, and ~40,000 on IQ3.

  A model's short score minus its long score is what distance costs it.
- **Answers are whole files:** ```python blocks starting with `# file: shopkit/<name>.py`. They're written into a
  copy of the project, and the task's hidden tests run against it. Files sent without fences, as `# file:` or
  `### FILE:` sections, are accepted too and counted in the summary's "without fences" column.
- **Checks:** `just eval-long --check` makes sure each reference answer (`longctx/reference`) passes, and that the
  project as given fails, so every task tests something.

| # | Task | The far-away facts it needs |
|---|---|---|
| 01 | `line_total` | SKU normal form, the 24-unit limit, half-to-even rounding, currency places |
| 02 | `shipping_cost` | the weight bands, the 0 g and over-weight rules, the region not shipped to |
| 03 | `order_total` | codes that add up or can't combine, expiry dates, free-shipping thresholds before discount, tax by region |
| 04 | fix a tax rounding bug | the bug is in `money.scale`, at the top; the fix must keep half-to-even |
| 05 | fix overselling | the bug is in `stock.reserve`, in the middle |
| 06 | `known_events` | every event name emitted across the project, written out |
| 07 | `receipt_line` | reuse `format_money` and the SKU normal form |

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
