from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


FEATURE_NAMES = (
    "confidence",
    "parser_match_rate",
    "structural_match_rate",
    "independent_detector_agreement",
    "test_evidence_rate",
    "ambiguity_rate",
    "signal_strength",
)


def load_calibration_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def run_repository_grouped_logistic_experiment(
    rows: Iterable[dict[str, Any]],
    *,
    l2_penalty: float = 1.0,
    iterations: int = 1_500,
    learning_rate: float = 0.08,
) -> dict[str, Any]:
    """Evaluate a regularized correctness calibrator without leaking repositories.

    This is deliberately a feasibility experiment, not an operational scorer. Each
    repository is held out in turn; the model sees no rows from that repository
    while making its six predictions.
    """

    items = list(rows)
    if not items:
        raise ValueError("calibration dataset is empty")
    missing = [name for name in FEATURE_NAMES if any(name not in item for item in items)]
    if missing:
        raise ValueError(f"calibration dataset is missing features: {', '.join(missing)}")
    if any("repo_id" not in item or "matched" not in item for item in items):
        raise ValueError("calibration dataset requires repo_id and matched fields")

    groups: dict[str, list[int]] = defaultdict(list)
    for index, item in enumerate(items):
        groups[str(item["repo_id"])].append(index)
    if len(groups) < 3:
        raise ValueError("at least three repositories are required for grouped evaluation")

    predictions: list[float | None] = [None] * len(items)
    for held_out in groups:
        train_indices = [index for repo_id, indices in groups.items() if repo_id != held_out for index in indices]
        test_indices = groups[held_out]
        x_train = [_features(items[index]) for index in train_indices]
        y_train = [1.0 if items[index]["matched"] else 0.0 for index in train_indices]
        means, scales = _standardize_fit(x_train)
        weights, intercept = _fit_regularized_logistic(
            [_standardize(row, means, scales) for row in x_train],
            y_train,
            l2_penalty=l2_penalty,
            iterations=iterations,
            learning_rate=learning_rate,
        )
        for index in test_indices:
            predictions[index] = _sigmoid(intercept + sum(weight * feature for weight, feature in zip(weights, _standardize(_features(items[index]), means, scales))))

    model_predictions = [float(value) for value in predictions if value is not None]
    targets = [1.0 if item["matched"] else 0.0 for item in items]
    heuristic_predictions = [float(item["confidence"]) for item in items]
    return {
        "experiment": "repository_grouped_regularized_logistic_correctness_calibration",
        "operational": False,
        "row_count": len(items),
        "repository_count": len(groups),
        "feature_names": list(FEATURE_NAMES),
        "validation": "leave-one-repository-out",
        "l2_penalty": l2_penalty,
        "heuristic_brier_score": round(_brier(heuristic_predictions, targets), 4),
        "logistic_brier_score": round(_brier(model_predictions, targets), 4),
        "heuristic_reliability": _reliability(heuristic_predictions, targets),
        "logistic_reliability": _reliability(model_predictions, targets),
        "recommendation": _recommendation(_brier(heuristic_predictions, targets), _brier(model_predictions, targets), len(items)),
    }


def render_calibration_experiment_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Repository-grouped logistic calibration feasibility experiment",
        "",
        "This is an exploratory correctness-calibration experiment. It does not replace deterministic convention inference.",
        "",
        f"- Rows: `{result['row_count']}`",
        f"- Repositories: `{result['repository_count']}`",
        f"- Validation: `{result['validation']}`",
        f"- Features: `{', '.join(result['feature_names'])}`",
        f"- Heuristic Brier score: `{result['heuristic_brier_score']}`",
        f"- Logistic Brier score: `{result['logistic_brier_score']}`",
        "",
        "## Reliability",
        "",
        "| Model | Probability band | Rows | Mean prediction | Observed correctness |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for model_name, rows in (("heuristic", result["heuristic_reliability"]), ("logistic", result["logistic_reliability"])):
        for row in rows:
            lines.append(
                f"| `{model_name}` | `{row['band']}` | `{row['count']}` | `{row['mean_prediction']}` | `{row['observed_correctness']}` |"
            )
    lines.extend(["", "## Recommendation", "", str(result["recommendation"])])
    return "\n".join(lines)


def _features(item: dict[str, Any]) -> list[float]:
    return [float(item[name]) for name in FEATURE_NAMES]


def _standardize_fit(rows: list[list[float]]) -> tuple[list[float], list[float]]:
    means = [sum(row[column] for row in rows) / len(rows) for column in range(len(FEATURE_NAMES))]
    scales = [
        max(math.sqrt(sum((row[column] - means[column]) ** 2 for row in rows) / len(rows)), 0.05)
        for column in range(len(FEATURE_NAMES))
    ]
    return means, scales


def _standardize(row: list[float], means: list[float], scales: list[float]) -> list[float]:
    return [(value - mean) / scale for value, mean, scale in zip(row, means, scales)]


def _fit_regularized_logistic(
    rows: list[list[float]],
    targets: list[float],
    *,
    l2_penalty: float,
    iterations: int,
    learning_rate: float,
) -> tuple[list[float], float]:
    weights = [0.0] * len(FEATURE_NAMES)
    positive_rate = min(max(sum(targets) / len(targets), 0.01), 0.99)
    intercept = math.log(positive_rate / (1.0 - positive_rate))
    for _ in range(iterations):
        errors = [_sigmoid(intercept + sum(weight * feature for weight, feature in zip(weights, row))) - target for row, target in zip(rows, targets)]
        intercept -= learning_rate * sum(errors) / len(rows)
        for column in range(len(weights)):
            gradient = sum(error * row[column] for error, row in zip(errors, rows)) / len(rows) + l2_penalty * weights[column] / len(rows)
            weights[column] -= learning_rate * gradient
    return weights, intercept


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(min(value, 30.0), -30.0)))


def _brier(predictions: list[float], targets: list[float]) -> float:
    return sum((prediction - target) ** 2 for prediction, target in zip(predictions, targets)) / len(targets)


def _reliability(predictions: list[float], targets: list[float]) -> list[dict[str, float | int | str]]:
    bands = ((0.0, 0.6), (0.6, 0.8), (0.8, 1.01))
    results: list[dict[str, float | int | str]] = []
    for lower, upper in bands:
        indices = [index for index, value in enumerate(predictions) if lower <= value < upper]
        if not indices:
            continue
        results.append(
            {
                "band": f"{lower:.1f}-{min(upper, 1.0):.1f}",
                "count": len(indices),
                "mean_prediction": round(sum(predictions[index] for index in indices) / len(indices), 4),
                "observed_correctness": round(sum(targets[index] for index in indices) / len(indices), 4),
            }
        )
    return results


def _recommendation(heuristic_brier: float, logistic_brier: float, row_count: int) -> str:
    if logistic_brier < heuristic_brier and row_count >= 200:
        return "Promising but still experimental: rerun after each reviewed corpus expansion; do not operationalize without stable grouped-holdout gains."
    if logistic_brier < heuristic_brier:
        return "The grouped experiment improves Brier score, but the corpus is still too small to operationalize; retain the heuristic and collect more reviewed repositories."
    return "The grouped experiment does not improve Brier score; retain the heuristic and use the failure patterns to guide detector and corpus work."
