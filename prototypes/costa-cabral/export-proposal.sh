#!/bin/sh
# Export the actual SUMO replay, bilingual MP4 films and portable static website.
set -eu
task_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$task_root"
export UV_CACHE_DIR="$task_root/.cache/uv"
export UV_PYTHON_INSTALL_DIR="$task_root/.cache/python"
if [ ! -x .venv/bin/python ] || [ ! -f prototypes/costa-cabral/runs/moderate-baseline-17/routes.rou.xml ]; then
 ./prototypes/costa-cabral/prototype.sh
fi
uv pip install --python .venv/bin/python -r prototypes/costa-cabral/requirements.txt
command -v ffmpeg >/dev/null || { echo 'Install ffmpeg to render MP4 videos.'; exit 1; }
.venv/bin/python prototypes/costa-cabral/capture_replay.py
.venv/bin/python prototypes/costa-cabral/render.py
.venv/bin/python prototypes/costa-cabral/prepare_3d.py
.venv/bin/python prototypes/costa-cabral/presentation.py "$@"
if [ -f prototypes/line-701/results.json ]; then
 .venv/bin/python prototypes/line-701/build_site.py
fi
