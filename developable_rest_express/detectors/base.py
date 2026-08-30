from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, ClassVar, Generic, Sequence, TypeVar

from ..models import (
    ConventionAssessment,
    ConventionEvidence,
    ConventionTarget,
    DetectorMetrics,
    RepoHandle,
)
from ..scoring import assess_convention

if TYPE_CHECKING:
    from .snapshot import RepoSnapshot


CONFLICT_PENALTY = 0.1
FULL_COVERAGE = 1.0
TYPESCRIPT_REPO_QUALITY = 0.9
JAVASCRIPT_REPO_QUALITY = 0.8
UNSUPPORTED_FRAMEWORK_QUALITY = 0.45

SignalsT = TypeVar("SignalsT")


def ratio(numerator: float, denominator: float) -> float:
    """Return ``numerator / denominator`` clamped to the unit interval.

    Args:
        numerator: Observed count.
        denominator: Population the count is measured against.

    Returns:
        The quotient rounded to four decimal places, or 0.0 when the
        denominator is not positive.
    """
    if denominator <= 0:
        return 0.0
    return round(min(max(float(numerator) / float(denominator), 0.0), 1.0), 4)


@dataclass(frozen=True)
class Classification:
    """A detector's conclusion about one convention.

    Attributes:
        value: The inferred convention value.
        ambiguity_rate: How unclear the supporting evidence was, where a higher
            value means less certainty.
        conflicts: Descriptions of signals that contradict the conclusion.
    """

    value: str
    ambiguity_rate: float
    conflicts: tuple[str, ...] = ()


@dataclass(frozen=True)
class DetectorFinding:
    """A classification together with the metrics that produced it.

    The scorer consumes ``metrics.independent_detector_agreement`` twice: once
    directly as the evidence agreement term and once through signal strength.
    That double count is deliberate and documented in ``docs/scoring.md``.
    Holding it in one field makes the two uses impossible to diverge.

    Attributes:
        classification: The detector's conclusion.
        metrics: Raw evidence rates handed to the scorer.
        evidence: Human-readable counts backing the conclusion.
    """

    classification: Classification
    metrics: DetectorMetrics
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class Rule(Generic[SignalsT]):
    """A guarded classification within a first-match-wins table.

    Attributes:
        classification: Result returned when the guard holds.
        matches: Predicate evaluated against the detector's gathered signals.
    """

    classification: Classification
    matches: Callable[[SignalsT], bool]


def first_match(
    rules: Sequence[Rule[SignalsT]],
    signals: SignalsT,
    fallback: Classification,
) -> Classification:
    """Return the classification of the first rule matching ``signals``.

    Args:
        rules: Ordered rules; earlier entries take priority.
        signals: Structural counts gathered for one repository.
        fallback: Returned when no rule matches.

    Returns:
        The winning classification.
    """
    for rule in rules:
        if rule.matches(signals):
            return rule.classification
    return fallback


class Detector(ABC):
    """Base class for the deterministic Express convention detectors.

    A subclass answers exactly one question about a repository and returns a
    :class:`DetectorFinding`. Every downstream scoring concern -- repository
    quality, coverage, conflict penalty, and the supported and ambiguous flags
    -- is owned here so that no subclass can reimplement it inconsistently.

    Class Attributes:
        convention_name: The convention target this detector reports on.
        unsupported_values: Inferred values meaning no usable signal was found.
        ambiguous_values: Inferred values meaning the evidence was mixed.
            Defaults to ``unsupported_values``; override only where the two
            genuinely differ.
    """

    convention_name: ClassVar[ConventionTarget]
    unsupported_values: ClassVar[frozenset[str]]
    ambiguous_values: ClassVar[frozenset[str] | None] = None

    def assess(self, repo: RepoHandle, snapshot: "RepoSnapshot") -> ConventionAssessment:
        """Detect this convention in ``snapshot`` and score the result.

        Args:
            repo: Prepared repository handle supplying the quality inputs.
            snapshot: Cached view of the repository's files.

        Returns:
            The scored assessment for this convention.
        """
        return assess_convention(self._build_evidence(repo, self.detect(snapshot)))

    @abstractmethod
    def detect(self, snapshot: "RepoSnapshot") -> DetectorFinding:
        """Return this detector's finding for ``snapshot``."""

    def _build_evidence(self, repo: RepoHandle, finding: DetectorFinding) -> ConventionEvidence:
        classification = finding.classification
        return ConventionEvidence(
            convention_name=self.convention_name,
            inferred_value=classification.value,
            agreement=finding.metrics.independent_detector_agreement,
            repo_quality=self._repo_quality(repo),
            coverage=FULL_COVERAGE,
            conflict_penalty=CONFLICT_PENALTY if classification.conflicts else 0.0,
            detector_metrics=finding.metrics,
            evidence=list(finding.evidence),
            affected_repos=[repo.repo_id],
            conflicts=list(classification.conflicts),
            supported=classification.value not in self.unsupported_values,
            ambiguous=classification.value in self._effective_ambiguous_values(),
        )

    @classmethod
    def _effective_ambiguous_values(cls) -> frozenset[str]:
        if cls.ambiguous_values is None:
            return cls.unsupported_values
        return cls.ambiguous_values

    @staticmethod
    def _repo_quality(repo: RepoHandle) -> float:
        if repo.language == "typescript" and repo.framework == "express":
            return TYPESCRIPT_REPO_QUALITY
        if repo.framework == "express":
            return JAVASCRIPT_REPO_QUALITY
        return UNSUPPORTED_FRAMEWORK_QUALITY
