from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from ..models import ConventionTarget, DetectorMetrics
from .base import Classification, Detector, DetectorFinding, Rule, first_match, ratio
from .snapshot import RepoSnapshot


APP_ROUTE_PATTERN = re.compile(r"(?<![\w.])app\.(get|post|put|delete|patch|options|head)\(")
ROUTER_ROUTE_PATTERN = re.compile(r"\b\w*[Rr]outer\.(get|post|put|delete|patch|options|head)\(")

FEATURE_DIRECTORIES = frozenset({"api", "modules", "features"})

MIN_ROUTER_MODULE_FILES = 2
INCIDENTAL_APP_ROUTES = 2

DECORATOR_ROUTING = "decorator_routing"
RESOURCE_ROUTER_MODULES = "resource_router_modules"
FEATURE_ROUTER_MODULES = "feature_router_modules"
EXPRESS_ROUTER_MODULES = "express_router_modules"
INLINE_APP_ROUTES = "inline_app_routes"
MIXED_ROUTES = "mixed_routes"
UNSUPPORTED = "unsupported"

STRONGLY_RECOGNIZED = frozenset({DECORATOR_ROUTING, FEATURE_ROUTER_MODULES})

MIXED_ROUTES_CONFLICT = "Repo mixes multiple route declaration styles."
UNSUPPORTED_CLASSIFICATION = Classification(UNSUPPORTED, 0.9)


def _declares_router(text: str) -> bool:
    """Return whether ``text`` constructs an Express router."""
    return "express.Router" in text or "Router()" in text


def _is_feature_router(snapshot: RepoSnapshot, path: Path) -> bool:
    """Return whether ``path`` is a router colocated inside a feature module."""
    parts = snapshot.relative_parts(path)
    return (
        "router" in path.stem.lower()
        and "routes" not in parts
        and bool(FEATURE_DIRECTORIES & parts)
    )


@dataclass(frozen=True)
class RouteDeclarationSignals:
    """Route declaration markers observed in one repository.

    Attributes:
        router_files: Route files that construct a router.
        app_route_hits: ``app.<method>(`` call sites in route files.
        router_route_hits: Router ``<name>.<method>(`` call sites in route files.
        decorator_hits: ``@Controller(`` occurrences across all code files.
        feature_router_files: Routers colocated inside feature modules.
        resource_router_files: Files importing resource-router middleware.
        declares_routing_controllers: Manifest declares ``routing-controllers``.
        declares_resource_router: Manifest declares resource-router middleware.
    """

    router_files: int
    app_route_hits: int
    router_route_hits: int
    decorator_hits: int
    feature_router_files: int
    resource_router_files: int
    declares_routing_controllers: bool
    declares_resource_router: bool


def _app_routes_are_incidental(signals: RouteDeclarationSignals) -> bool:
    """Return whether a few app-level routes sit beside genuine router modules."""
    return (
        signals.router_files >= MIN_ROUTER_MODULE_FILES
        and signals.app_route_hits <= INCIDENTAL_APP_ROUTES
    )


def _router_modules_lead(signals: RouteDeclarationSignals) -> bool:
    """Return whether router modules dominate app-level route declarations."""
    return bool(signals.router_files) and (
        signals.app_route_hits == 0
        or signals.router_route_hits >= signals.app_route_hits * 2
        or _app_routes_are_incidental(signals)
    )


