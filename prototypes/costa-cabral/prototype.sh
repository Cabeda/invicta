#!/bin/sh
# THROWAWAY prototype. Frozen demo: open costa-cabral.prototype.html directly.
set -eu
task_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$task_root"
export UV_CACHE_DIR="$task_root/.cache/uv"
export UV_PYTHON_INSTALL_DIR="$task_root/.cache/python"
if [ ! -x .venv/bin/python ]; then uv venv --python 3.12 .venv; fi
uv pip install --python .venv/bin/python -r prototypes/costa-cabral/requirements.txt
.venv/bin/python prototypes/costa-cabral/prepare.py
.venv/bin/python prototypes/costa-cabral/experiment.py "$@"
.venv/bin/python prototypes/costa-cabral/render.py
