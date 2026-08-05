from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock
import subprocess

from pydantic import ValidationError

from developable_rest_express.analysis import analyze_profile
from developable_rest_express.adapters.express import analyze_express_repo
from developable_rest_express.benchmark_loader import load_benchmark
from developable_rest_express.calibration import run_repository_grouped_logistic_experiment
from developable_rest_express.evaluation import evaluate_benchmark
from developable_rest_express.governance import load_governance, validate_benchmark_review
from developable_rest_express.models import BenchmarkFixture, BenchmarkReview, RepoHandle, RepoReference
from developable_rest_express.profile_loader import load_profile
from developable_rest_express.reporting import (
    render_analysis_json,
    render_analysis_markdown,
    render_evaluation_json,
    render_evaluation_markdown,
)
from developable_rest_express.workspace import RepoPreparationError, prepare_benchmark, prepare_profile


FIXTURES_ROOT = Path(__file__).parent / "fixtures"


class DevelopableRestExpressTests(unittest.TestCase):
    def test_valid_profile_with_mixed_local_and_github_inputs(self) -> None:
        profile = load_profile(FIXTURES_ROOT / "profiles" / "mixed_profile.yaml")
        self.assertEqual(profile.reference_repos[0].source_kind, "local_path")
        self.assertEqual(profile.reference_repos[1].source_kind, "github_url")
        self.assertEqual(profile.expected_framework, "express")

    def test_invalid_profile_duplicate_repo_id(self) -> None:
        duplicate_profile = """
profile_id: duplicate
library: developable-rest-express
purpose: bad fixture
reference_repos:
  - repo_id: dup
    source: ./one
  - repo_id: dup
    source: ./two
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "duplicate.yaml"
            path.write_text(duplicate_profile)
            with self.assertRaises(ValidationError):
                load_profile(path)

    def test_invalid_benchmark_fixture_labels(self) -> None:
        invalid_benchmark = """
benchmark_id: bad
library: developable-rest-express
framework_scope: express
repos:
  - repo_id: one
    source: ../repos/express_layered
expected_conventions: {}
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "benchmark.yaml"
            path.write_text(invalid_benchmark)
            with self.assertRaises(ValidationError):
                load_benchmark(path)

    def test_github_benchmark_requires_a_full_revision(self) -> None:
        invalid_benchmark = """
benchmark_id: missing-revision
library: developable-rest-express
framework_scope: express
review:
  author: author
  reviewer: reviewer
  review_mode: peer_review
  reviewed_at: 2026-08-04
  rationale: Test fixture.
repos:
  - repo_id: public-repo
    source: https://github.com/example/public-repo.git
expected_conventions:
  public-repo:
    route_declaration_style: express_router_modules
    route_controller_boundary: routes_call_controllers
    validation_at_edge_pattern: no_clear_validation
    service_repository_layering: layering_unclear
    auth_middleware_presence: auth_middleware_unclear
    test_layout_shape: no_clear_tests
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "benchmark.yaml"
            path.write_text(invalid_benchmark)
            with self.assertRaises(ValidationError):
                load_benchmark(path)

    def test_prepare_profile_local_paths(self) -> None:
        profile_path = FIXTURES_ROOT / "profiles" / "local_profile.yaml"
        profile = load_profile(profile_path)
        with tempfile.TemporaryDirectory() as tmp_dir:
            prepared = prepare_profile(profile, profile_path, cache_root=Path(tmp_dir) / "cache")
            self.assertEqual(len(prepared), 3)
            self.assertTrue(all(repo.local_path for repo in prepared))
            self.assertTrue(all(repo.source_kind == "local_path" for repo in prepared))

    def test_prepare_profile_mixed_with_cache_reuse(self) -> None:
        profile_path = FIXTURES_ROOT / "profiles" / "mixed_profile.yaml"
        profile = load_profile(profile_path)

        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_root = Path(tmp_dir) / "cache"

            def fake_run_git(command: list[str], action: str) -> str:
                if "clone" in command:
                    destination = Path(command[-1])
                    destination.mkdir(parents=True, exist_ok=True)
                    (destination / ".git").mkdir(parents=True, exist_ok=True)
                    (destination / "package.json").write_text('{"dependencies":{"express":"^4.0.0"}}')
                    (destination / "src").mkdir(exist_ok=True)
                    (destination / "src" / "app.js").write_text("const express = require('express');")
                    return ""
                if "config" in command:
                    return "https://github.com/example/remote-express-service.git"
                if "rev-parse" in command:
                    return "deadbeef"
                raise AssertionError(f"Unexpected git command: {command}")

            with mock.patch("developable_rest_express.workspace._run_git", side_effect=fake_run_git):
                first = prepare_profile(profile, profile_path, cache_root=cache_root)
            self.assertEqual(len(first), 3)
            remote_first = next(repo for repo in first if repo.repo_id == "remote-express")
            self.assertFalse(remote_first.prepared_from_cache)

            def fake_run_git_cached(command: list[str], action: str) -> str:
                if "clone" in command:
                    raise AssertionError("should not reclone")
                if "config" in command:
                    return "https://github.com/example/remote-express-service.git"
                if "rev-parse" in command:
                    return "deadbeef"
                raise AssertionError(f"Unexpected git command: {command}")

            with mock.patch("developable_rest_express.workspace._run_git", side_effect=fake_run_git_cached):
                second = prepare_profile(profile, profile_path, cache_root=cache_root)
            remote_second = next(repo for repo in second if repo.repo_id == "remote-express")
            self.assertTrue(remote_second.prepared_from_cache)

    def test_invalid_github_url_handling(self) -> None:
        invalid_profile = """
