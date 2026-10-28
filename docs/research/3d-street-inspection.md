# Inspecting the Costa Cabral simulation in 3D

Research checked **28 October 2026**. The initial feasibility recommendation has now been implemented as a browser 3D inspection prototype. See [the implementation and verification notes](../../prototypes/costa-cabral/3D.md). CARLA and surveyed terrain have not been installed or added.

## Recommendation for this project

**Yes: add a browser-based 3D replay of the existing SUMO runs. Start with Three.js, then add verified terrain/building data only where useful.** The immediate goal should be inspecting street allocation, junction crossings, bus queues and proposed changes from several viewpoints. Rendering should use the frozen trajectories and scenario identifiers already associated with the report. A 3D view improves inspection and communication; it does not validate demand, traffic rules, punctuality or the proposed policy.

The existing project already has a static presentation and code that exports SUMO FCD trajectories, sampled every four seconds, with vehicle identifiers, positions, heading, speed, scenario and source-input hashes. This is a practical basis for a 3D viewer, although its current export does not request elevation. See the local [capture script](../../prototypes/costa-cabral/capture_replay.py) and [prototype documentation](../../prototypes/costa-cabral/README.md). This is a code inspection finding, not a new simulation run.

| Path | What is verified | Assessment for Costa Cabral |
| --- | --- | --- |
| **Three.js static replay** | Extruded shapes, efficient repeated meshes and orbit/pan/zoom camera controls are documented. | **Recommended first step.** Reuse the current replay and package dependencies/assets with a portable static site. [Extrusion](https://threejs.org/docs/pages/ExtrudeGeometry.html), [instancing](https://threejs.org/docs/pages/InstancedMesh.html), [camera controls](https://threejs.org/docs/pages/OrbitControls.html). |
| **CesiumJS geospatial replay** | Time-sampled positions, glTF vehicle models, terrain and geospatial content are documented. | Prefer if terrain, geographic context and larger city extents become central. Hosted basemaps/tiles bring separate access and licensing requirements. [Positions](https://cesium.com/learn/cesiumjs/ref-doc/SampledPositionProperty.html), [models](https://cesium.com/learn/cesiumjs/ref-doc/ModelGraphics.html), [quickstart](https://cesium.com/learn/cesiumjs-learn/cesiumjs-quickstart/). |
| **SUMO native 3D** | Available when `sumo-gui` is compiled with OpenSceneGraph. | Useful for a local technical check if a suitable build is available; officially experimental and less suitable as the shareable presentation. [SUMO GUI](https://eclipse.dev/sumo/docs/sumo-gui.html#3d-visualization). |
| **CARLA + SUMO co-simulation** | A documented integration synchronises compatible maps, vehicles and traffic lights. | A later option for detailed driving/sensor/physical-environment questions. Requires considerably more map preparation and a supported GPU server environment. [CARLA 0.9.16 integration](https://carla.readthedocs.io/en/0.9.16/adv_sumo/). |

## Native SUMO 3D: real capability, limited presentation path

With OpenSceneGraph enabled, `sumo-gui --osg-view true` opens a 3D view. Roads, junctions, crossings and traffic lights are generated; static models can be placed through GUI-settings decals, and vehicle types can specify `osgFile`. The official documentation labels this **experimental**, listing missing pedestrian/cyclist models, vehicle-rendering performance problems and a reload issue. Buildings and detailed street furniture are not automatically reconstructed as a surveyed city. [SUMO 3D capabilities and limitations](https://eclipse.dev/sumo/docs/sumo-gui.html#3d-visualization).

SUMO documents macOS installation, but that does not establish OpenSceneGraph support in a particular binary. The companion [local audit](costa-cabral-report-variables.md) checked this project's SUMO GUI 1.28.0 feature list: it advertises GUI support but **does not advertise OSG**. A native 3D view was not launched or tested. This strengthens the recommendation to extend the browser replay. [Official installation guidance](https://eclipse.dev/sumo/docs/Installing/).

## Browser replay: how to keep it useful and honest

The proposed pipeline is **SUMO network + frozen trajectory export → preprocessed scene/replay assets → static browser viewer**. Three.js supplies rendering primitives, not a SUMO importer; scene conversion and playback are application code. It can extrude building footprints and instance vehicles, while `OrbitControls` supports inspection from different viewpoints. [Three.js extrusion](https://threejs.org/docs/pages/ExtrudeGeometry.html), [repeated meshes](https://threejs.org/docs/pages/InstancedMesh.html), [controls](https://threejs.org/docs/pages/OrbitControls.html).

Recommended implementation rules:

- Generate road/lane geometry from the **same network version** used by the selected run. Show the restriction boundaries and permitted direct crossings explicitly; generic street scenery must not override the model's actual connectivity.
- Preserve the original simulation clock, IDs and source hashes. Let users switch baseline/proposal, follow a bus, scrub time, hide buildings and inspect a junction. Editing a policy or demand assumption still requires rerunning the Python/SUMO workflow.
- FCD coordinates refer to the **centre of the vehicle's front bumper**, so a model centred at its midpoint needs an offset. Preserve heading/units and the SUMO projection/offset when converting coordinates. FCD supports geographic output and a `z` field when present. [SUMO FCD specification](https://eclipse.dev/sumo/docs/Simulation/Output/FCDOutput.html).
- Current four-second sampling is appropriate for an overview but can interpolate through junction corners. Capture at the existing simulation step first, or use lane-aware interpolation, before making close-up movement claims. A smaller simulation timestep is a deliberate rerun requiring comparison, rather than a way to invent precision from existing samples. Interpolation creates a display between samples, not additional observed or simulated events.
- Label missing building heights as illustrative, and keep actual versus enlarged vehicle scale selectable. Attractive buildings do not establish accurate curb positions, sightlines, accessibility clearances or crash risk.
- Bundle a pinned renderer and all needed assets locally. A static HTTP host is sufficient; browser module/model loading should not rely on opening the HTML directly from disk. Three.js documents production static export and the limitations of `file://` loading. [Deployment guidance](https://threejs.org/manual/pages/installation.html).

CesiumJS offers a more geographic version of the same architecture: feed trajectories into `SampledPositionProperty` and attach glTF vehicles. Its default position interpolation is linear. The standard tutorial uses Cesium ion tokens for hosted terrain/buildings; those services are distinct from the open-source viewer and should not become an unnoticed requirement of an offline package. No Porto-specific photorealistic tileset was verified here. [Sampled positions](https://cesium.com/learn/cesiumjs/ref-doc/SampledPositionProperty.html), [glTF models](https://cesium.com/learn/cesiumjs/ref-doc/ModelGraphics.html), [hosting/content setup](https://cesium.com/learn/cesiumjs-learn/cesiumjs-quickstart/).

## Terrain and buildings: Portuguese sources and verified access limits

**DGT LiDAR is a credible terrain source.** Official products include classified point clouds and bare-earth MDT / surface MDS GeoTIFFs at 0.5 m and 2 m grid spacing. Grid spacing and point density are not survey-accuracy guarantees. A June 2026 DGT notice still warns about incomplete northwest availability, so national coverage statements alone do not prove a particular Porto tile is downloadable. [DGT products](https://www.dgterritorio.gov.pt/atividades/cartografia/cartografia-topografica/modelos-digitais), [availability notice](https://www.dgterritorio.gov.pt/descarregamento-de-dados-lidar-de-portugal-continental).

A read-only **official DGT metadata probe** succeeded on 28 October 2026: `POST https://cdd.dgterritorio.gov.pt/dgt-be/v1/search`, with `{"collections":["MDT-2m"],"bbox":[-8.615,41.16,-8.585,41.19],"limit":2}`, returned two Porto-area tile records. One was `MDT-2m-162469-07-2025`, advertised as GeoTIFF, metre-valued, EPSG:3763. A bounded request to its asset URL redirected to an authentication page and returned HTML; **no terrain file was obtained or inspected**. Thus local tile metadata is confirmed, complete corridor coverage and authenticated download access remain unresolved. Use the [DGT data centre](https://cdd.dgterritorio.gov.pt/dgt-fe/) for access; do not embed temporary asset links or account credentials in the public site.

For building context, DGT publishes the **experimental Mapa de Construções LiDAR 2024**, with a CC BY 4.0 catalogue licence. It represents construction polygons extracted from LiDAR, and explicitly warns that nearby buildings can merge into one polygon and that the product should not identify individual buildings. It is useful for context after clipping/checking; it is not a ready-made textured 3D city or a verified height attribute source. [Official DGT catalogue entry](https://dados.gov.pt/pt/datasets/mapa-de-construcoes-lidar-2024).

Porto's municipality separately offers requested **digital planimetry and altimetry**, including built fabric, sidewalks, streets, spot heights and contours. This is a request/quotation/licence process, not a verified open API or free 3D city download. It could be more useful for engineering geometry than decorative building detail. [Municipal digital cartography service](https://portaldomunicipe.cm-porto.pt/-/informa%C3%A7%C3%A3o-urban%C3%ADstica-digital-1).

If elevation is added to the simulator, SUMO supports importing GeoTIFF heightmaps and identifies particular models that consume elevation. Draping the browser scene on terrain does **not** automatically make simulated buses respond to hills. Align horizontal/vertical references, road levels and bridges before using heights in behaviour or costs. [SUMO elevation support](https://eclipse.dev/sumo/docs/Networks/Elevation.html).

## CARLA: defer until the question requires it

The versioned **CARLA 0.9.16** integration documents generating a compatible SUMO network from OpenDRIVE and synchronising both engines. Its traffic-light conversion has a material limitation: SUMO can distinguish lane-specific lights that CARLA's integration cannot, requiring an explicit reconciliation. A converted map must therefore be compared against the access/crossing semantics already established for Costa Cabral. [Versioned co-simulation documentation](https://carla.readthedocs.io/en/0.9.16/adv_sumo/).

CARLA can convert OSM to OpenDRIVE through Python, but the standalone road mesh is minimal; buildings and a realistic streetscape are additional work. Errors in OpenDRIVE propagate into the scene, and the generator may widen/smooth junction geometry. [OSM conversion](https://carla.readthedocs.io/en/latest/tuto_G_openstreetmap/), [OpenDRIVE mode](https://carla.readthedocs.io/en/latest/adv_opendrive/).

Official CARLA server installation paths target **Windows/Linux**, rather than native macOS. UE4/UE5 documentation and releases differ; pin a compatible CARLA/SUMO stack and test the actual co-simulation instead of assuming feature parity across branches. The current UE5 installation page requires a substantial GPU environment for rendering. This is a separate workstation/server project, not a small extension of the present static site. [UE4 package requirements](https://carla.readthedocs.io/en/latest/start_quickstart/), [UE5 requirements](https://carla-ue5.readthedocs.io/en/latest/start_quickstart/), [0.9.16 release](https://carla.org/2025/09/16/release-0.9.16/).

## Proposed stages

1. **Inspect the existing model in browser 3D:** real network geometry, simple car/bus meshes, synchronised baseline/proposal, clock and junction selection. Keep assumed scenery visibly distinct. This can reuse existing SUMO results.
2. **Add verified geographic context:** confirm terrain download coverage, clip building footprints, validate heights/road levels and improve capture frequency for close-ups. Recalculate simulation results only when changing model inputs, not merely camera/scenery.
3. **Engineering or driving fidelity only when needed:** obtain accurate curb/grade/signal geometry and consider CARLA if sensor, driving or detailed physical interaction questions justify its map/server cost.

The first stage is sufficient to answer “can we look around the simulated street in 3D?”; it does not remove the missing-observation priorities in the traffic report.
