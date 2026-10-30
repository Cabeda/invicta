# Queue investigation evidence

The [results](../701-queue-onset-results-2026-10-30.md) explain these cases. None qualifies a full-service proposal or validates field operation.

`manifest.json` binds the original source ledger and shared input archives, each retained case file and the small native fixture. Case payloads use gzip with both compressed and original-byte SHA-256 values. Existing `trial_evidence.read_archive()` verifies these descriptors. Native snapshot payloads may themselves be compressed; their outer gzip preserves the original native bytes.

The groups distinguish the unchanged original-input bus-blockage capture, snapshot actor-removal analogues, the partial full-network two-car sweep, complete reduced-network comparisons, and the full-network two-car join and reprocessing control. Do not combine their demand or coverage claims. The earlier sweep's exception and post-run audit are separate files.

The two `network_recipes` retain supported netconvert commands, source/target hashes and compact **Zstandard reference patches** for exact reconstruction of the full regional variants. These are not gzip payloads. Their reference is the verified original proposed-layout `network.net.xml` from `shared_inputs`. Decode with:

```sh
zstd -d --patch-from=verified-source.net.xml network-recipes/joined.zst -o new-joined.net.xml
```

Check the source against `reference_sha256`, the compressed patch against `sha256`, and the decoded file against `decoded_target_sha256`. The manifest records the encoder version. Repeat with `roundtrip.zst` for the unmodified reprocessing control. The patches retain the exact observed bytes, including generated headers, without duplicating regional XML maps.

The fast native regression needs neither these regional variants nor Zstandard. It uses the committed 13-road fixture and the pinned SUMO environment:

```sh
.venv/bin/python -m unittest discover -s prototypes/line-701/full -p test_junction_geometry.py -v
```
