"""Deterministic Express convention detectors."""

from __future__ import annotations

from typing import List

from ..models import ConventionAssessment, RepoHandle
from .auth_middleware import AuthMiddlewareDetector
from .base import Detector
from .route_controller_boundary import RouteControllerBoundaryDetector
from .route_declaration import RouteDeclarationDetector
from .service_repository_layering import ServiceRepositoryLayeringDetector
from .snapshot import RepoSnapshot
from .test_layout import TestLayoutDetector
from .validation_at_edge import ValidationAtEdgeDetector


DETECTORS: tuple[Detector, ...] = (
    RouteDeclarationDetector(),
    RouteControllerBoundaryDetector(),
    ValidationAtEdgeDetector(),
    ServiceRepositoryLayeringDetector(),
    AuthMiddlewareDetector(),
    TestLayoutDetector(),
)


def analyze_repo(repo: RepoHandle) -> List[ConventionAssessment]:
    """Assess every supported convention for one prepared Express repository.

    Args:
        repo: Prepared repository handle whose framework fingerprint is Express.

    Returns:
        One assessment per convention target, in detector declaration order.
    """
    snapshot = RepoSnapshot(repo.local_path_obj)
    return [detector.assess(repo, snapshot) for detector in DETECTORS]
