COSTA CABRAL — STATIC PROPOSAL WEBSITE

Serve this whole folder with: python3 -m http.server 8080
Open http://localhost:8080/?dimension=3d for 3D, or omit the query for 2D.
The 2D page also opens directly; 3D modules/assets require HTTP and WebGL2.
A modern browser with DecompressionStream is required for compressed assets.

Publish by uploading ALL extracted files together to any static website host.
No backend, database, API key or build step is required.
Keep filenames and relative paths intact. index.html is the entry point.

PT/EN language switch. Synchronized actual SUMO trajectory replays.
2D map and 3D inspection: orbit, street camera, bus following, building toggle.
3D uses one-second SUMO output and model vehicle dimensions; 2D uses four seconds.
The 3D network is flat; building heights are estimated. Not a surveyed city.
Keep vendor/ and inspection-assets/ folders and inspection-3d.js in the export.
Three precomputed demand cases; these controls do not run new simulations.
MP4 videos have burned-in PT or EN captions.
The browser can record the selected view to WebM if MediaRecorder is supported.

These are simulated trajectories and uncalibrated outcomes, not observed traffic
or a validated forecast. Input schedule: 2 Sep 2026. Seed 17 in replays;
reported metrics aggregate seeds 17,42,73. Unserved demand remains explicit.
Vehicle symbols are enlarged and motion interpolates four-second samples.

OSM (c) OpenStreetMap contributors, ODbL. Municipal GIS/STCP catalogue: CC0.
Source URLs/hashes in sources.json. Detailed model limitations in findings.md.
