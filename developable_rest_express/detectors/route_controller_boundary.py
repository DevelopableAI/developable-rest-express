from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import ClassVar

from ..models import ConventionTarget, DetectorMetrics
from .base import (
    DATA_ACCESS_MARKERS,
    Classification,
    Detector,
    DetectorFinding,
    ratio,
)
from .snapshot import RepoSnapshot


ROUTES_CALL_CONTROLLERS = "routes_call_controllers"
ROUTES_CALL_SERVICES = "routes_call_services"
ROUTES_CALL_REPOSITORIES = "routes_call_repositories"
BOUNDARY_UNCLEAR = "boundary_unclear"

BYPASS_CONFLICT = "Route layer bypasses controllers."


CONTROLLER_MARKERS = ("controller", "handler")
SERVICE_MARKERS = ("service",)
REPOSITORY_MARKERS = ("repo",)


def _role_of(specifier: str) -> str | None:
    """Return the layer an import specifier addresses, or None.

    A specifier names exactly one layer. Data-access markers are tested first so
    that a data module living under a ``services`` directory is counted as data
    access rather than as a service, which is what the route boundary means.
    """
    lowered = specifier.lower()
    if any(marker in lowered for marker in DATA_ACCESS_MARKERS):
        return "repository"
    if any(marker in lowered for marker in CONTROLLER_MARKERS):
        return "controller"
    if any(marker in lowered for marker in SERVICE_MARKERS):
        return "service"
    if any(marker in lowered for marker in REPOSITORY_MARKERS):
        return "repository"
    return None


@dataclass(frozen=True)
class BoundarySignals:
    """Layers that route files import, counted across the repository.

    Attributes:
        controller_imports: Route imports naming a controller.
        service_imports: Route imports naming a service.
        repository_imports: Route imports naming a repository.
    """

    controller_imports: int
    service_imports: int
    repository_imports: int


class RouteControllerBoundaryDetector(Detector):
    """Detect which layer sits immediately behind the route definitions."""

    convention_name: ClassVar[ConventionTarget] = "route_controller_boundary"
    unsupported_values: ClassVar[frozenset[str]] = frozenset({BOUNDARY_UNCLEAR})

    def detect(self, snapshot: RepoSnapshot) -> DetectorFinding:
        """Return the route boundary finding for ``snapshot``."""
        signals = self._gather(snapshot)
        classification = self._classify(signals)
        return DetectorFinding(
            classification=classification,
            metrics=self._metrics(snapshot, signals, classification),
            evidence=self._evidence(signals),
        )

    @staticmethod
    def _gather(snapshot: RepoSnapshot) -> BoundarySignals:
        specifiers = [
            specifier
            for path in snapshot.route_files
            for specifier in snapshot.imports_in(path)
        ]
        roles = Counter(_role_of(item) for item in specifiers)
        return BoundarySignals(
            controller_imports=roles["controller"],
            service_imports=roles["service"],
            repository_imports=roles["repository"],
        )

    @staticmethod
    def _classify(signals: BoundarySignals) -> Classification:
        deeper = max(signals.service_imports, signals.repository_imports)
        if signals.controller_imports and signals.controller_imports >= deeper:
            return Classification(ROUTES_CALL_CONTROLLERS, 0.1)
        if signals.service_imports and signals.service_imports >= signals.repository_imports:
            return Classification(ROUTES_CALL_SERVICES, 0.25, (BYPASS_CONFLICT,))
        if signals.repository_imports:
            return Classification(ROUTES_CALL_REPOSITORIES, 0.35, (BYPASS_CONFLICT,))
        return Classification(BOUNDARY_UNCLEAR, 0.85)

    @staticmethod
    def _metrics(
        snapshot: RepoSnapshot,
        signals: BoundarySignals,
        classification: Classification,
    ) -> DetectorMetrics:
        total = signals.controller_imports + signals.service_imports + signals.repository_imports
        return DetectorMetrics(
            parser_match_rate=ratio(total, max(len(snapshot.route_files), 1) * 3),
            structural_match_rate=ratio(signals.controller_imports, max(total, 1)),
            independent_detector_agreement=(
                0.9 if classification.value == ROUTES_CALL_CONTROLLERS else 0.55
            ),
            test_evidence_rate=snapshot.test_signal,
            ambiguity_rate=classification.ambiguity_rate,
        )

    @staticmethod
    def _evidence(signals: BoundarySignals) -> tuple[str, ...]:
        return (
            f"Route files import controllers {signals.controller_imports} times.",
            f"Route files import services {signals.service_imports} times.",
            f"Route files import repositories {signals.repository_imports} times.",
        )
