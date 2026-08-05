# Express V1 calibration analysis

This exploratory analysis uses the 204 rows in `benchmarks/public/calibration/express_v1.jsonl`, after the reviewed Batch 03 expansion. It evaluates the current heuristic confidence; the separate logistic experiment remains non-operational.

## Overall result

- Brier score: `0.1479` (lower is better). The increase is expected: Batch 03 adds clean-architecture, request-handler, direct SQL, and feature-module patterns that the detector does not yet recognize consistently.
- The high-confidence bucket remains useful: mean predicted confidence `0.8793`, observed precision `0.9429` across 70 rows.
- The medium bucket is well aligned: `0.7991` predicted vs `0.8000` observed across 85 rows.
- The low bucket is overconfident: `0.5827` predicted vs `0.5306` observed across 49 rows. It remains explain-only.

## By convention

| Convention | Rows | Exact-match accuracy | Mean confidence | Interpretation |
| --- | ---: | ---: | ---: | --- |
| auth_middleware_presence | 34 | 0.9412 | 0.8422 | Strong, but helper-based versus route-wired auth needs a detector distinction. |
| service_repository_layering | 34 | 0.6471 | 0.7412 | Primary gap: clean/request-handler architecture and direct ORM data access remain under-recognized. |
| test_layout_shape | 34 | 0.9412 | 0.7342 | Strong across Jest/Supertest, Vitest, Mocha/Chai, and no-test cases. |
| route_controller_boundary | 34 | 0.7059 | 0.7454 | Needs handlers and direct data-access route boundaries. |
| validation_at_edge_pattern | 34 | 0.7353 | 0.7689 | Handler/controller-side Zod and no-clear validation remain a gap. |
| route_declaration_style | 34 | 0.7353 | 0.8160 | Still overconfident for mixed, feature, and class-based routing. |

## Feature separation

Correct inferences have higher mean parser match (`0.3799` vs `0.1452`), structural match (`0.6116` vs `0.4459`), agreement (`0.7890` vs `0.6443`), and signal strength (`0.5846` vs `0.3933`). Incorrect inferences have materially higher ambiguity (`0.5495` vs `0.2337`).

`test_evidence_rate` has modest separation (`0.5034` correct vs `0.4277` incorrect), but this is not enough evidence to weight it in a learned scorer.

## Decision

The 204-row threshold is now met. The [repository-grouped logistic experiment](express-v1-logistic-calibration-experiment.md) improves Brier score out of fold, but it has only 44 mismatch examples and is not operational. Retain the heuristic, rerun the experiment after each corpus expansion, and require stable grouped-holdout gains over several expansions before considering calibrated confidence in product output.