profile_id: invalid-remote
library: developable-rest-express
purpose: invalid remote source
reference_repos:
  - source: https://gitlab.com/example/repo
  - source: ./relative/local
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "relative" / "local").mkdir(parents=True)
            ((root / "relative" / "local") / "package.json").write_text('{"dependencies":{"express":"^4.0.0"}}')
            path = root / "profile.yaml"
            path.write_text(invalid_profile)
            profile = load_profile(path)
            with self.assertRaises(RepoPreparationError):
                prepare_profile(profile, path, cache_root=root / "cache")

    def test_unreachable_repo_reports_clear_error(self) -> None:
        profile_path = FIXTURES_ROOT / "profiles" / "mixed_profile.yaml"
        profile = load_profile(profile_path)
        with tempfile.TemporaryDirectory() as tmp_dir:
            with mock.patch(
                "developable_rest_express.workspace._run_git",
                side_effect=RepoPreparationError("Failed to clone repo from https://github.com/example/remote-express-service: timeout"),
            ):
                with self.assertRaises(RepoPreparationError) as ctx:
                    prepare_profile(profile, profile_path, cache_root=Path(tmp_dir) / "cache")
        self.assertIn("Failed to clone repo", str(ctx.exception))

    def test_analyze_profile_detects_layered_and_ambiguous_patterns(self) -> None:
        profile_path = FIXTURES_ROOT / "profiles" / "local_profile.yaml"
        with tempfile.TemporaryDirectory() as tmp_dir:
            report = analyze_profile(load_profile(profile_path), profile_path, cache_root=Path(tmp_dir) / "cache")
        reports = {item.repo.repo_id: item for item in report.repo_reports}

        layered = {item.convention_name: item for item in reports["layered-fixture"].conventions}
        self.assertEqual(layered["route_declaration_style"].inferred_value, "express_router_modules")
        self.assertEqual(layered["route_controller_boundary"].inferred_value, "routes_call_controllers")
        self.assertEqual(layered["service_repository_layering"].inferred_value, "controller_service_repository")
        self.assertEqual(layered["auth_middleware_presence"].inferred_value, "auth_middleware_present")

        ambiguous = {item.convention_name: item for item in reports["ambiguous-fixture"].conventions}
        self.assertEqual(ambiguous["route_declaration_style"].inferred_value, "mixed_routes")
        self.assertIn(ambiguous["route_declaration_style"].bucket, {"low", "medium"})
        self.assertEqual(ambiguous["test_layout_shape"].inferred_value, "no_clear_tests")

    def test_detector_regression_fixture_recognizes_layering_feature_routes_and_vitest(self) -> None:
        root = FIXTURES_ROOT / "repos" / "detector_regressions"
        assessments = {
            assessment.convention_name: assessment
            for assessment in analyze_express_repo(
                RepoHandle(
                    repo_id="detector-regressions",
                    source=str(root),
                    source_kind="local_path",
                    role="reference",
                    local_path=str(root),
                    framework="express",
                    language="typescript",
                )
            )
        }
        self.assertEqual(assessments["service_repository_layering"].inferred_value, "controller_service_model")
        self.assertEqual(assessments["route_declaration_style"].inferred_value, "feature_router_modules")
        self.assertEqual(assessments["test_layout_shape"].inferred_value, "vitest_test_layout")

        jest_root = FIXTURES_ROOT / "repos" / "jest_non_supertest"
        jest_assessments = {
            assessment.convention_name: assessment
            for assessment in analyze_express_repo(
                RepoHandle(
                    repo_id="jest-non-supertest",
                    source=str(jest_root),
                    source_kind="local_path",
                    role="reference",
                    local_path=str(jest_root),
                    framework="express",
                    language="javascript",
                )
            )
        }
        self.assertEqual(jest_assessments["test_layout_shape"].inferred_value, "jest_test_layout")

        resource_root = FIXTURES_ROOT / "repos" / "resource_router"
        resource_assessments = {
            assessment.convention_name: assessment
            for assessment in analyze_express_repo(
                RepoHandle(repo_id="resource-router", source=str(resource_root), source_kind="local_path", role="reference", local_path=str(resource_root), framework="express", language="javascript")
            )
        }
        self.assertEqual(resource_assessments["route_declaration_style"].inferred_value, "resource_router_modules")
        self.assertEqual(resource_assessments["service_repository_layering"].inferred_value, "flat_handlers")

        repository_only_root = FIXTURES_ROOT / "repos" / "route_repository_only"
        repository_only_assessments = {
            assessment.convention_name: assessment
            for assessment in analyze_express_repo(
                RepoHandle(repo_id="route-repository-only", source=str(repository_only_root), source_kind="local_path", role="reference", local_path=str(repository_only_root), framework="express", language="typescript")
            )
        }
        self.assertEqual(repository_only_assessments["service_repository_layering"].inferred_value, "repository_only")

        flat_data_root = FIXTURES_ROOT / "repos" / "route_flat_data_access"
        flat_data_assessments = {
            assessment.convention_name: assessment
            for assessment in analyze_express_repo(
                RepoHandle(repo_id="route-flat-data-access", source=str(flat_data_root), source_kind="local_path", role="reference", local_path=str(flat_data_root), framework="express", language="typescript")
            )
        }
        self.assertEqual(flat_data_assessments["service_repository_layering"].inferred_value, "flat_handlers")

        mocha_root = FIXTURES_ROOT / "repos" / "mocha_supertest"
        mocha_assessments = {assessment.convention_name: assessment for assessment in analyze_express_repo(RepoHandle(repo_id="mocha-supertest", source=str(mocha_root), source_kind="local_path", role="reference", local_path=str(mocha_root), framework="express", language="javascript"))}
        self.assertEqual(mocha_assessments["test_layout_shape"].inferred_value, "mocha_supertest_layout")

    def test_benchmark_evaluation_and_reports(self) -> None:
        benchmark_path = FIXTURES_ROOT / "benchmarks" / "local_benchmark.yaml"
        fixture = load_benchmark(benchmark_path)
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = evaluate_benchmark(fixture, benchmark_path, cache_root=Path(tmp_dir) / "cache")

        self.assertEqual(result.total_conventions_evaluated, 18)
        self.assertIn("route_declaration_style", result.exact_match_accuracy_by_convention)
        self.assertIn("high", result.precision_by_confidence_bucket)
        self.assertGreaterEqual(result.ambiguous_repo_count, 1)
        self.assertGreaterEqual(result.unsupported_convention_count, 1)

        analysis_path = FIXTURES_ROOT / "profiles" / "local_profile.yaml"
        with tempfile.TemporaryDirectory() as tmp_dir:
            analysis_report = analyze_profile(load_profile(analysis_path), analysis_path, cache_root=Path(tmp_dir) / "cache")
        analysis_json = render_analysis_json(analysis_report)
        analysis_md = render_analysis_markdown(analysis_report)
        evaluation_json = render_evaluation_json(result)
        evaluation_md = render_evaluation_markdown(result)

        self.assertIn('"profile_id": "fixture-local-profile"', analysis_json)
        self.assertIn("Analysis Report: fixture-local-profile", analysis_md)
        self.assertIn('"benchmark_id": "fixture-benchmark"', evaluation_json)
        self.assertIn("Public Benchmark Summary Table", evaluation_md)
        self.assertIn("Repo Provenance", evaluation_md)
        self.assertIn('"requested_revision"', evaluation_json)

    def test_repository_grouped_logistic_calibration_experiment(self) -> None:
        rows = [
            {
                "repo_id": f"repo-{repo_index}",
                "matched": matched,
                "confidence": confidence,
                "parser_match_rate": confidence,
                "structural_match_rate": confidence,
                "independent_detector_agreement": confidence,
                "test_evidence_rate": 0.5,
                "ambiguity_rate": 1.0 - confidence,
                "signal_strength": confidence,
            }
            for repo_index in range(4)
            for matched, confidence in ((True, 0.9), (False, 0.2))
        ]
        result = run_repository_grouped_logistic_experiment(rows, iterations=200)
        self.assertEqual(result["row_count"], 8)
        self.assertEqual(result["repository_count"], 4)
        self.assertEqual(result["validation"], "leave-one-repository-out")
        self.assertIn("heuristic_brier_score", result)
        self.assertIn("logistic_brier_score", result)

    def test_local_revision_must_match_the_requested_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            repo = root / "repo"
            repo.mkdir()
            (repo / "package.json").write_text('{"dependencies":{"express":"^4.0.0"}}')
            (repo / "app.js").write_text("const express = require('express');")
            self._git(repo, "init")
            self._git(repo, "config", "user.email", "fixture@example.com")
            self._git(repo, "config", "user.name", "Fixture")
            self._git(repo, "add", ".")
            self._git(repo, "commit", "-m", "fixture")
            revision = self._git(repo, "rev-parse", "HEAD")
            profile_path = root / "profile.yaml"
            profile_path.write_text(
                f"""
profile_id: pinned-local
library: developable-rest-express
purpose: local revision verification
reference_repos:
  - repo_id: one
    source: ./repo
    revision: {revision}
  - repo_id: two
    source: ./repo
    revision: {revision}
"""
            )
            prepared = prepare_profile(load_profile(profile_path), profile_path, cache_root=root / "cache")
            self.assertTrue(all(repo_handle.commit_sha == revision for repo_handle in prepared))
            self.assertTrue(all(repo_handle.requested_revision == revision for repo_handle in prepared))

            profile_path.write_text(profile_path.read_text().replace(revision, "b" * 40))
            with self.assertRaises(RepoPreparationError):
                prepare_profile(load_profile(profile_path), profile_path, cache_root=root / "cache")

    def test_pinned_remote_checkout_and_cache_provenance(self) -> None:
        revision = "a" * 40
        review = BenchmarkReview(
            author="fixture-owner",
            reviewer="fixture-owner",
            review_mode="bootstrap_self_review",
            reviewed_at="2026-08-04",
            rationale="Test fixture.",
        )
        fixture = BenchmarkFixture(
            benchmark_id="pinned",
            library="developable-rest-express",
            framework_scope="express",
            review=review,
            repos=[RepoReference(repo_id="pinned", source="https://github.com/example/pinned.git", revision=revision)],
            expected_conventions={
                "pinned": {
                    "route_declaration_style": "express_router_modules",
                    "route_controller_boundary": "routes_call_controllers",
                    "validation_at_edge_pattern": "route_validation_middleware",
                    "service_repository_layering": "layering_unclear",
                    "auth_middleware_presence": "auth_middleware_present",
                    "test_layout_shape": "no_clear_tests",
                }
            },
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_root = Path(tmp_dir) / "cache"
            commands: list[list[str]] = []

            def fake_run_git(command: list[str], action: str) -> str:
                commands.append(command)
                if "clone" in command:
                    destination = Path(command[-1])
                    destination.mkdir(parents=True)
                    (destination / ".git").mkdir()
                    (destination / "package.json").write_text('{"dependencies":{"express":"^4.0.0"}}')
                    return ""
                if "config" in command:
                    return "https://github.com/example/pinned.git"
                if "rev-parse" in command:
                    return revision
                if "checkout" in command:
                    return ""
                raise AssertionError(f"Unexpected git command: {command}")

            with mock.patch("developable_rest_express.workspace._run_git", side_effect=fake_run_git):
                prepared = prepare_benchmark(fixture, Path(tmp_dir) / "benchmark.yaml", cache_root=cache_root)
            self.assertEqual(prepared[0].commit_sha, revision)
            self.assertFalse(prepared[0].prepared_from_cache)
            self.assertTrue(any("checkout" in command and "--detach" in command for command in commands))
            self.assertTrue((cache_root / f"example__pinned__{revision}").exists())

            with mock.patch("developable_rest_express.workspace._run_git", side_effect=fake_run_git):
                cached = prepare_benchmark(fixture, Path(tmp_dir) / "benchmark.yaml", cache_root=cache_root)
            self.assertTrue(cached[0].prepared_from_cache)

    def test_governance_rejects_self_review_after_manual_peer_switch(self) -> None:
        fixture = load_benchmark(FIXTURES_ROOT / "benchmarks" / "local_benchmark.yaml")
        governance = load_governance(Path(__file__).parents[1] / "benchmark-governance.yaml")
        validate_benchmark_review(fixture, governance)

        governance.review_mode = "peer_review"
        governance.maintainers = ["adityaarchunananand", "reviewer"]
        with self.assertRaises(ValueError):
            validate_benchmark_review(fixture, governance)

    def test_reproducibility_fixture_profile_and_benchmark_load(self) -> None:
        profile = load_profile(FIXTURES_ROOT / "profiles" / "reproducible_profile.yaml")
        benchmark = load_benchmark(FIXTURES_ROOT / "benchmarks" / "reproducible_benchmark.yaml")
        self.assertEqual(profile.profile_id, "reproducible-local-profile")
        self.assertEqual(benchmark.benchmark_id, "reproducible-local-benchmark")
        self.assertEqual(benchmark.review.review_mode, "bootstrap_self_review")

    @staticmethod
    def _git(repo: Path, *args: str) -> str:
        result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True)
        return result.stdout.strip()


if __name__ == "__main__":
    unittest.main()
