# Windows shortcuts for this PC (see RESUME.md).  `just --list` shows the recipes.
# The paths below are this PC's; override one on the command line, e.g. `just port=8093 serve`.

set windows-shell := ["pwsh", "-NoLogo", "-NoProfile", "-Command"]
set default-list := true

term := justfile_directory() + '\terminal'
py := term + '\.venv\Scripts\python.exe'
port := '8080'
ctx := '65536'
# the best measured VRAM reserve on the RTX 5070 Ti (setup's default on Windows is 1280; 1500 if the display freezes)
reserve := '700'

# the Coder's files (setup was told to keep them where they are)
data := 'D:\Strata-data'
# the full model's files (C: has the room; it is the same SSD as D:)
iq3_data := 'C:\Strata-data'

# the run configs setup writes
coder_cfg := term + '\strata-coder-iq1_m.json'
iq3_cfg := term + '\strata-iq3_xxs.json'
inkling_cfg := term + '\strata-inkling-ud-q2_k_xl.json'

# the benchmark scripts (D:\UnbiasedStrataPS, see its plainpolySQ.md)
bench_dir := 'D:\UnbiasedStrataPS'

# run the server for Qwen3.8 Flash-Next Coder IQ1_M on 127.0.0.1 (this PC only) (Ctrl+C stops it)
serve *args:
    & '{{py}}' '{{term}}\serve\server.py' --engine strata --config '{{coder_cfg}}' --port {{port}} {{args}}

# the same, reachable from the network: needs $env:STRATA_API_KEY (clients send it as a Bearer token)
serve-lan *args:
    if (-not $env:STRATA_API_KEY) { Write-Error 'Set $env:STRATA_API_KEY first: the server must not be on the network without a key.'; exit 1 }
    & '{{py}}' '{{term}}\serve\server.py' --engine strata --config '{{coder_cfg}}' --port {{port}} --host 0.0.0.0 {{args}}

# run the server for Qwen3.8 Flash-Next IQ3_XXS (the full model) on 127.0.0.1; run `just setup-iq3` once first
serve-iq3 *args:
    if (-not (Test-Path '{{iq3_cfg}}')) { Write-Error 'No IQ3_XXS run config yet: run `just setup-iq3` first.'; exit 1 }
    & '{{py}}' '{{term}}\serve\server.py' --engine strata --config '{{iq3_cfg}}' --port {{port}} {{args}}

# run the server for Inkling 2 Mini UD-Q2_K_XL (strata-poly, one request at a time) on 127.0.0.1; `just setup-inkling` first
serve-inkling *args:
    if (-not (Test-Path '{{inkling_cfg}}')) { Write-Error 'No Inkling run config yet: run `just setup-inkling` first.'; exit 1 }
    & '{{py}}' '{{term}}\serve\server.py' --engine strata --config '{{inkling_cfg}}' --port {{port}} {{args}}

# write the Coder's run config with the best measured settings (no downloads; the model files stay where they are)
setup-coder *args:
    & '{{justfile_directory()}}\START-HERE.bat' --yes --family coder --model IQ1_M --data-dir '{{data}}' --context {{ctx}} --kv int8 --vision no --experimental-speed-projection off --vram-reserve-mib {{reserve}} --no-start {{args}}

# write the IQ3_XXS run config the same way
setup-iq3 *args:
    & '{{justfile_directory()}}\START-HERE.bat' --yes --family qwen --model IQ3_XXS --data-dir '{{iq3_data}}' --context {{ctx}} --kv int8 --vision no --experimental-speed-projection off --vram-reserve-mib {{reserve}} --no-start {{args}}

# write Inkling 2 Mini's run config: UD-Q2_K_XL (its experts all fit the 16 GB card), 32K, no pictures, setup's VRAM reserve
setup-inkling *args:
    & '{{justfile_directory()}}\START-HERE.bat' --yes --family inkling --model UD-Q2_K_XL --data-dir '{{iq3_data}}' --vision no --no-start {{args}}

# check this PC (GPU, driver, RAM, disk) and change nothing
check:
    & '{{justfile_directory()}}\START-HERE.bat' --check

# get the newest code (git pull), engine and settings, without starting the model
update:
    & '{{justfile_directory()}}\UPDATE.bat'

# show the last lines of a model's engine log (speed per request, expert-cache hit rate, slots, VRAM budget)
log model='coder-iq1_m' lines='40':
    Get-Content '{{term}}\strata-{{model}}.log' -Tail {{lines}}

# the coding eval (eval\README.md): all models, thinking off and minimum, on port 8093; `just eval --check` checks the tests
eval *args:
    Set-Location '{{justfile_directory()}}'; & '{{py}}' eval\run_eval.py {{args}}

# benchmark a run config on port 8093 with the greedy client (needs the GPU to itself), e.g. `just bench r700`
bench label config=coder_cfg client='bench_greedy.py':
    Set-Location '{{bench_dir}}'; .\bench\ab-polystrata.ps1 -Label '{{label}}' -Config '{{config}}' -Client '{{client}}'
