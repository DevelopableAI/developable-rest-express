# Repository-grouped logistic calibration feasibility experiment

This is an exploratory math-based ML experiment, not a replacement for deterministic convention inference. It predicts whether a detector result is correct from exported evidence metrics, and holds out every row from one repository at a time.

## Configuration

- Corpus: 204 manually reviewed convention rows from 34 SHA-pinned repositories.
- Target: `matched` (whether detector output equals the human-reviewed label).
- Features: heuristic confidence, parser match, structural match, independent detector agreement, test evidence, ambiguity, and signal strength.
- Validation: leave-one-repository-out; no rows from the held-out repository enter training.
- Model: L2-regularized logistic regression (`l2_penalty=1.0`), implemented without external ML dependencies.
- Status: non-operational. The model does not infer convention labels and is not used to change product confidence.

## Out-of-fold results

| Measure | Heuristic | Logistic calibrator |
| --- | ---: | ---: |
| Brier score | 0.1479 | 0.1292 |

| Model | Probability band | Rows | Mean prediction | Observed correctness |
| --- | --- | ---: | ---: | ---: |
| Heuristic | 0.0–0.6 | 30 | 0.5565 | 0.7333 |
| Heuristic | 0.6–0.8 | 49 | 0.6947 | 0.4898 |
| Heuristic | 0.8–1.0 | 125 | 0.8583 | 0.9120 |
| Logistic | 0.0–0.6 | 43 | 0.4385 | 0.4419 |
| Logistic | 0.6–0.8 | 12 | 0.7324 | 0.7500 |
| Logistic | 0.8–1.0 | 149 | 0.8885 | 0.8859 |

The reduction in Brier score is promising, and the logistic reliability bands are better aligned. It is not enough to operationalize: the corpus contains only 44 mismatches, examples within a repository are correlated, and architecture classes remain imbalanced. The command is available for repeatable reassessment:

```bash
developable-rest-express run-calibration-experiment benchmarks/public/calibration/express_v1.jsonl --output md
```

Keep the deterministic confidence as the product output until several successive, repository-grouped expansions preserve or improve this result.
