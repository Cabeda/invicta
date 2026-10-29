# 701: official signal and crossing data, across both directions

Verified **29 October 2026, 16:26–16:33 UTC**, through public official websites and read-only APIs. This supplements the existing [data audit](traffic-simulation-tools.md#porto-open-data-enrichment), [inbound extent](line-701-porto-extent.md) and [outbound snapshot](line-701-outbound.md). No application, published dataset or simulation input was changed for this research.

**Usable official location data exists for Porto, Maia and Valongo, but no current public controller plans, phase/cycle/offset tables, pedestrian clearance times or 701 priority logic were verified.** Porto offers explicitly CCZero downloads. Maia and Valongo expose useful public records whose reuse licences remain unverified; their dated attributes are old. A location inventory can challenge imported OSM signal positions; it cannot replace the model's generated timings with observed timings.

## What is actually downloadable

| Source | Contents actually parsed | Age, coverage and reuse boundary |
|---|---|---|
| [Porto signal dataset](https://dadosabertos.cm-porto.pt/dataset/sistema-de-gestao-de-trafego-semaforos) | 2,522 equipment points; 294 distinct non-null installation strings, with 18 records missing the installation. GeoJSON and CSV; a CKAN DataStore query also works. | Municipality of Porto; **CCZero**. Declared biweekly frequency, metadata modified 1 October 2026, resource `last_modified` 4 September. No survey/effective date is supplied. Counts describe records, not intersections/controllers. [Metadata](https://dadosabertos.cm-porto.pt/api/3/action/package_show?id=sistema-de-gestao-de-trafego-semaforos), [GeoJSON](https://dadosabertos.cm-porto.pt/dataset/63c06501-9e19-11f1-84ed-6abdb6d5cf34/resource/4f67e2f7-f445-4f18-b3cb-211ea8c7c098/download/ext-sistema-de-gestao-de-trafego-semaforos-geojson.geojson) |
| [Porto LED crossings](https://dadosabertos.cm-porto.pt/dataset/sinalizacao-led-em-travessias-de-peoes) | 37 points describing the **LED-equipped subset** of pedestrian crossings. | Porto; **CCZero**; same declared frequency and September-resource/October-metadata distinction. Does not enumerate all crossings, identify their complete geometry or establish traffic-signal control. [Metadata](https://dadosabertos.cm-porto.pt/api/3/action/package_show?id=sinalizacao-led-em-travessias-de-peoes), [GeoJSON](https://dadosabertos.cm-porto.pt/dataset/63519d35-9e19-11f1-84ed-6abdb6d5cf34/resource/f1e9e386-88e6-42ab-9363-5dd5b4f6e3d7/download/ext-sinalizacao-led-em-travessias-de-peoes-geojson.geojson) |
| [Maia BaZe](https://baze.cm-maia.pt/BaZe/base2b.htm?e0=Semaforos) | Public `Semaforos` API returns 60 point features, with MAIA identifiers and operational status embedded in HTML popup text; metadata names **Soltráfego** as the source. | All 60 embedded status timestamps are **2020**. Neither current operation nor complete municipal coverage is established. No reuse licence/update contract was found in the inspected response or viewer. [API](https://baze.cm-maia.pt/BaZe/api/api4gj.php?nome=Semaforos) |
| [Valongo municipal ArcGIS roads service](https://sig.cm-valongo.pt/arcgis/rest/services/MuniSIG/MXD_VIAS_2016/MapServer?f=pjson) | Layer **11**, `Apoio Sinal Luminoso`, has 172 signal-support points. Related table **12**, `Sinalização Luminosa`, has 416 signal records, including 123 labelled pedestrian signals. | All support `DataUltima` values are **19 June–17 July 2009**. The service name's `2016` is not a survey date. The inspected service has empty copyright text and no verified reuse licence. Public access does not establish redistribution rights. [Support schema](https://sig.cm-valongo.pt/arcgis/rest/services/MuniSIG/MXD_VIAS_2016/MapServer/11?f=pjson), [table schema](https://sig.cm-valongo.pt/arcgis/rest/services/MuniSIG/MXD_VIAS_2016/MapServer/12?f=pjson) |

The complete Porto GeoJSON files are byte-identical to those reported in the 28 October repository audit. That confirms unchanged export bytes, not unchanged on-street conditions. The [Porto catalogue API](https://dadosabertos.cm-porto.pt/api/3/action/package_search?rows=1000) again returned 69 dataset listings; no complete crossing/controller-plan dataset was identified in that snapshot.

## Endpoint and field contracts

**Porto signal points:** `FeatureCollection`, point coordinates, and exactly `equipamento`, `numero_instalacao`, `wifi`, `objectid`. Preserve `numero_instalacao` as text: values include leading zeroes, suffix letters, combined identifiers and spaces. There is no signal orientation, vehicle/pedestrian head type, approach/lane assignment, controlled movement, controller program or phase duration. `wifi` is missing/unknown/absent in the inspected records; it does not expose signal status. [Raw GeoJSON](https://dadosabertos.cm-porto.pt/dataset/63c06501-9e19-11f1-84ed-6abdb6d5cf34/resource/4f67e2f7-f445-4f18-b3cb-211ea8c7c098/download/ext-sistema-de-gestao-de-trafego-semaforos-geojson.geojson).

The tabular API is:

```text
https://dadosabertos.cm-porto.pt/api/3/action/datastore_search?resource_id=c70d0b05-908c-43f4-a7eb-316cae38df94&limit=1
```

It reports `total=2522` and adds `_id` and `esriGeometryPoint`. The latter is projected `x,y` text. Catalogue CRS is **EPSG:3763**, whereas downloaded GeoJSON coordinates are longitude/latitude with no `crs` member. Transforming the first tabular point from EPSG:3763 to EPSG:4326 reproduces its GeoJSON position within approximately 0.0001 m. This verifies the coordinate interpretation for that paired sample; do not interpret GeoJSON degrees as TM06 metres. [DataStore response](https://dadosabertos.cm-porto.pt/api/3/action/datastore_search?resource_id=c70d0b05-908c-43f4-a7eb-316cae38df94&limit=1).

**Porto LED points:** `toponimo`, `numero_travessias`, `numero_sinais_h7`, `objectid`, `globalid`. These supply street names and inventory quantities, rather than crossing endpoints, widths, refuge islands or pedestrian stages. **Other road markings** is not a substitute: its 415 exported points have `tipo_marca` values `A14`, `20`, `M17b`, `RSU`, `30`; no explicit general pedestrian-crossing type was found. Decode publisher codes before using them as regulatory facts. [LED download](https://dadosabertos.cm-porto.pt/dataset/63519d35-9e19-11f1-84ed-6abdb6d5cf34/resource/f1e9e386-88e6-42ab-9363-5dd5b4f6e3d7/download/ext-sinalizacao-led-em-travessias-de-peoes-geojson.geojson), [markings download](https://dadosabertos.cm-porto.pt/dataset/5c4eb941-9e19-11f1-84ed-6abdb6d5cf34/resource/1ca88f6d-c51e-4619-bd06-1b649fe2d2f4/download/ext-marcas-rodoviarias-diversas-na-faixa-de-rodagem-geojson.geojson).

**Maia:** parse UTF-8 with BOM. Features have `properties.popupContent` and `properties.icon`; the stable-looking `MAIA.xxx` identifier, status and timestamp require HTML-text parsing. The collection metadata has `name`, `desc`, `fonte`, with date and curator null. Do not treat an `Em Operação` popup from 2020 as a live state, and do not promote the display icon into a current red/amber/green indication. [API](https://baze.cm-maia.pt/BaZe/api/api4gj.php?nome=Semaforos).

**Valongo:** these bounded public queries returned the complete totals independently reported by `returnCountOnly=true`, below the service's 1,000-record limit:

```text
https://sig.cm-valongo.pt/arcgis/rest/services/MuniSIG/MXD_VIAS_2016/MapServer/11/query?where=1%3D1&outFields=*&outSR=4326&f=geojson
https://sig.cm-valongo.pt/arcgis/rest/services/MuniSIG/MXD_VIAS_2016/MapServer/12/query?where=1%3D1&outFields=*&returnGeometry=false&f=json
```

Support attributes include `OBJECTID_1`, `RUA_ID`, `TipoApoio`, `EstadoCons`, `FotoEnquad`, `Observacoe`, `DataUltima`, `IDApoioLuminoso`. Table fields include `IDSinalLum`, `IDApoioLum`, `SINALTRANS`, `EstadoCons`, `IDApoioLuminoso`. The declared one-to-many relationship uses **`IDApoioLuminoso`**. Pedestrian-head records can be located through that relationship; they still do not define crossing geometry or timing. Native service CRS is ESRI **102161**, different from Porto TM06; request `outSR=4326` as above rather than combining raw projected coordinates. [172-point response](https://sig.cm-valongo.pt/arcgis/rest/services/MuniSIG/MXD_VIAS_2016/MapServer/11/query?where=1%3D1&outFields=*&outSR=4326&f=geojson), [416-row response](https://sig.cm-valongo.pt/arcgis/rest/services/MuniSIG/MXD_VIAS_2016/MapServer/12/query?where=1%3D1&outFields=*&returnGeometry=false&f=json).

Valongo road layer **7**, `Faixa de Rodagem`, offers polyline geometry, `IDEixoVia`, `LarguraMed`, `TipoPavime`, `EstadoCons`, `DataObserv`. Its schema lacks lane counts, directions, turn restrictions and speed limits. It is a geometry/width lead, subject to its age and unresolved reuse terms. [Road schema](https://sig.cm-valongo.pt/arcgis/rest/services/MuniSIG/MXD_VIAS_2016/MapServer/7?f=pjson).

## Whole-line proximity screen, not a junction survey

I projected both **complete frozen STCP shapes** to EPSG:3763 and calculated each inventory point's minimum distance to each ordered polyline. Source shapes retain their existing provenance: inbound 28 October retrieval, outbound 29 October retrieval; neither is a verified historical street survey. No municipal clipping was applied, so the screen covers Codiceira/Alfena, Ermesinde, Maia, the Areosa boundary area and Porto. [Official direction 0 shape](https://stcp.pt/api/route/701/shape?direction_id=0), [direction 1 shape](https://stcp.pt/api/route/701/shape?direction_id=1).

| Inventory | Outbound direction 0: ≤20 / ≤40 / ≤75 m | Inbound direction 1: ≤20 / ≤40 / ≤75 m |
|---|---:|---:|
| Porto signal equipment | 95 / **106** / 121 | 96 / **100** / 121 |
| Porto LED crossing points | 1 / **1** / 1 | 2 / **2** / 2 |
| Maia signals | 3 / **3** / 3 | 3 / **3** / 3 |
| Valongo signal supports | 16 / **19** / 23 | 22 / **23** / 23 |

These are **derived candidate counts**, not counts of junctions controlling the bus or proof of complete coverage. Adjacent streets, pedestrian heads and approach-side equipment can enter a buffer; a missing point may be an incomplete/old inventory. The 40 m Porto candidates have 12 outbound and 10 inbound installation strings, also not verified controller counts.

Concrete leads:

- Porto LED `objectid=29`, **Rua de Costa Cabral**, `[-8.5920294162, 41.1680868421]`, is approximately 2.0–2.5 m from both shapes. `objectid=2433`, **Rua da Constituição**, `[-8.6015908414, 41.1615035826]`, is approximately 1.5 m from inbound only. The records each declare one crossing and two H7 signs. [LED source](https://dadosabertos.cm-porto.pt/dataset/63519d35-9e19-11f1-84ed-6abdb6d5cf34/resource/f1e9e386-88e6-42ab-9363-5dd5b4f6e3d7/download/ext-sinalizacao-led-em-travessias-de-peoes-geojson.geojson).
- Maia **MAIA.001** `[-8.5671687126,41.2069755373]`, **MAIA.012** `[-8.5801398754,41.1913065390]`, **MAIA.045** `[-8.5705000162,41.2038719044]` are within 40 m of both shapes. Their status text is old. [Maia source](https://baze.cm-maia.pt/BaZe/api/api4gj.php?nome=Semaforos).
- Joining the Valongo 40 m candidates to table 12 yields 41 signal rows outbound, including 13 pedestrian-head records, and 51 inbound, including 17 pedestrian-head records. This is derived from the dated support inventory, not evidence of current crossing operation.

The full coordinate/property/distance review list is in `.cache/701-signal-research/route-proximity-screen.json`. A second screen, `network-proximity-screen.json`, uses the existing `prototypes/line-701/full/data/baseline.net.xml` projection and its **134 traffic-light junction nodes / 126 `tlLogic` IDs**. Across both route directions, the union of 40 m inventory candidates gives:

| Inventory | Candidate points | Points within 50 m of their nearest modeled traffic-light node | Distinct nearby modeled nodes |
|---|---:|---:|---:|
| Porto equipment | 139 | 113 | 12 |
| Maia | 3 | 1 | 1 |
| Valongo supports | 23 | 12 | 2 |
| Porto LED | 2 | 0 | 0 |

Maia's nearby modeled node is `269567465`; Valongo's are `1155513031`, `1173439981`. The cache file lists every candidate's nearest node and distance, including Porto IDs. **No controller identity or controlled movement was verified by this nearest-neighbour calculation.** A close head and junction may be unrelated, and LED warning signs need not imply signal control. Review unmatched candidates before deciding whether to add/move junction control; obtain crossing endpoints before adding SUMO crossings/walking areas.

## Controller operation, other portals and evidence limits

The [Urban Platform mobility case](https://plataformaurbana.porto.digital/acao/#AVPGM) describes MobiDash, induction-loop sensors, bus movement, alerts and historical retention. It establishes an institutional acquisition lead, not public controller timings or unrestricted historical access. The [public broker type list](https://broker.fiware.urbanplatform.portodigital.pt/v2/types?limit=1000&options=values) returned 18 types, including `TrafficFlowObserved` and `Device`, but no signal-specific controller/phase type. Three sampled Device records described air-quality devices. This limited inspection cannot establish that no protected signal data exists.

The official Porto [GIS service directory](https://fedservergeo.cm-porto.pt/arcgis/rest/services?f=pjson) is public, but its [CityFlow](https://fedservergeo.cm-porto.pt/arcgis/rest/services/CityFlow?f=pjson) and [GESTAO_ATIVOS](https://fedservergeo.cm-porto.pt/arcgis/rest/services/GESTAO_ATIVOS?f=pjson) folders returned ArcGIS **499 Token Required**. Do not infer their contents from folder names. Public cartographic layers inspected did not establish a current, complete pedestrian-crossing/controller dataset. Porto's municipality also explicitly describes traffic CCTV as supervision **without image/sound recording**; an archive for retrospective crossing counts must not be assumed. [Municipal traffic management](https://mobilidade.cm-porto.pt/servicos/gestao-de-trafego).

[Gondomar's official geoportal](https://pdm.cm-gondomar.pt/geoportal/pt/Home/Index) loaded, but the inspected entry page and targeted official searches did not yield a downloadable corridor signal/crossing inventory or timing plan. This is a search boundary, not a finding that no such records exist. Valongo's [Mobilidade folder](https://sig.cm-valongo.pt/arcgis/rest/services/Mobilidade?f=pjson) was empty, while its older MuniSIG layer was accessible; its [OpenData folder](https://sig.cm-valongo.pt/arcgis/rest/services/ValongoOpenData?f=pjson) listed boundaries/toponymy only.

The [IMT NAP](https://www.nap-portugal.imt-ip.pt/nap/multimodal) is relevant for transport metadata, but the inspected [public information-type API](https://www.nap-portugal.imt-ip.pt/API/api/informationTypes?local=pt), [supplier list](https://www.nap-portugal.imt-ip.pt/API/api/suppliers/all) and [map response](https://www.nap-portugal.imt-ip.pt/API/api/mapElements/all/?local=pt) did not supply 701 signal/crossing/timing data. The map snapshot contained one IP roadworks item; do not generalize that to the whole NAP's institutional holdings. The Valongo-hosted [AMP service listing](https://sig.cm-valongo.pt/arcgis/rest/services/WEBSIGAMP?f=pjson) is another GIS lead, not verified operational control data. The AMP main website returned HTTP 403 during the direct probe.

**Planned priority is not implemented 701 priority.** Porto's official July 2026 [PMUS announcement](https://pactoparaoclima.porto.pt/plano-de-mobilidade-urbana-sustentavel-traca-estrategia-para-transformar-a-mobilidade-no-porto-na-proxima-decada/) describes implementing public-transport signal priority as a planned measure. No inspected source establishes an activated 701-specific scheme, eligible approaches, detector/bus identifiers, request conditions, green extension limits or priority event logs.

## Acquisition and SUMO handoff

1. **Integrate Porto's CCZero points as review evidence** with publisher, record ID, original installation text, coordinates, dates and hash. Preserve many-heads-to-one-junction relationships; do not convert every point into a separate controller.
2. **Keep Maia/Valongo provenance and age visible.** Verify reuse rights before redistributing those records; request a current inventory rather than publishing 2009/2020 states as operational truth.
3. **Ask each relevant road authority for the matched study period:** controller/site IDs and coordinates; signal-group-to-lane/turn/crossing mapping; stages/conflicts; amber/all-red and pedestrian clearance; time-of-day plans, cycle lengths and offsets; actuated detector logic; plan/version validity; and any bus-priority configuration/event logs. Include emergency and pedestrian constraints. This is a proposed acquisition request, not a message that has been sent.
4. **Obtain crossing geometry and current street operation.** Endpoints, widths, refuges, kerbs, walking connections, control/button arrangements, lane widths/counts/directions, turn restrictions and applicable signs remain necessary. A pedestrian signal head does not supply a SUMO crossing.
5. **Retain explicit assumed signal programs until replaced by validated plans.** Actual location points can improve topology review immediately; they do not calibrate timings, queue storage, bus delay or pedestrian waiting.

## Related speed-limit check for the regional route

The general heavy-passenger-vehicle **without trailer** limits are 20 km/h in coexistence zones, 50 in other locality zones, 80 on other public roads, 90 on reserved automobile/motorcycle roads, and 100 on motorways. The current consolidated Code's Article 27 makes general maxima subject to Articles 24–25 and lower imposed limits; Article 28 provides for specifically signposted limits. [Official consolidated Articles 27–28](https://diariodarepublica.pt/dr/legislacao-consolidada/lei/2013-116041830-116043263), [official republication with the table](https://files.diariodarepublica.pt/gratuitos/1s/2020/12/23802.pdf).

This supports auditing a whole-route model's inherited global 50 km/h vehicle cap, **not assuming that any particular 701 link legally permits more than 50**. Road-specific signage/classification, bus restrictions and operating/vehicle constraints must be checked separately. Imported OSM `maxspeed` values are unverified road evidence; a higher modeled physical vehicle cap does not authorize exceeding a road limit or establish an attainable operating speed. The limits do not replace crossing, curvature, visibility and traffic constraints.

## Reproducibility

Full bounded public responses are cached under `.cache/701-signal-research/`; `source-manifest.json` records URLs, successful/failed fetches, UTC retrieval time, byte count and SHA-256. The cache is research material and may be ignored by Git; preserve approved source bytes separately before making a durable ingestion bundle. Key hashes:

| File | SHA-256 |
|---|---|
| `porto-semaforos.geojson` | `cda5d669a0e1b3a8562eaa8cb367edd16eb02d399e4aaafe181af78c755eebff` |
| `porto-led-crossings.geojson` | `db51e5377115decddf3623d5bd7fbb8c9ebcf247358ab2345d9c382282ea15f4` |
| `maia-semaforos.json` | `8a620401c2b13dcf9435f0a0e4e4a5da1fa97b6af6073d945281d813c5a13f8a` |
| `valongo-signal-supports.geojson` | `5d00b8eb6e232b78812cbe9774350cd728e7e5e7d7f10a623506a5c9d5a08fdb` |
| `valongo-signal-table.json` | `0b36d60132b5828dd4cd3b1545e611476ac1081d29b9aa7aa21533a091215e98` |

Counts, schemas, dates, joins, coordinate interpretation and proximity screens were checked from the fetched bytes. No field validation, controller login, historical timing export, implemented-priority confirmation or calibrated traffic replay was performed by this research.
