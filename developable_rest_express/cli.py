from __future__ import annotations

import argparse
from pathlib import Path

from .analysis import analyze_profile
from .benchmark_loader import load_benchmark
from .evaluation import evaluate_benchmark, export_calibration_rows
from .models import ConventionEvidence, DetectorMetrics, OutputFormat
from .profile_loader import load_profile
from .reporting import (
    render_analysis_json,
    render_analysis_markdown,
    render_evaluation_json,
    render_evaluation_markdown,
    render_output_bundle,
)
from .scoring import assess_convention
from .workspace import DEFAULT_CACHE_ROOT, prepare_benchmark, prepare_profile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="developable-rest-express")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_profile = subparsers.add_parser(
        "validate-profile",
        help="Validate a convention profile YAML file.",
    )
    validate_profile.add_argument("path", type=Path)

    prepare_profile_parser = subparsers.add_parser(
        "prepare-profile",
        help="Prepare local and GitHub-backed repos for a convention profile.",
    )
    prepare_profile_parser.add_argument("path", type=Path)
    prepare_profile_parser.add_argument("--cache-root", type=Path, default=None)

    prepare_benchmark_parser = subparsers.add_parser(
        "prepare-benchmark",
        help="Prepare and verify the pinned repos for a benchmark fixture.",
    )
    prepare_benchmark_parser.add_argument("path", type=Path)
    prepare_benchmark_parser.add_argument("--cache-root", type=Path, default=None)

    analyze_profile_parser = subparsers.add_parser(
        "analyze-profile",
        help="Prepare and analyze repos for a convention profile.",
    )
    analyze_profile_parser.add_argument("path", type=Path)
    analyze_profile_parser.add_argument("--cache-root", type=Path, default=None)
    analyze_profile_parser.add_argument("--output", choices=["json", "md", "both"], default="both")

    evaluate_parser = subparsers.add_parser(
        "evaluate-benchmark",
        help="Evaluate benchmark expectations against analyzed repos.",
    )
    evaluate_parser.add_argument("path", type=Path)
    evaluate_parser.add_argument("--cache-root", type=Path, default=None)
    evaluate_parser.add_argument("--output", choices=["json", "md", "both"], default="both")

    calibration_parser = subparsers.add_parser("export-calibration-dataset", help="Export JSONL rows for scorer calibration.")
    calibration_parser.add_argument("path", type=Path)
    calibration_parser.add_argument("--cache-root", type=Path, default=None)
    calibration_parser.add_argument("--output-path", type=Path, required=True)

    subparsers.add_parser(
        "score-demo",
        help="Run a small built-in scoring example.",
    )

    return parser


def run_validate_profile(path: Path) -> int:
    profile = load_profile(path)
    print(profile.model_dump_json(indent=2))
    return 0


def run_prepare_profile(path: Path, cache_root: Path | None) -> int:
    profile = load_profile(path)
    prepared = prepare_profile(profile, path, cache_root=cache_root)
    payload = {
        "profile_id": profile.profile_id,
        "cache_root": str(cache_root or path.parent / DEFAULT_CACHE_ROOT),
        "repos": [repo.model_dump() for repo in prepared],
    }
    import json

    print(json.dumps(payload, indent=2))
    return 0


def run_prepare_benchmark(path: Path, cache_root: Path | None) -> int:
    benchmark = load_benchmark(path)
    prepared = prepare_benchmark(benchmark, path, cache_root=cache_root)
    payload = {
        "benchmark_id": benchmark.benchmark_id,
        "cache_root": str(cache_root or path.parent / DEFAULT_CACHE_ROOT),
        "review": benchmark.review.model_dump(mode="json"),
        "repos": [repo.model_dump() for repo in prepared],
    }
    import json

    print(json.dumps(payload, indent=2))
    return 0


def run_analyze_profile(path: Path, cache_root: Path | None, output: OutputFormat) -> int:
    profile = load_profile(path)
    report = analyze_profile(profile, path, cache_root=cache_root)
    json_payload = render_analysis_json(report)
    markdown_payload = render_analysis_markdown(report)
    print(render_output_bundle(json_payload, markdown_payload, output))
    return 0


def run_evaluate_benchmark(path: Path, cache_root: Path | None, output: OutputFormat) -> int:
    benchmark = load_benchmark(path)
    result = evaluate_benchmark(benchmark, path, cache_root=cache_root)
    json_payload = render_evaluation_json(result)
    markdown_payload = render_evaluation_markdown(result)
    print(render_output_bundle(json_payload, markdown_payload, output))
    return 0


def run_export_calibration_dataset(path: Path, cache_root: Path | None, output_path: Path) -> int:
    import json

    rows = export_calibration_rows(load_benchmark(path), path, cache_root=cache_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    print(json.dumps({"rows": len(rows), "output_path": str(output_path)}))
    return 0


def run_score_demo() -> int:
    evidence = ConventionEvidence(
        convention_name="service_repository_layering",
        inferred_value="controller_service_repository",
        source_type="deterministic",
        agreement=0.92,
        repo_quality=0.88,
        coverage=1.0,
        conflict_penalty=0.03,
        detector_metrics=DetectorMetrics(
            parser_match_rate=0.95,
            structural_match_rate=0.91,
            independent_detector_agreement=0.89,
            test_evidence_rate=0.75,
            ambiguity_rate=0.08,
        ),
        evidence=[
            "5/5 repos expose separate controller and service layers.",
            "92% of route files call controllers instead of repositories directly.",
            "4/5 repos contain controller tests mocking services.",
        ],
        affected_repos=[
            "reference-api-one",
            "reference-api-two",
            "reference-api-three",
            "context-api-one",
            "evaluation-api-one",
        ],
        conflicts=["One repo uses a combined handlers/ directory for admin routes."],
    )
    assessment = assess_convention(evidence)
    print(assessment.model_dump_json(indent=2))
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "validate-profile":
        return run_validate_profile(args.path)
    if args.command == "prepare-profile":
        return run_prepare_profile(args.path, args.cache_root)
    if args.command == "prepare-benchmark":
        return run_prepare_benchmark(args.path, args.cache_root)
    if args.command == "analyze-profile":
        return run_analyze_profile(args.path, args.cache_root, args.output)
    if args.command == "evaluate-benchmark":
        return run_evaluate_benchmark(args.path, args.cache_root, args.output)
    if args.command == "export-calibration-dataset":
        return run_export_calibration_dataset(args.path, args.cache_root, args.output_path)
    if args.command == "score-demo":
        return run_score_demo()

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
