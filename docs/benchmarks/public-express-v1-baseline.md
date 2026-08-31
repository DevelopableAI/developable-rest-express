# Public Express V1 baseline

> **Superseded by [the V2 baseline](public-express-v2-baseline.md)** (run 33436574252,
> 63 repositories, 378 conventions). This document records the 6-repository state as of
> 2026-08-04 and is kept as an immutable historical comparator. Do not cite its accuracy
> figures as current.

The committed V1 baseline is the successful manually dispatched [Public Benchmark workflow run](https://github.com/DevelopableAI/developable-rest-express/actions/runs/30935152752) on `2026-08-04`, for commit `a14d9094b66c7437e6f7cd0bb5dc811017df95de`.

The uploaded `public-express-benchmark` artifact contains the authoritative JSON and Markdown reports. Its exact-match accuracies were:

| Convention | Accuracy |
| --- | --- |
| route_declaration_style | 0.3333 |
| route_controller_boundary | 0.8333 |
| validation_at_edge_pattern | 0.6667 |
| service_repository_layering | 0.1667 |
| auth_middleware_presence | 1.0000 |
| test_layout_shape | 0.6667 |

The report evaluated all 36 labeled conventions against the six SHA-pinned public repositories. It is the comparator for subsequent detector milestones; no MCP or skill emission is authorized until benchmark confidence is consistently useful.
