# Costa Cabral access experiment — THROWAWAY

**Project focus:** buses meeting their published schedules while catering to residents, shoppers, businesses and everyday services. Practical local access is an explicit requirement. See the [agreed project brief](../../docs/PROJECT_BRIEF.md); the current shopper/service-access policy is not yet modelled.

Question: can both directions of Rua de Costa Cabral be restricted to buses, local residents, taxis, bicycles and motorcycles, while ordinary cars can directly cross at junctions?

The user explicitly confirmed **crossings only**, not short longitudinal connecting stretches. The prototype answers the policy/routing question and exposes simulated tradeoffs. It is **not calibrated and does not justify implementation**.

## Open the prototype

Open [costa-cabral.prototype.html](costa-cabral.prototype.html) directly in a browser. It is a single offline HTML file with frozen results, free-play journey buttons, guided walkthroughs, readable state, and report/scenario downloads. Its controls select already-computed cases; they do not secretly run a browser approximation of SUMO.

## Rerun the actual simulations

From the repository:

```sh
./prototypes/costa-cabral/prototype.sh
```

Requires `uv` (already installed on the prototype machine); the script creates a project-local Python 3.12 environment and installs pinned SUMO packages. It rebuilds the network from frozen public inputs, runs 18 simulations, and regenerates the HTML, CSV and findings. No GUI SUMO or desktop automation is needed. The simulations run locally; no web service or API is needed after the frozen inputs and Python packages are available.

Edit the three demand dictionaries in `experiment.py` to try other explicit assumptions, then rerun. `--quick` runs one paired case/seed and replaces the displayed results with that reduced batch; rerun without it to restore all 18 runs.

- [FINDINGS.md](FINDINGS.md): question, assumptions, numeric results, caveats and potential rollout.
- [results.csv](results.csv): metrics by case, access policy, random seed and vehicle group.
- [results.json](results.json): complete frozen results plus network geometry and municipal overlays.
- `runs/` (ignored): SUMO XML outputs, route definitions, stops, logs and per-run results.
- `data/manifest.json`: original source URLs, input checksums and lane corrections.
- `data/network.osm.xml.gz`, `data/frozen/`: public input snapshots, retained for reproducibility.

## What is real and what is assumed

**Source data:** OSM highway geometry and access tags, fetched 28 October 2026 through nine official map API tiles; municipal BUS-corridor and loading-area GeoJSON snapshots; published STCP GTFS schedule. The selected GTFS service is **2 September 2026, 08:00–09:00**, a holiday weekday with 21 mappable bus trips on routes 701, 702 and 703. This is a dated schedule, not present-day service. A public bus-position snapshot is archived as reference only and does not calibrate the traffic or bus lateness.

**Assumptions:** 60 minutes of demand from an empty network plus 30 minutes to drain; three synthetic demand cases and three seeds (17/42/73); 20-second bus dwell, generated signal timings, perfect restriction compliance, static fastest routing within a buffered district. Sumolib's mutable partial-route cache is disabled; only complete routes are memoized to keep worker query order from changing paths. No measured traffic OD, turning counts, passenger demand, permit registry or observed upstream bus lateness.

**Lane premise:** the OSM import created some stretches with two general lanes plus a contraflow lane. Eight directed stretches were normalized to one lane per mapped direction to model the user's two-lane premise. Existing mapped directions and bus/bike contraflow permissions remain in the baseline. This correction is a hypothesis requiring a field/layout audit, not a surveyed inventory.

**Local-resident proxy:** `custom1` is a synthetic SUMO permit class with ordinary-car shape. Only trips starting or ending on a corridor road edge receive it. This does not mean all passenger cars are exempt, nor does it establish real resident eligibility. Access to adjacent streets and legitimate non-resident visits/deliveries needs a real policy decision; those rights are not inferred.

**Crossings:** ordinary passenger cars retain direct mapped crossing connections; no Costa Cabral road edge may appear in their restricted routes. Five direct crossing OD pairs are available in this imported graph. Staggered crossings requiring a longitudinal Costa Cabral link do not receive an exception. This limited generated crossing demand is not a traffic count.

**Accounting:** requested journeys are held fixed within each baseline/restricted pair. Missing permitted routes, insertion failures and unfinished trips remain visible. Teleporting is disabled. Completed-trip means can be biased when completion differs: do not interpret the reported bus gains as an equal-served-demand welfare comparison. Some routes may need a larger district to find a legitimate diversion; some baseline queues expose unvalidated junction/traffic assumptions.

