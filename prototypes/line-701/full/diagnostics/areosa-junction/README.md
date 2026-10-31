# Areosa detector starvation

The 10% synthetic busy run left ordinary vehicles stopped around the Areosa controller for roughly 19 hours, including vehicles reporting a green ahead. This is a diagnostic pattern, not observed Porto congestion.

The reduced network has 51 normal roads. The original full network and this reduction both strand the second car inside `:1838444495_0_2` when two cars and a bicycle arrive at 20, 30 and 40 seconds. Each two-actor subset completes with the same remaining departure times. The reduction reprocesses boundary geometry; it does not claim exact state continuation or identical internal coordinates.

The ranked probes were detector actuation, split-junction storage and approach lane choice. A fixed cycle of the existing phases clears the actors. Changing `jam-threshold` to 30 or `detector-length` to 20 does not. Changing only the Areosa programme's `detector-gap` to zero clears all actors across 21 bicycle departure offsets. No road geometry, phase state, minimum/maximum green or yellow/all-red interval is edited by that correction. The exact detector cause is inferred from this differential test; it is not a surveyed detector location. SUMO documents [detector placement and its actuated-controller limitations](https://sumo.dlr.de/docs/Simulation/Traffic_Lights.html#type_actuated).

Run the native regression from the repository root:

```sh
.venv/bin/python -m unittest discover -s prototypes/line-701/full -p test_areosa_detection.py
```

It verifies the failing original, removal of each actor, unchanged signal phases and complete collision-free passage in every corrected offset. `provenance.json` binds the local inputs to the frozen regional model. A full-line rerun is required before making any statement about traffic effects; the local test alone cannot qualify a proposal.
