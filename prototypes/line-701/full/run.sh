#!/bin/sh
set -eu
full_root=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
cd "$full_root"
.venv/bin/python prototypes/line-701/full/prepare.py
.venv/bin/python prototypes/line-701/full/geometry_audit.py
.venv/bin/python prototypes/line-701/full/experiment.py "$@"
.venv/bin/python prototypes/line-701/full/prepare_replay.py
.venv/bin/python prototypes/line-701/build_site.py
