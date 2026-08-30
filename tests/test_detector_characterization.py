from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

from developable_rest_express.detectors import analyze_repo
from developable_rest_express.models import RepoHandle
from developable_rest_express.workspace import fingerprint_repo


PROJECT_ROOT = Path(__file__).parents[1]
FIXTURE_REPOS = PROJECT_ROOT / "tests" / "fixtures" / "repos"
GOLDEN_PATH = PROJECT_ROOT / "tests" / "fixtures" / "golden" / "express_assessments.json"
REGENERATE_FLAG = "DEVELOPABLE_REGENERATE_DETECTOR_GOLDEN"

CONVENTION_ORDER = (
    "route_declaration_style",
    "route_controller_boundary",
    "validation_at_edge_pattern",
    "service_repository_layering",
    "auth_middleware_presence",
    "test_layout_shape",
)


def fixture_repo_paths() -> list[Path]:
    """Return every fixture repository directory in a stable order."""
    return sorted(path for path in FIXTURE_REPOS.iterdir() if path.is_dir())


def build_handle(repo_path: Path) -> RepoHandle:
    """Return a handle fingerprinted the way the analysis pipeline would.

    Args:
        repo_path: Directory holding one fixture repository.

    Returns:
        A handle carrying the detected framework and language, both of which
        feed the repository-quality term of the score.
    """
    framework, language = fingerprint_repo(repo_path)
    return RepoHandle(
        repo_id=repo_path.name,
        source=repo_path.name,
        source_kind="local_path",
        role="reference",
        local_path=str(repo_path),
        framework=framework,
        language=language,
    )


def analyze_fixture_repos() -> dict[str, list[dict]]:
    """Return every fixture repository's assessments keyed by repository id."""
    return {
        repo_path.name: [
            assessment.model_dump(mode="json")
            for assessment in analyze_repo(build_handle(repo_path))
        ]
        for repo_path in fixture_repo_paths()
    }


def serialize(assessments: dict[str, list[dict]]) -> str:
    """Return canonical JSON so the committed golden stays diff-stable.

    Args:
        assessments: The assessment of the repo by each of the 14 conventions.

    Returns:
        A string version of the assessment for writing to a file. 
    """
    return json.dumps(assessments, indent=2, sort_keys=True) + "\n"


class DetectorCharacterizationTests(unittest.TestCase):
    """Assert the Express detectors still produce their recorded output."""

    maxDiff = None

    def test_fixture_repos_match_the_committed_golden_output(self) -> None:
        actual = analyze_fixture_repos()
        if os.environ.get(REGENERATE_FLAG) == "1":
            self._regenerate(actual)
            self.skipTest(f"Golden regenerated; unset {REGENERATE_FLAG} to assert against it.")
        if not GOLDEN_PATH.exists():
            self.fail(f"Golden file is missing. Create it with {REGENERATE_FLAG}=1.")

        expected = json.loads(GOLDEN_PATH.read_text())
        self.assertEqual(sorted(expected), sorted(actual), "fixture repository set changed")
        for repo_id in sorted(expected):
            with self.subTest(repo=repo_id):
                self.assertEqual(expected[repo_id], actual[repo_id])

    def test_every_fixture_repo_reports_all_conventions_in_order(self) -> None:
        for repo_id, assessments in analyze_fixture_repos().items():
            with self.subTest(repo=repo_id):
                reported = tuple(item["convention_name"] for item in assessments)
                self.assertEqual(CONVENTION_ORDER, reported)

    def _regenerate(self, assessments: dict[str, list[dict]]) -> None:
        GOLDEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN_PATH.write_text(serialize(assessments))
