# Express V1 calibration analysis

This exploratory analysis uses the 156 rows in `benchmarks/public/calibration/express_v1.jsonl`, after the reviewed 10-repository Batch 02 expansion. It evaluates the current heuristic confidence; it does not train a model.

## Overall result

- Brier score: `0.1384` (lower is better). The increase is expected: Batch 02 intentionally adds direct-data-access and handler patterns that the detector does not yet recognize.
- The high-confidence bucket remains conservative: mean predicted confidence `0.8765`, observed precision `0.9600` across 50 rows.
- The medium bucket is comparatively well aligned: `0.7993` predicted vs `0.8235` observed across 68 rows.
- The low bucket is slightly overconfident: `0.5814` predicted vs `0.5526` observed across 38 rows. It should remain explain-only.

## By convention

| Convention | Rows | Exact-match accuracy | Mean confidence | Interpretation |
| --- | ---: | ---: | ---: | --- |
| auth_middleware_presence | 26 | 0.9231 | 0.8299 | Strong, but helper-based versus route-wired auth needs a detector distinction. |
| service_repository_layering | 26 | 0.6923 | 0.7457 | Primary gap: direct repositories, direct ORM clients, and flat handlers are under-recognized. |
| test_layout_shape | 26 | 0.9231 | 0.7253 | Strong across Jest/Supertest, Vitest, Mocha/Chai, and no-test cases. |
| route_controller_boundary | 26 | 0.7308 | 0.7475 | Needs handlers and direct data-access route boundaries. |
| validation_at_edge_pattern | 26 | 0.7692 | 0.7622 | Better diversified; handler/controller-side Zod remains a gap. |
| route_declaration_style | 26 | 0.7692 | 0.8151 | Still overconfident for mixed and feature routing, despite stronger coverage. |

## Feature separation

Correct inferences have higher mean parser match (`0.3464` vs `0.1554`), structural match (`0.6043` vs `0.4111`), agreement (`0.7834` vs `0.6235`), and signal strength (`0.5708` vs `0.3697`). Incorrect inferences have materially higher ambiguity (`0.6365` vs `0.2415`).

`test_evidence_rate` now has modest separation (`0.5037` correct vs `0.4105` incorrect), but this is not enough evidence to weight it in a learned scorer.

## Decision

Do not fit a production scorer yet. The dataset now has 26 examples per convention, but the target remains 200–300 reviewed rows and the Batch 02 gaps are clustered by architecture family. Add at least eight more diverse repositories before an interpretable logistic-regression and probability-calibration experiment, using a repository-family holdout split.
