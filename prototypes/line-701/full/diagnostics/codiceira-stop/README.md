# Codiceira: direct route and internal stop diagnostic

The frozen STCP shape and OSM relation support the direct outbound turn. This controlled two-bus fixture uses the V17 native network, unchanged 12 m bus physics and a strict internal busStop interval projected near COD3. It tests passage, a 20-second stop, completion and native conflicts. Five controlled arrival offsets pass; they are not regional arrivals or a paired street-policy benefit.

The platform/official pins do not specify a bus-front or door alignment. This anchor remains a diagnostic assumption. Full stop/path representation, continuous footprint/conflict checks, passenger access and unchanged full-service qualification remain required. The production model/audit is not bypassed or changed.

The frozen archive is `docs/research/701-codiceira-direct-route-2026-10-31/study.json`. Its V17 network descriptor restores the exact bytes. The initial omitted intermediate road failed native route validation and remains in that archive. See `docs/research/701-codiceira-berth-sources-2026-10-31.md` for source identities and limits.
