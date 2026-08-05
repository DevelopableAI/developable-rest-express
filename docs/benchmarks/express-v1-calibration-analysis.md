# Express V1 calibration analysis

This exploratory analysis uses the 96 rows in `benchmarks/public/calibration/express_v1.jsonl`. It evaluates the current heuristic confidence; it does not train a model.

## Overall result

- Brier score: `0.1240` (lower is better).
- The high-confidence bucket is conservative: mean predicted confidence `0.8779`, observed precision `0.9706` across 34 rows.
- The medium bucket is comparatively well aligned: `0.7974` predicted vs `0.8182` observed across 44 rows.
- The low bucket is overconfident: `0.5772` predicted vs `0.6111` observed across 18 rows. Its small sample size means it should remain explain-only.

## By convention

| Convention | Rows | Exact-match accuracy | Mean confidence | Interpretation |
| --- | ---: | ---: | ---: | --- |
| auth_middleware_presence | 16 | 1.0000 | 0.8316 | Strong but still narrow corpus coverage. |
| service_repository_layering | 16 | 0.8750 | 0.7704 | Promising after detector improvements. |
| test_layout_shape | 16 | 0.8750 | 0.7512 | Promising; add further framework diversity. |
| route_controller_boundary | 16 | 0.8125 | 0.7572 | Needs more non-controller route styles. |
| validation_at_edge_pattern | 16 | 0.7500 | 0.7897 | Overconfident; prioritize varied validation libraries. |
| route_declaration_style | 16 | 0.6875 | 0.8075 | Most overconfident convention; prioritize alternate routing abstractions. |

## Feature separation

Correct inferences have higher mean parser match (`0.3338` vs `0.1837`), structural match (`0.6550` vs `0.3911`), agreement (`0.7943` vs `0.6450`), and signal strength (`0.5910` vs `0.4135`). Incorrect inferences have materially higher ambiguity (`0.5938` vs `0.2176`).

`test_evidence_rate` does not separate correct from incorrect rows (`0.5576` correct vs `0.6017` incorrect), so it should be scrutinized before it receives a learned weight.

## Decision

Do not fit a production scorer yet. The dataset has only 16 examples per convention and includes recent label corrections. Expand to at least 200–300 reviewed rows, with emphasis on route declaration and validation diversity, then use a repository-family holdout split for an interpretable logistic-regression and probability-calibration experiment.
