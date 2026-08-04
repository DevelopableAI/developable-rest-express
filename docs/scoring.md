# Scoring

## What scoring means

A confidence score is a prediction that an inferred convention is correct and safe enough to use at a given automation level.

That means two properties matter:

- ranking: more trustworthy conventions should score higher than weaker ones
- calibration: a score like `0.87` should correspond to real-world correctness at roughly that level after evaluation

## Signal strength

`signal_strength` is not the final confidence.

It measures the clarity and abundance of evidence supporting a proposed convention inside the analyzed repos.

Current heuristic components:

- parser match rate
- structural match rate
- independent detector agreement
- test evidence rate
- inverse ambiguity rate

Current heuristic formula:

```text
signal_strength =
  0.30 * parser_match_rate +
  0.20 * structural_match_rate +
  0.20 * independent_detector_agreement +
  0.15 * test_evidence_rate +
  0.15 * (1 - ambiguity_rate)
```

## Confidence

Current heuristic confidence formula:

```text
confidence =
  agreement * 0.35 +
  signal_strength * 0.25 +
  repo_quality * 0.15 +
  coverage * 0.15 +
  determinism_bonus * 0.10 -
  conflict_penalty
```

This is a starting point only.

The current Express adapter supplies these features from structural code signals. `repo_quality` is currently `0.9` for Express TypeScript and `0.8` for Express JavaScript; per-repo coverage is currently `1.0`; deterministic detectors receive a `1.0` bonus; and a detected structural conflict incurs a `0.1` penalty.

`agreement` is currently a heuristic detector signal and contributes both directly and through `signal_strength`. This deliberate V1 shortcut means confidence is not yet a calibrated probability.

## Confidence buckets

Current buckets:

- `0.85 - 1.00`: high
- `0.65 - 0.84`: medium
- `0.40 - 0.64`: low
- `< 0.40`: do not operationalize

## How these numbers become defensible

The weights and thresholds should eventually be backed by benchmark data.

Recommended approach:

1. Build labeled convention-inference examples from real REST repo profiles.
2. Measure whether the heuristic score ranks correct inferences above incorrect ones.
3. Fit an interpretable model, likely logistic regression, on the feature set.
4. Calibrate the resulting probabilities on held-out data.
5. Set operational thresholds using observed precision rather than intuition.

## Benchmark Accuracy Is Separate

The benchmark report's exact-match accuracy is the fraction of manually labeled repository conventions whose inferred value matches the expected value. It evaluates detector correctness; it does not contribute to an individual assessment's confidence score during V1.

## Evaluation metrics to add later

- precision per convention type
- recall per convention type
- Brier score
- reliability diagrams / calibration curves
- thresholded precision for operational buckets
