from __future__ import annotations

from pathlib import Path

from .adapters.express import analyze_express_repo
from .models import BenchmarkFixture, ComparisonResult, EvaluationResult
from .workspace import prepare_benchmark


def evaluate_benchmark(
    fixture: BenchmarkFixture,
    fixture_path: Path,
    cache_root: Path | None = None,
) -> EvaluationResult:
    repo_handles = prepare_benchmark(fixture, fixture_path, cache_root=cache_root)
    comparisons: list[ComparisonResult] = []

    for repo in repo_handles:
        expected = fixture.expected_conventions[repo.repo_id]
        analyses = analyze_express_repo(repo) if repo.framework == "express" else []
        by_name = {item.convention_name: item for item in analyses}

        for convention_name in expected.model_dump().keys():
            if convention_name in by_name:
                assessment = by_name[convention_name]
                inferred_value = assessment.inferred_value
                confidence = assessment.confidence
                bucket = assessment.bucket
                supported = assessment.supported
                ambiguous = assessment.ambiguous
            else:
                inferred_value = "unsupported"
                confidence = 0.0
                bucket = "do_not_operationalize"
                supported = False
                ambiguous = True

            expected_value = getattr(expected, convention_name)
            comparisons.append(
                ComparisonResult(
                    repo_id=repo.repo_id,
                    convention_name=convention_name,
                    expected_value=expected_value,
                    inferred_value=inferred_value,
                    matched=inferred_value == expected_value,
                    confidence=confidence,
                    bucket=bucket,
                    supported=supported,
                    ambiguous=ambiguous,
                )
            )

    by_convention: dict[str, list[ComparisonResult]] = {}
    by_bucket: dict[str, list[ComparisonResult]] = {}
    for comparison in comparisons:
        by_convention.setdefault(comparison.convention_name, []).append(comparison)
        by_bucket.setdefault(comparison.bucket, []).append(comparison)

    exact_match_accuracy_by_convention = {
        name: round(sum(item.matched for item in items) / len(items), 4)
        for name, items in by_convention.items()
    }
    precision_by_confidence_bucket = {
        name: round(sum(item.matched for item in items) / len(items), 4)
        for name, items in by_bucket.items()
    }

    false_positives = [
        item
        for item in comparisons
        if not item.matched and item.supported and item.expected_value != "unsupported"
    ]
    false_negatives = [
        item
        for item in comparisons
        if not item.matched and not item.supported and item.expected_value != "unsupported"
    ]
    ambiguous_repo_count = len(
        {
            item.repo_id
            for item in comparisons
            if item.ambiguous
        }
    )
    unsupported_convention_count = sum(not item.supported for item in comparisons)

    return EvaluationResult(
        benchmark_id=fixture.benchmark_id,
        library=fixture.library,
        framework_scope=fixture.framework_scope,
        review=fixture.review,
        repos=repo_handles,
        comparisons=comparisons,
        total_conventions_evaluated=len(comparisons),
        exact_match_accuracy_by_convention=exact_match_accuracy_by_convention,
        precision_by_confidence_bucket=precision_by_confidence_bucket,
        ambiguous_repo_count=ambiguous_repo_count,
        unsupported_convention_count=unsupported_convention_count,
        false_positives=false_positives,
        false_negatives=false_negatives,
        notes=["Evaluation is based on heuristic confidence, pending calibration."],
    )
