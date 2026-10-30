# Combatentes repeated internal stop

The native fixture reproduces Cabeda's observation: after admission at the first light, a lone bus receives another red stop inside this compact junction. The unchanged source waits **41 s inbound and 110 s outbound** after admission. No traffic, passengers, scheduled stops or pedestrian demand is needed to trigger the fault.

`split.net.xml.gz` contains 59 normal roads extracted from the frozen signal-enabled seed-17 bus-only control. All six focus junction attributes/request matrices and the 24-phase controller table match the original semantically. Extracting through netconvert rounds capped lane speeds from 13.88888888888889 to 13.89 m/s; the unchanged study bus's lower maximum still applies. Outer cut boundaries are explicit. `source.json` binds compressed/decoded bytes, the original archive, extraction command and selected roads. `buses.rou.xml` keeps the original bus type and local route suffixes in both directions.

The five represented traffic-light junctions share one controller. The correction footprint also includes the central priority node `299610705`, which is why the generic `--tls.uncontrolled-within` option alone does not remove the observed extra stops. `boundary-controls.json` explicitly binds the footprint, original 21 controlled movements and programme: ten controls are approached from a road wholly inside the footprint, and eleven control entry from outside it. The recipe has separate signatures for the inspected final network and the earlier import stage before normal overlay conversion and the study speed cap.

`signal_mapping.write_boundary_controls` writes supported plain connection patches with `uncontrolled="true"` for the ten internal movements and explicitly pins all existing normal-road connections from the frozen V6 control. Normal yielding/conflict logic remains; it does not mark movements `pass=true` or disable all traffic lights. The eleven external controlled movements retain their signal indices and phase table. Netconvert recalculates off-state yielding and internal conflict geometry; actual actuated phase transitions are not asserted identical. Two generated internal-only stages remain without controlling detectors and are reported as warnings. No claim is made that the remaining assumed programme is Porto's actual one.

Run the regression from the repository root:

```sh
.venv/bin/python -m unittest discover -s prototypes/line-701/full -p test_signal_mapping.py -v
```

The correction is opt-in during the second import pass. The recipe loads its declared frozen control from the repository evidence ledger and a hash-verified compatible native import, validates that actual input's topology separately, and rejects any output changes outside the reviewed junction. This path materializes frozen import bytes rather than performing another fresh OSM import:

```sh
.venv/bin/python prototypes/line-701/full/priority_model.py \
  --output .cache/701-model-with-combatentes-correction \
  --junction-corrections prototypes/line-701/full/diagnostics/alfena-junction/join.nod.xml \
  --signal-corrections prototypes/line-701/full/diagnostics/combatentes-junction/boundary-controls.json
```

The Alfena geometry correction is inherited from that frozen import. Omitting its argument preserves the declared inherited source; supplying it requires the exact expected digest. A conflicting node patch is rejected rather than silently ignored or reported as applied.

The native tests check lone and opposing buses, 408 paired movement cases (17 retained bus paths, three relative departure offsets), and all 17 paths together with eight walkers at three offsets. `movements.json` stores the bus-capable external paths derived from the source connections. Each test requires every requested bus and walker to start and finish, with zero recorded collisions. Vehicle permissions and the complete imported pedestrian lane/connection graph are also compared. These are software/model diagnostics, not exhaustive safety validation.

A blanket six-node physical join was rejected: it removed an existing walking connection in the compiled graph (`1352537841 → 1352537837#1`). A programme-only always-permissive internal-state probe also cleared the buses but changes actuation. Neither is the selected correction. V7's minimal connection patch and V8's fresh control rebuild introduced unrelated converter drift. The selected V9 integration anchors connection pins to the exact archived baseline and compares the complete corrected network against that source.

The local success does not establish field timetable compliance or a physical signal-head mapping. Full-day numerical results are recorded separately. The source has incomplete crossing representation; retained walking access is not a pedestrian phase plan. No OSM edit or street proposal is made.

Source: © OpenStreetMap contributors, ODbL, derived from the repository's frozen [OSM archive/manifest](../../data/network-manifest.json). SUMO documents [uncontrolled connection patches](https://sumo.dlr.de/docs/Networks/PlainXML.html#explicitly_setting_which_edge_lane_is_connected_to_which) and warns that internal control/junction grouping needs inspection in its [OSM traffic-light guidance](https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html#traffic_lights).
