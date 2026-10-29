# Invicta

[Live demo](https://invicta-dusky.vercel.app/?lang=pt#route) · [Open in 3D](https://invicta-dusky.vercel.app/?lang=pt&dimension=3d&camera=combatentes&view=compare#replay)

A bilingual, interactive Porto mobility demo: help buses meet their schedules while keeping everyday access workable for residents, shoppers and other travellers.

Explore **the full 701 in both directions**, including Codiceira and Ermesinde, on an interactive street map. Each direction keeps its own selected section and trip. Shared links restore those selections, language, scenario and camera; the public summary expands into timetable and source detail. In 3D, camera movement defaults to **3×**, with **1× / 3× / 10×** controls and an additional **Shift boost**.

The native street pilot follows **STCP 701 through the entire Porto municipal extent to Bolhão**, with 16 official stops and the boundary approach before Areosa. A separate whole-line service model uses all 56 stops and 63 inbound workings to test passenger/dwell feedback, bunching, capacity and schedule/headway controls. Compare scheduled references, timestamped GPS passages and native SUMO results; inspect the Porto baseline/candidate replay in 3D.

**Exploratory prototype:** traffic, passenger demand, signals, dwell and recovery are uncalibrated. The short GPS sample does not establish recurring delays or causes. Connectivity checks need field verification. Whole-line service dynamics are assumed; outside-Porto road traffic, the reverse direction, other routes and shared vehicle rotations are not modelled. The strict zero-lateness goal can be tested, but actual punctuality is not guaranteed.

## Open locally

```sh
python3 -m http.server 8765 --directory prototypes/costa-cabral/proposal
# http://127.0.0.1:8765/?lang=pt
```

Switch between Portuguese and English, select journeys and scenarios, export a policy or explanation, and record the 3D replay as WebM. Browser uploads stay in memory. The earlier street study, films and metropolitan transition calculator are under `legacy.html`.

## Source and reproducibility

- [701 pilot and commands](prototypes/line-701/README.md)
- [701 findings and limitations](prototypes/line-701/REPORT.md)
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
vercel --prod
```

[`vercel.json`](vercel.json) serves the checked-in `prototypes/costa-cabral/proposal` folder, with no install step, simulation job or server. New proposals are generated locally, committed and deployed as static assets. Keep the asset folders and `vendor/` together. Compressed replay files are fetched and decompressed by the viewer; do not add a `Content-Encoding: gzip` header to those stored gzip payloads.

The live project is `invicta` in `jos-cabedas-projects`. It uses direct CLI deployment; pushing to GitHub does not automatically publish a new website version. See [deployment details](docs/DEPLOYMENT.md).

Vercel configuration reference: [project configuration](https://vercel.com/docs/project-configuration/vercel-json).
