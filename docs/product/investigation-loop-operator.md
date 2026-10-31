# Run a line investigation

The session workflow keeps cheap local reproductions separate from complete service-day trials. It does not infer a cause from a late destination or generate an unreviewed street design. The investigating agent chooses a falsifiable hypothesis and a supported patch; the workflow retains the inputs, execution, failures, costs and next unresolved case.

The analysis, local recorder and session state accept a line identity. Preparing another line's roads, official timetable, demand pools and stop matching remains a separate adapter. The current full-day runner is the 701 adapter; a new line must supply its own prepared model and demand, rather than inherit Porto assumptions.

## Start with verified evidence

From the repository root, using the pinned simulation environment:

```sh
.venv/bin/python prototypes/line-701/full/study_session.py \
  --workspace .cache/studies/701 \
  init --line 701 \
  --source docs/research/701-investigation-loop-2026-10-31/study.json \
  --trial v14-combined-010-s17
```

An optional `--deadline` accepts an ISO timestamp. Workspaces are independent per line. Never reuse a directory for a different reference. `initial-casebook/README.md` explains the selected problem; `casebook.json` retains every timing interval, missing event, collision, ordinary stall and sampled non-stop wait. Added delay is distinct from inherited lateness. Skipped on-demand passage records are not counted as stationary service.

## Register a local experiment

Save a JSON proposal, for example `.cache/storage-control.json`:

```json
{
  "id": "storage-control",
  "network": "prototypes/line-701/full/diagnostics/areosa-junction/source.net.xml",
  "routes": "prototypes/line-701/full/diagnostics/areosa-junction/regional-five.rou.xml",
  "end_seconds": 900,
  "wall_seconds": 30,
  "hypothesis": {
    "change": "Unchanged regional blockage control",
    "prediction": "The resident vehicle remains stranded",
    "evidence": "Five load-bearing actors reduced from the recorded regional queue"
  }
}
```

```sh
.venv/bin/python prototypes/line-701/full/study_session.py \
  --workspace .cache/studies/701 step --proposal .cache/storage-control.json
```

A local case explicitly requests 1–100 vehicles in departure order. Implicit flows and unaccounted people are rejected. Additional signal programmes can be supplied through `additional`. A different network/programme/routes byte, native version or recorder implementation prevents cache reuse. Exact repeats reuse verified native results, including a failure to clear; a computation-limited case is retained but not reused as a completed experiment. Use a fresh experiment ID when physical inputs change.

Each recorded case exports a portable `index.html` with 2D/3D views of the **same one-second recording**, true vehicle dimensions and recorded signal states in the technical panel. The displayed geometry is cropped around recorded actors. A shared URL retains the frame, actor, dimension, language and source execution identity. If no positions were recorded before a budget stop, there is no visual claim. A failed visual export is journaled and can be retried without rerunning unchanged physics.

Serve a case folder over HTTP(S), for example:

```sh
python3 -m http.server 8780 --bind 127.0.0.1 \
  --directory .cache/studies/701/cases/storage-control
```

## Return to the complete reference

A service proposal contains `id`, `model`, `config` and the same `hypothesis` fields. The configuration is the existing native runner's explicit configuration. A model changing geometry or signal programmes needs a new identity and its own empty-network prerequisite. Pass its readiness evidence and reviewed stop assumptions through `config.readiness`. The default native wall budget is 180 seconds; a larger declared `diagnostic_budget_seconds` may be at most 900 seconds and must fit the session deadline.

```sh
.venv/bin/python prototypes/line-701/full/study_session.py \
  --workspace .cache/studies/701 service --proposal .cache/service-proposal.json
.venv/bin/python prototypes/line-701/full/study_session.py \
  --workspace .cache/studies/701 status
```

Service reuse includes prepared-model bytes, the actual runner implementation/dependencies, native version, demand pools, acceptance settings and any paired workload. Every bound input/output is checked again. Analysis can be regenerated separately. The result recomputes timetable, complete vehicle/person request sets and collisions from native outputs; it does not accept headline counts from a report.

A full service case can pass its simulation gates while `qualified` remains false. Access review, the declared paired scenario/seed matrix and field validation remain separate. Empty, passenger and traffic profiles retain independent unresolved cases: passing an empty prerequisite cannot erase a failing combined workload. Policy variants remain in the journal even when a later result supersedes their workload profile.

`events.jsonl` is flushed before the atomic state update. An interrupted state promotion is recovered from the journal. Concurrent writers are refused. Incomplete/corrupt journal records require explicit inspection rather than silently discarding evidence. The status reports native executions, verified reuses and measured native time. Native failures preserve their directories and reason; never overwrite them.

## Restore prepared models from the archive

The archive stores deduplicated compressed objects. Use its verified public reader rather than copying guessed cache paths:

```python
import json
from pathlib import Path
import sys
sys.path.insert(0, 'prototypes/line-701/full')
from trial_evidence import read_archive

manifest = Path('docs/research/701-investigation-loop-2026-10-31/study.json')
ledger = json.loads(manifest.read_text())
output = Path('.cache/restored-model-v14')
output.mkdir(parents=True, exist_ok=False)
for name, descriptor in ledger['models']['v14']['evidence'].items():
    if Path(name).name != name:
        raise ValueError('Model file leaves its directory')
    (output / name).write_bytes(read_archive(manifest.parent, descriptor))
```

Archive analysis and zero-step inspection work directly from the manifest. Full-day reruns need the restored prepared model plus their declared source-bound readiness review. Regenerating geometry starts from the frozen source import, not a fresh current OSM download. `areosa_compound.py` reproduces the V13 base network and rejects changes outside its reviewed footprint or to normal-lane semantics. `route_topology.contract_reference` preserves canonical stop indices for short workings; a removed served stop requires explicit rematching. A passing local case never bypasses the stop-berth audit.

The new loop enforces the agreed 60-second operational criterion explicitly, including when analysing a legacy run recorded with a broader score. Strict scoring remains independent. Service proposals cannot silently relax that threshold. Partial executions retain their evidence but cannot replace a complete workload failure profile.

Native completion is checkpointed before analysis. A reporting/storage failure can therefore resume the same verified physical execution. Casebooks are built in separate pending directories and promoted with source/hash receipts. Native initialization attempts, successful starts and measured elapsed time are distinct; preflight rejection consumes no reported native execution. Additional local XML is restricted to signal programmes and supported stopping/parking definitions; demand-bearing or unknown definitions are rejected before allocation.