**Bus measurement:** buses start at their first mapped corridor stop. Entry queue delay is SUMO insertion delay, shown separately. Final-stop arrivals ≤180 seconds late are an illustrative corridor metric, not an STCP punctuality standard or an observation of current reliability. All 21 requested trips mapped; unfinished stop sequences count as failures.

## Capture / verdict

Captured on throwaway branch `prototype/costa-cabral-access`. The portable policy module lives in a separate script block in the HTML template. No production decision has been validated, so no simulation logic was promoted into production. The branch and findings commit are the context pointer; no implementation issue existed in this initially empty repository.

Verdict: the requested access/crossing distinction is expressible and inspectable. Real-world bus-reliability gains, safe diversion capacity, eligibility/enforcement design, construction costs and implementation phases remain open and need matched observations and engineering work.

## Source attribution

- © OpenStreetMap contributors, ODbL: <https://www.openstreetmap.org/copyright>. Original tile URLs in `data/osm-source-urls.json`.
- Município do Porto / Porto Digital municipal BUS and loading datasets: CC0 as declared in their catalogue. URLs and SHA-256 in the manifest.
- STCP schedule: CC0 as declared in the municipal catalogue; archive service date/version retained. <https://dadosabertos.cm-porto.pt/en/dataset/horarios-paragens-e-rotas-stcp>
- SUMO 1.28.0: EPL-2.0 OR GPL-2.0-or-later. <https://eclipse.dev/sumo/>

This is scratch code and frozen experimental output. No tests or production framework were added.

## Verification performed

The one-command workflow completed all 18 scenario runs. A saved baseline scenario was replayed with an identical route file and identical group metrics after disabling mutable partial-route caching. All final runs reported zero teleports. Browser DOM checks covered shortcut rejection, crossing/resident access, demand switching, a complete guided walkthrough and report generation; 6,018 road polylines rendered without horizontal page overflow. No production test suite was introduced.

## Proposal video and website

**Integrated 3D:** choose **Explore in 3D / Explorar em 3D** above the replay, or open `proposal/index.html?dimension=3d&camera=conde&view=restricted` through the local HTTP server. Orbit around synchronized baseline/proposal views, move a street-level camera, follow the same bus, hide buildings, share the camera pose or record the 3D view to WebM. See [3D.md](3D.md) for controls, provenance and verification. The view uses one-second native trajectories and SUMO vehicle dimensions, with 2,089 mapped building footprints. Terrain is flat and building heights are estimated; this is not a surveyed city. 3D requires HTTP(S), WebGL2 and DecompressionStream; the original 2D HTML still opens directly.

Open `proposal/index.html` for the bilingual public-facing presentation. Its PT/EN switch also changes the captioned film. Two 60-second 1080p H.264 videos are included:

- `proposal/costa-cabral-pt.mp4`
- `proposal/costa-cabral-en.mp4`

The replay uses actual SUMO FCD outputs from seed 17, synchronized between policies, from 08:12 to 08:24. Positions are sampled every four seconds and interpolated for playback; vehicle symbols are enlarged for legibility. The displayed numerical outcomes still aggregate three seeds from the full one-hour experiment. These are simulated trajectories, not observed vehicle tracking.

The site controls demand case, camera/junction, comparison versus a single policy, replay time, speed and language. It exports the current selection as JSON. In a browser supporting MediaRecorder/canvas.captureStream, **Record view (WebM)** records the selected camera, language, demand and policy view from its current time to the end. This recording remains local in the browser and does not call a simulation service. It is a replay of precomputed scenarios; new access rules or demand values still require the Python experiment runner.

Rebuild the full presentation with one command (requires `ffmpeg`):

```sh
./prototypes/costa-cabral/export-proposal.sh
```

Use `--skip-video` to rebuild only the site/archive after changing text or layout. `--case busy --camera conde --language both` renders another predefined scenario/camera. The standardized MP4 filenames are replaced, so rerun the default command to restore the original moderate-demand films.

`costa-cabral-proposal-site.zip` is the portable website export. Unzip and upload **all files and nested folders together** to a static host; `index.html` is the entry point. There is no backend, database, API key, build step or remote JavaScript dependency. Three.js 0.186.1 and its MIT licence are bundled under `vendor/`; retain `inspection-assets/` and `inspection-3d.js` as well. A local preview link is local to the user's machine; this task prepares the bundle without publishing it to a public host. Keep both MP4s, posters and the supporting result/source files beside the HTML.

The compressed native replay dataset is retained in `media/replays.json.gz`. Native FCD XML and capture logs are under ignored `runs/media/`. Hashes of the source network, routes and stop definitions accompany each replay. Adding capture preserved all 60 completed stop events in the checked baseline clip exactly.
