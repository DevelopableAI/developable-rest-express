"""Detection of where request validation is applied."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from ...models import ConventionTarget, DetectorMetrics
from .base import Classification, Detector, DetectorFinding, ratio
from .snapshot import RepoSnapshot


VALIDATION_LIBS = ("joi", "zod", "yup", "express-validator", "celebrate")

ROUTE_VALIDATION = "route_validation_middleware"
CONTROLLER_VALIDATION = "controller_validation"
NO_CLEAR_VALIDATION = "no_clear_validation"

CONTROLLER_VALIDATION_CONFLICT = (
    "Validation appears to happen inside controllers instead of at the route edge."
)


def _library_mentions(text: str) -> int:
    """Count how many known validation libraries appear in ``text``."""
    return sum(library in text for library in VALIDATION_LIBS)


def _validation_hits(text: str) -> int:
    """Count validation markers in one route file."""
    lowered = text.lower()
    return _library_mentions(text) + lowered.count("validate(") + lowered.count("validator")


@dataclass(frozen=True)
class ValidationSignals:
    """Validation markers observed in one repository.

    Attributes:
        route_hits: Validation occurrences counted across route files.
        controller_hits: Validation-library mentions inside controller files.
        validator_files: Source files that are, or sit under, a validator.
    """

    route_hits: int
    controller_hits: int
    validator_files: int


class ValidationAtEdgeDetector(Detector):
    """Detect whether request validation runs at the route edge."""

    convention_name: ClassVar[ConventionTarget] = "validation_at_edge_pattern"
    unsupported_values: ClassVar[frozenset[str]] = frozenset({NO_CLEAR_VALIDATION})

    def detect(self, snapshot: RepoSnapshot) -> DetectorFinding:
        """Return the validation-placement finding for ``snapshot``."""
        signals = self._gather(snapshot)
        classification = self._classify(signals)
        return DetectorFinding(
            classification=classification,
            metrics=self._metrics(snapshot, signals, classification),
            evidence=self._evidence(signals),
        )

    @staticmethod
    def _gather(snapshot: RepoSnapshot) -> ValidationSignals:
        return ValidationSignals(
            route_hits=sum(_validation_hits(snapshot.text(path)) for path in snapshot.route_files),
            controller_hits=sum(
                _library_mentions(snapshot.text(path))
                for path in snapshot.code_files
                if "controllers" in snapshot.relative_parts(path)
            ),
            validator_files=sum(
                "validator" in path.name.lower() or "validators" in snapshot.relative_parts(path)
                for path in snapshot.code_files
            ),
        )

    @staticmethod
    def _classify(signals: ValidationSignals) -> Classification:
        if signals.route_hits or signals.validator_files:
            return Classification(ROUTE_VALIDATION, 0.15 if signals.route_hits else 0.3)
        if signals.controller_hits:
            return Classification(CONTROLLER_VALIDATION, 0.35, (CONTROLLER_VALIDATION_CONFLICT,))
        return Classification(NO_CLEAR_VALIDATION, 0.8)

    @staticmethod
    def _metrics(
        snapshot: RepoSnapshot,
        signals: ValidationSignals,
        classification: Classification,
    ) -> DetectorMetrics:
        total = signals.route_hits + signals.controller_hits + signals.validator_files
        at_edge = signals.route_hits + signals.validator_files
        return DetectorMetrics(
            parser_match_rate=ratio(total, max(len(snapshot.route_files), 1) * 4),
            structural_match_rate=ratio(at_edge, max(total, 1)),
            independent_detector_agreement=0.85 if classification.value == ROUTE_VALIDATION else 0.5,
            test_evidence_rate=snapshot.test_signal,
            ambiguity_rate=classification.ambiguity_rate,
        )

    @staticmethod
    def _evidence(signals: ValidationSignals) -> tuple[str, ...]:
        return (
            f"Route-level validation signals: {signals.route_hits}.",
            f"Controller-level validation signals: {signals.controller_hits}.",
            f"Validator directory/file signals: {signals.validator_files}.",
        )
