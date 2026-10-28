#!/bin/sh
# THROWAWAY route-first pilot. Uses frozen official inputs; no live polling by default.
set -eu
task_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$task_root"
export UV_CACHE_DIR="$task_root/.cache/uv"
export UV_PYTHON_INSTALL_DIR="$task_root/.cache/python"
if [ ! -x .venv/bin/python ] || [ ! -f prototypes/costa-cabral/data/baseline.net.xml ]; then
 ./prototypes/costa-cabral/prototype.sh
fi
.venv/bin/python prototypes/line-701/prepare_network.py
.venv/bin/python prototypes/line-701/prepare_scope.py
.venv/bin/python prototypes/line-701/prepare_route.py
.venv/bin/python prototypes/line-701/experiment.py "$@"
.venv/bin/python prototypes/line-701/analyse_observations.py
.venv/bin/python prototypes/line-701/prepare_replay.py
.venv/bin/python prototypes/line-701/build_site.py
