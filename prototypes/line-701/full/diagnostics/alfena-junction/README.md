# Alfena two-car junction diagnostic

This is a reduced native reproduction of a persistent blocking mechanism in the frozen V5 proposed-layout run. It is not a traffic proposal, a field validation or a full-line compliance result.

`split.net.xml` retains 13 roads from the recorded regional input. At nodes `14297876949` and `14297876959`, the junction attributes and right-of-way request matrices are identical to the original. Their centres are about 6.64 m apart; the two normal connecting roads have only 0.20 m of available lane length after junction geometry. A car cannot be stored within that lane. The source OSM represents the two carriageways of Rua de São Vicente and its junction with Rua Nossa Senhora da Paz as separate nodes.

`pair.rou.xml` contains the original `crossing` type and local route suffixes for `crossing_14_109` and `crossing_14_33`. Only these two actors are requested. Both are inserted; at overlapping arrival times they remain stopped at the same positions as the archived queue. Each actor completes alone. Origins, destinations, type and requested actor count stay fixed in the comparison.

`join.nod.xml` is a **candidate model correction**: use one compound priority junction, with supported netconvert node joining. The eight external vehicle movements remain available. This neither adds bus priority nor bans a car movement. It has not been promoted into the regional baseline or treated as a surveyed street design.

Run from the repository root:

```sh
.venv/bin/python -m unittest discover -s prototypes/line-701/full -p test_junction_geometry.py -v
```

The tests retain the split-network failure, check each actor alone, verify all eight external vehicle movements and run the joined case at 21 relative departure offsets from −10 to +10 seconds. Offsets are explicit diagnostic inputs, not observed traffic counts. The reduced boundary changes exact arrival timing; its deadlock-offset range is not asserted to equal the full network's range.

The original-input replay reaches the first prolonged bus wait at 15:19:33 and matches 3,074 completed native bus calls against the frozen run. That captures the queue's propagation into a bus; the two ordinary vehicles' first blocking manoeuvres are earlier. See the [investigation report](../../../../../docs/research/701-queue-onset-results-2026-10-30.md) for evidence bindings and limitations.

Source: © OpenStreetMap contributors, ODbL, derived from the repository's frozen [OSM archive and manifest](../../data/network-manifest.json) and `v5-moderate-priority-mapped-s17` native evidence. [SUMO OSM junction import guidance](https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html#junctions) explains why separately mapped carriageways may require an explicit junction join; [plain-XML joining](https://sumo.dlr.de/docs/Networks/PlainXML.html#joining-nodes) documents the supported operation. File and source hashes are recorded in `provenance.json`.
