from abc import ABC, abstractmethod
from typing import ClassVar

from pydantic.dataclasses import dataclass

from developable_rest_express.adapters.express import RepoSnapshot
from developable_rest_express.models import ConventionAssessment, ConventionTarget, DetectorMetrics, RepoHandle
from developable_rest_express.scoring import assess_convention


@dataclass(frozen=True)
class Classification:
    value: str
    ambiguity_rate: float
    conflicts: tuple[str, ...] = ()

@dataclass(frozen=True)
class DetectorFinding:
    classification: Classification
    metrics: DetectorMetrics
    agreement: float
    evidence: tuple[str, ...]

class Detector(ABC):
    convention_name: ClassVar[ConventionTarget]
    unsupported_values: ClassVar[frozenset[str]]
    ambiguous_values: ClassVar[frozenset[str] | None] = None   # None → same as unsupported_values

    def assess(self, repo: RepoHandle, snapshot: RepoSnapshot) -> ConventionAssessment:
        return assess_convention(self._to_evidence(repo, self.detect(snapshot)))

    @abstractmethod
    def detect(self, snapshot: RepoSnapshot) -> DetectorFinding:
        ...
