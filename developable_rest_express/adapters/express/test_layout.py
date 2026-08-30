"""Detection of how a repository organises and runs its tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from ...models import ConventionTarget, DetectorMetrics
from .base import Classification, Detector, DetectorFinding, Rule, first_match, ratio
from .snapshot import RepoSnapshot


VITEST_LAYOUT = "vitest_test_layout"
MOCHA_SUPERTEST_LAYOUT = "mocha_supertest_layout"
MOCHA_LAYOUT = "mocha_test_layout"
JEST_SUPERTEST_LAYOUT = "jest_supertest_layout"
JEST_LAYOUT = "jest_test_layout"
BASIC_LAYOUT = "basic_test_layout"
NO_CLEAR_TESTS = "no_clear_tests"

RECOGNIZED_FRAMEWORK_LAYOUTS = frozenset(
    {JEST_SUPERTEST_LAYOUT, JEST_LAYOUT, VITEST_LAYOUT, MOCHA_SUPERTEST_LAYOUT, MOCHA_LAYOUT}
)

NO_TESTS_CLASSIFICATION = Classification(NO_CLEAR_TESTS, 0.85)


@dataclass(frozen=True)
class TestLayoutSignals:
    """Test tooling observed in one repository.

    Attributes:
        test_files: Source files recognised as tests.
        supertest_hits: supertest mentions across test files, plus one when the
            manifest declares the dependency alongside at least one test file.
        jest_config: Whether a root-level Jest config file exists.
        uses_jest: Whether Jest is indicated by config, manifest, or test source.
        uses_vitest: Whether Vitest is indicated by config or manifest.
        uses_mocha: Whether the manifest declares Mocha.
    """

    test_files: int
    supertest_hits: int
    jest_config: bool
    uses_jest: bool
    uses_vitest: bool
    uses_mocha: bool

    @property
    def has_tests(self) -> bool:
        """Return whether any test file was found."""
        return self.test_files > 0

    @property
    def has_supertest(self) -> bool:
        """Return whether any supertest mention was found."""
        return self.supertest_hits > 0


TEST_LAYOUT_RULES: tuple[Rule[TestLayoutSignals], ...] = (
    Rule(Classification(VITEST_LAYOUT, 0.1), lambda s: s.has_tests and s.uses_vitest),
    Rule(
        Classification(MOCHA_SUPERTEST_LAYOUT, 0.1),
        lambda s: s.has_tests and s.uses_mocha and s.has_supertest,
    ),
    Rule(Classification(MOCHA_LAYOUT, 0.15), lambda s: s.has_tests and s.uses_mocha),
    Rule(Classification(JEST_SUPERTEST_LAYOUT, 0.1), lambda s: s.has_tests and s.has_supertest),
    Rule(Classification(JEST_LAYOUT, 0.2), lambda s: s.has_tests and s.uses_jest),
    Rule(Classification(BASIC_LAYOUT, 0.35), lambda s: s.has_tests),
)


def _count_supertest(snapshot: RepoSnapshot, package_text: str) -> int:
    """Count supertest mentions in test files plus the manifest bonus."""
    mentions = sum(snapshot.text(path).count("supertest") for path in snapshot.test_files)
    return mentions + int(bool(snapshot.test_files) and '"supertest"' in package_text)


class TestLayoutDetector(Detector):
    """Detect which test framework and layout a repository uses."""

    convention_name: ClassVar[ConventionTarget] = "test_layout_shape"
    unsupported_values: ClassVar[frozenset[str]] = frozenset({NO_CLEAR_TESTS})

    def detect(self, snapshot: RepoSnapshot) -> DetectorFinding:
        """Return the test-layout finding for ``snapshot``."""
        signals = self._gather(snapshot)
        classification = first_match(TEST_LAYOUT_RULES, signals, NO_TESTS_CLASSIFICATION)
        return DetectorFinding(
            classification=classification,
            metrics=self._metrics(snapshot, signals, classification),
            evidence=self._evidence(signals),
        )

    @staticmethod
    def _gather(snapshot: RepoSnapshot) -> TestLayoutSignals:
        package_text = snapshot.package_text
        jest_config = snapshot.has_root_config("jest.config")
        return TestLayoutSignals(
            test_files=len(snapshot.test_files),
            supertest_hits=_count_supertest(snapshot, package_text),
            jest_config=jest_config,
            uses_jest=(
                jest_config
                or "jest" in package_text
                or any("jest" in snapshot.text(path).lower() for path in snapshot.test_files)
            ),
            uses_vitest=snapshot.has_root_config("vitest.config") or '"vitest"' in package_text,
            uses_mocha='"mocha"' in package_text,
        )

    @staticmethod
    def _metrics(
        snapshot: RepoSnapshot,
        signals: TestLayoutSignals,
        classification: Classification,
    ) -> DetectorMetrics:
        code_files = max(len(snapshot.code_files), 1)
        return DetectorMetrics(
            parser_match_rate=ratio(signals.test_files + signals.supertest_hits, code_files),
            structural_match_rate=ratio(signals.test_files, code_files),
            independent_detector_agreement=(
                0.86 if classification.value in RECOGNIZED_FRAMEWORK_LAYOUTS else 0.4
            ),
            test_evidence_rate=ratio(
                signals.supertest_hits + signals.test_files, signals.test_files + 1
            ),
            ambiguity_rate=classification.ambiguity_rate,
        )

    @staticmethod
    def _evidence(signals: TestLayoutSignals) -> tuple[str, ...]:
        return (
            f"Test files detected: {signals.test_files}.",
            f"supertest mentions detected: {signals.supertest_hits}.",
            f"Jest config present: {'yes' if signals.jest_config else 'no'}.",
            f"Vitest detected: {'yes' if signals.uses_vitest else 'no'}.",
            f"Mocha detected: {'yes' if signals.uses_mocha else 'no'}.",
        )
