# Invicta

[Live demo](https://invicta-dusky.vercel.app/?lang=pt#route) · [Open in 3D](https://invicta-dusky.vercel.app/?lang=pt&dimension=3d&camera=combatentes&view=compare#replay)

A bilingual, interactive Porto mobility demo: help buses meet their schedules while keeping everyday access workable for residents, shoppers and other travellers.

Switch between **2D planning** (map, sections and timetables) and **3D inspection** (streets, queues and native vehicle replay), retaining the same direction and scenario.

Explore **the full 701 in both directions**, including Codiceira and Ermesinde, on an interactive street map. Each direction keeps its own selected section and trip. Shared links restore those selections, language, scenario and camera; the public summary expands into timetable and source detail. In 3D, camera movement defaults to **3×**, with **1× / 3× / 10×** controls and an additional **Shift boost**.

The native traffic study runs **the complete 701 in both directions in the same regional simulation**: 56 inbound stops, 54 outbound stops and all 127 scheduled workings, including short trips and service after midnight. Baseline and priority policies use identical requested demand. Full-day results are paired with a 16:50–18:20 native 3D replay across the entire line. A separate inbound passenger/berth model explores dwell, capacity and bunching feedback.

**Exploratory prototype:** traffic, passenger demand, signals, dwell and recovery are uncalibrated. The short GPS sample does not establish recurring delays or causes. Connectivity checks need field verification. Both directions and regional road traffic are simulated with synthetic demand. Other bus routes and shared physical vehicle rotations are not modelled. The strict zero-lateness goal can be tested, but actual punctuality is not guaranteed.

## Open locally

```sh
python3 -m http.server 8765 --directory prototypes/costa-cabral/proposal
# http://127.0.0.1:8765/?lang=pt
```

Switch between Portuguese and English, select journeys and scenarios, export a policy or explanation, and record the 3D replay as WebM. Browser uploads stay in memory and are included only when you explicitly share or export the proposal. The earlier street study, films and metropolitan transition calculator are under `legacy.html`.

## Source and reproducibility

- [701 pilot and commands](prototypes/line-701/README.md)
- [Full traffic study and reproduction](prototypes/line-701/full/README.md)
- [701 findings and limitations](prototypes/line-701/REPORT.md)
- [Architecture and validation](docs/ARCHITECTURE.md)
- [Official route and timetable research](docs/research/line-701-data-and-direction.md)
- [Outbound route, timetable matching and source dates](docs/research/line-701-outbound.md)
- [Project objectives](docs/PROJECT_BRIEF.md)
- [Earlier Costa Cabral experiment](prototypes/costa-cabral/README.md)

SUMO owns vehicle movement. Website controls select precomputed runs; new combinations require a local native rerun. Inputs retain source URLs, timestamps and hashes. OSM, STCP, Porto Digital and third-party software retain their respective attribution and licence terms.

## Deploy on Vercel

From this repository's root:

```sh
vercel login
vercel link
node scripts/prepare-deployment.mjs
# Commit and push the updated site and deployment manifest first.
vercel deploy --prod --yes --scope jos-cabedas-projects --build-env INVICTA_ASSET_COMMIT="$(git rev-parse HEAD)"
```

[`vercel.json`](vercel.json) serves the checked-in `prototypes/costa-cabral/proposal` folder, with no install step, simulation job or server. The build restores large assets from the exact pushed public GitHub commit and checks their hashes. New proposals are generated locally, committed and deployed as static assets. Keep the asset folders and `vendor/` together. Compressed replay files are fetched and decompressed by the viewer; do not add a `Content-Encoding: gzip` header to those stored gzip payloads.

The live project is `invicta` in `jos-cabedas-projects`. It uses direct CLI deployment; pushing to GitHub does not automatically publish a new website version. See [deployment details](docs/DEPLOYMENT.md).

Vercel configuration reference: [project configuration](https://vercel.com/docs/project-configuration/vercel-json).
