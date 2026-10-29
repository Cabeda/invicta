# Add a simulated line

The public page and both renderers are shared. Line-specific acquisition, timetable matching and native study preparation remain adapters; another line needs real prepared data rather than a copied demonstration.

1. Prepare a native study with explicit directions, scheduled trips including short services, matched road geometry, source hashes, baseline and candidate demand cases. Publish the current data contract (`meta.route`, `native_directions`, `replay_manifest`, `replay_assets`, geometry, colors and sources). Keep relative asset URLs valid from the public site root.
2. Put the study's public files in `prototypes/costa-cabral/proposal/lines/<line-id>/`, using names and namespaces distinct from existing studies. Prepared native scene/captures use the same `invicta.native-replay.v1` contract. Both directions use the same scene origin.
3. Create a registration JSON following an entry in `web/lines.json`: unique ID, operator, PT/EN name and description, root-relative data/reference/report paths, official source URL, study-specific evidence download paths, localized case labels/policy description and optional service-model capability. Runtime coverage, observation dates, sampling and dwell descriptions derive from the selected study; they are not copied from 701. Only the current 701 adapter supplies the separate passenger/berth analysis; use `serviceModel:false` for another line until its own operational model is provided.
4. Run `node scripts/register-line.mjs /absolute/path/registration.json`. It rejects duplicate identities and mismatched prepared data. The build copies the validated registry; the page selector and share links use the line ID.
5. Run `npm run build`, `npm run prepare:deploy`, `npm run check` and `npm run test:browser`. Review sources, access assumptions, failure cases and bilingual explanations before pushing and deploying.

The minimum-change decision ranks only fully tested packages meeting the declared punctuality and access constraints. It does not promise a global optimum or execute SUMO inside a visitor's browser. Additional packages must be natively run and bound to their own demand/source evidence before inclusion. Costs need measured quantities and local rates.

The current published static files retain their historical directory for URL and dataset compatibility. New application/domain modules live in `web/`; `docs/ARCHITECTURE.md` describes the remaining adapter boundaries.