ROUTE_DECLARATION_RULES: tuple[Rule[RouteDeclarationSignals], ...] = (
    Rule(Classification(DECORATOR_ROUTING, 0.08), lambda s: bool(s.decorator_hits)),
    Rule(Classification(DECORATOR_ROUTING, 0.25), lambda s: s.declares_routing_controllers),
    Rule(Classification(RESOURCE_ROUTER_MODULES, 0.12), lambda s: bool(s.resource_router_files)),
    Rule(Classification(RESOURCE_ROUTER_MODULES, 0.3), lambda s: s.declares_resource_router),
    Rule(Classification(FEATURE_ROUTER_MODULES, 0.12), lambda s: bool(s.feature_router_files)),
    Rule(
        Classification(EXPRESS_ROUTER_MODULES, 0.15),
        lambda s: _router_modules_lead(s) and bool(s.app_route_hits),
    ),
    Rule(
        Classification(EXPRESS_ROUTER_MODULES, 0.1),
        lambda s: _router_modules_lead(s) and bool(s.router_route_hits),
    ),
    Rule(Classification(EXPRESS_ROUTER_MODULES, 0.05), _router_modules_lead),
    Rule(
        Classification(INLINE_APP_ROUTES, 0.1),
        lambda s: bool(s.app_route_hits) and not s.router_files,
    ),
    Rule(
        Classification(MIXED_ROUTES, 0.5, (MIXED_ROUTES_CONFLICT,)),
        lambda s: bool(s.router_files) and bool(s.app_route_hits),
    ),
)


class RouteDeclarationDetector(Detector):
    """Detect the style in which routes are declared."""

    convention_name: ClassVar[ConventionTarget] = "route_declaration_style"
    unsupported_values: ClassVar[frozenset[str]] = frozenset({UNSUPPORTED})
    ambiguous_values: ClassVar[frozenset[str]] = frozenset({MIXED_ROUTES, UNSUPPORTED})

    def detect(self, snapshot: RepoSnapshot) -> DetectorFinding:
        """Return the route declaration finding for ``snapshot``."""
        signals = self._gather(snapshot)
        classification = first_match(
            ROUTE_DECLARATION_RULES, signals, UNSUPPORTED_CLASSIFICATION
        )
        return DetectorFinding(
            classification=classification,
            metrics=self._metrics(snapshot, signals, classification),
            evidence=self._evidence(signals),
        )

    @staticmethod
    def _gather(snapshot: RepoSnapshot) -> RouteDeclarationSignals:
        package_text = snapshot.package_text
        route_texts = [snapshot.text(path) for path in snapshot.route_files]
        return RouteDeclarationSignals(
            router_files=sum(_declares_router(text) for text in route_texts),
            app_route_hits=sum(len(APP_ROUTE_PATTERN.findall(text)) for text in route_texts),
            router_route_hits=sum(len(ROUTER_ROUTE_PATTERN.findall(text)) for text in route_texts),
            decorator_hits=sum(
                snapshot.text(path).count("@Controller(") for path in snapshot.code_files
            ),
            feature_router_files=sum(
                _is_feature_router(snapshot, path) for path in snapshot.code_files
            ),
            resource_router_files=sum(
                "resource-router-middleware" in snapshot.text(path)
                for path in snapshot.code_files
            ),
            declares_routing_controllers="routing-controllers" in package_text,
            declares_resource_router="resource-router-middleware" in package_text,
        )

    @staticmethod
    def _agreement(value: str) -> float:
        if value in STRONGLY_RECOGNIZED:
            return 0.9
        return 0.85 if value != UNSUPPORTED else 0.2

    @classmethod
    def _metrics(
        cls,
        snapshot: RepoSnapshot,
        signals: RouteDeclarationSignals,
        classification: Classification,
    ) -> DetectorMetrics:
        route_candidates = max(len(snapshot.route_files), 1)
        declarations = signals.router_files + signals.app_route_hits + signals.router_route_hits
        return DetectorMetrics(
            parser_match_rate=ratio(declarations, route_candidates * 4),
            structural_match_rate=ratio(signals.router_files, route_candidates),
            independent_detector_agreement=cls._agreement(classification.value),
            test_evidence_rate=snapshot.test_signal,
            ambiguity_rate=classification.ambiguity_rate,
        )

    @staticmethod
    def _evidence(signals: RouteDeclarationSignals) -> tuple[str, ...]:
        return (
            f"Detected {signals.router_files} router-oriented files.",
            f"Detected {signals.app_route_hits} app-level route call sites in route candidates.",
            f"Detected {signals.router_route_hits} router-level route call sites in route candidates.",
            f"Detected {signals.decorator_hits} controller decorators.",
            f"Detected {signals.feature_router_files} feature router files.",
            f"Detected {signals.resource_router_files} resource-router module files.",
        )
