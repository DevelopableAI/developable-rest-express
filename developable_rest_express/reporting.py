from __future__ import annotations

import json
from typing import Any

from .models import AnalysisReport, EvaluationResult


def render_analysis_json(report: AnalysisReport) -> str:
    return json.dumps(report.model_dump(mode="json"), indent=2)


def render_analysis_markdown(report: AnalysisReport) -> str:
    lines = [
        f"# Analysis Report: {report.profile_id}",
        "",
        f"- Library: `{report.library}`",
        f"- Total repos: `{report.summary.get('total_repos', 0)}`",
        f"- Unsupported repos: `{report.summary.get('unsupported_repos', 0)}`",
        "",
        "## Repo Summary",
        "",
        "| Repo | Role | Requested revision | Resolved revision | Framework | Language | Cache |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for repo in report.repos:
        lines.append(
            f"| `{repo.repo_id}` | `{repo.role}` | `{repo.requested_revision or '-'}` | `{repo.commit_sha or '-'}` | `{repo.framework or 'unknown'}` | `{repo.language or 'unknown'}` | `{repo.prepared_from_cache}` |"
        )

    for repo_report in report.repo_reports:
        lines.extend(
            [
                "",
                f"## Repo: {repo_report.repo.repo_id}",
                "",
                "| Convention | Inferred value | Confidence | Bucket | Supported | Ambiguous |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        if not repo_report.conventions:
            lines.append("| _none_ | unsupported | 0.0 | do_not_operationalize | no | yes |")
            continue
        for assessment in repo_report.conventions:
            lines.append(
                f"| `{assessment.convention_name}` | `{assessment.inferred_value}` | `{assessment.confidence}` | `{assessment.bucket}` | `{assessment.supported}` | `{assessment.ambiguous}` |"
            )
            for item in assessment.evidence:
                lines.append(f"- {item}")
            for item in assessment.conflicts:
                lines.append(f"- Conflict: {item}")
    return "\n".join(lines)


def render_evaluation_json(result: EvaluationResult) -> str:
    return json.dumps(result.model_dump(mode="json"), indent=2)


def render_evaluation_markdown(result: EvaluationResult) -> str:
    lines = [
        f"# Benchmark Evaluation: {result.benchmark_id}",
        "",
        f"- Library: `{result.library}`",
        f"- Framework scope: `{result.framework_scope}`",
        f"- Label author: `{result.review.author}`",
        f"- Label reviewer: `{result.review.reviewer}`",
        f"- Review mode: `{result.review.review_mode}`",
        f"- Reviewed at: `{result.review.reviewed_at.isoformat()}`",
        f"- Total conventions evaluated: `{result.total_conventions_evaluated}`",
        f"- Ambiguous repos: `{result.ambiguous_repo_count}`",
        f"- Unsupported conventions: `{result.unsupported_convention_count}`",
        "",
        "## Accuracy by Convention",
        "",
        "| Convention | Exact-match accuracy |",
        "| --- | --- |",
    ]
    for convention_name, score in result.exact_match_accuracy_by_convention.items():
        lines.append(f"| `{convention_name}` | `{score}` |")

    lines.extend(
        [
            "",
            "## Precision by Confidence Bucket",
            "",
            "| Bucket | Precision |",
            "| --- | --- |",
        ]
    )
    for bucket, score in result.precision_by_confidence_bucket.items():
        lines.append(f"| `{bucket}` | `{score}` |")

    lines.extend(
        [
            "",
            "## Repo Provenance",
            "",
            "| Repo | Source | Requested revision | Resolved revision | Cache reuse |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for repo in result.repos:
        lines.append(
            f"| `{repo.repo_id}` | `{repo.source}` | `{repo.requested_revision or '-'}` | `{repo.commit_sha or '-'}` | `{repo.prepared_from_cache}` |"
        )

    lines.extend(
        [
            "",
            "## Public Benchmark Summary Table",
            "",
            "| Repo | Convention | Expected | Inferred | Confidence | Bucket | Match |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in result.comparisons:
        lines.append(
            f"| `{item.repo_id}` | `{item.convention_name}` | `{item.expected_value}` | `{item.inferred_value}` | `{item.confidence}` | `{item.bucket}` | `{item.matched}` |"
        )

    lines.extend(["", "## Label Review", "", result.review.rationale])

    if result.false_positives:
        lines.extend(["", "## False Positives", ""])
        for item in result.false_positives:
            lines.append(
                f"- `{item.repo_id}` `{item.convention_name}` expected `{item.expected_value}` but inferred `{item.inferred_value}` at confidence `{item.confidence}`."
            )

    if result.false_negatives:
        lines.extend(["", "## False Negatives", ""])
        for item in result.false_negatives:
            lines.append(
                f"- `{item.repo_id}` `{item.convention_name}` expected `{item.expected_value}` but the analyzer returned `{item.inferred_value}`."
            )

    return "\n".join(lines)


def render_output_bundle(json_payload: str, markdown_payload: str, output_format: str) -> str:
    if output_format == "json":
        return json_payload
    if output_format == "md":
        return markdown_payload
    bundle: dict[str, Any] = {
        "json_report": json.loads(json_payload),
        "markdown_report": markdown_payload,
    }
    return json.dumps(bundle, indent=2)
