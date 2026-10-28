# Invicta

A bilingual, interactive Porto mobility demo: help buses meet their schedules while keeping everyday access workable for residents, shoppers and other travellers.

The current pilot follows **STCP 701 towards Bolhão, from Areosa to Marquês**, using 13 official stops and the actual route through Costa Cabral, Alegria and Constituição. Compare scheduled references, timestamped GPS passage windows and native SUMO experiments; explore bus priority by stop interval and inspect the baseline/candidate replay in 3D.

**Exploratory prototype:** traffic demand, signal operation and dwell times are uncalibrated. The short GPS sample does not establish recurring delays or their causes. Structural car-connectivity checks need field verification. This is a section of one direction, not a validated model of the full bus line.

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

Vercel configuration reference: [project configuration](https://vercel.com/docs/project-configuration/vercel-json).
