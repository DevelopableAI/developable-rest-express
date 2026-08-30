"""Detection of how a repository layers its request handling and data access."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from typing import ClassVar, Iterable, Sequence

from ..models import ConventionTarget, DetectorMetrics
from .base import Classification, Detector, DetectorFinding, Rule, first_match, ratio
from .snapshot import RepoSnapshot


CONTROLLER_DIRECTORIES = frozenset({"controllers", "controller"})
MANAGER_DIRECTORIES = frozenset({"manager", "managers"})
FEATURE_DIRECTORIES = frozenset({"api", "modules", "features"})
DATA_ACCESS_MARKERS = ("/db", "database", "model", "prisma", "drizzle", "redis", "client")

CLEAN_ARCHITECTURE_PORTS = "clean_architecture_ports"
REPOSITORY_ONLY = "repository_only"
FLAT_HANDLERS = "flat_handlers"
CONTROLLER_SERVICE_REPOSITORY = "controller_service_repository"
CONTROLLER_SERVICE_MODEL = "controller_service_model"
CONTROLLER_MANAGER_MODEL = "controller_manager_model"
CONTROLLER_MODEL = "controller_model"
CONTROLLER_REPOSITORY = "controller_repository"
SERVICE_DATA_ACCESS = "service_data_access"
FEATURE_SERVICE_LAYER = "feature_service_layer"
LAYERING_UNCLEAR = "layering_unclear"

STRONGLY_LAYERED = frozenset(
    {CONTROLLER_SERVICE_REPOSITORY, CONTROLLER_SERVICE_MODEL, CONTROLLER_MANAGER_MODEL}
)

CONTROLLER_BYPASS_CONFLICT = (
    "Controller layer bypasses services and reaches repositories directly."
)
ROUTE_REPOSITORY_CONFLICT = "Route handlers access repositories directly."
ROUTE_DATA_ACCESS_CONFLICT = "Route handlers access data utilities directly."

LAYERING_UNCLEAR_CLASSIFICATION = Classification(LAYERING_UNCLEAR, 0.85)


def _count_mentions(specifiers: Sequence[str], token: str) -> int:
    """Count import specifiers mentioning ``token``."""
    return sum(token in item.lower() for item in specifiers)


def _mentions_any(specifier: str, tokens: Iterable[str]) -> bool:
    """Return whether an import specifier mentions any of ``tokens``."""
    lowered = specifier.lower()
    return any(token in lowered for token in tokens)


@dataclass(frozen=True)
class LayeringSignals:
    """Structural layering markers observed in one repository.

    Directory counts are measured from each file's own package manifest, while
    the import edges are attributed using snapshot-root-relative paths. The two
    measures deliberately differ; see :class:`RepoSnapshot`.
    """

    controller_dirs: int
    service_dirs: int
    repository_dirs: int
    manager_dirs: int
    model_dirs: int
    application_dirs: int
    ports_dirs: int
    infrastructure_dirs: int
    handler_dirs: int
    controller_to_service: int
    controller_to_repository: int
    controller_to_manager: int
    controller_to_model: int
    service_to_repository: int
    service_to_model: int
    manager_to_model: int
    route_to_repository: int
    route_direct_data_access: int
    feature_service_files: int
    declares_resource_router: bool


LAYERING_RULES: tuple[Rule[LayeringSignals], ...] = (
    Rule(
        Classification(CLEAN_ARCHITECTURE_PORTS, 0.12),
        lambda s: bool(s.application_dirs and s.ports_dirs and s.infrastructure_dirs),
    ),
    Rule(
        Classification(REPOSITORY_ONLY, 0.18),
        lambda s: bool(s.route_to_repository) and not s.controller_dirs,
    ),
    Rule(
        Classification(FLAT_HANDLERS, 0.2),
        lambda s: bool(s.route_direct_data_access) and not s.controller_dirs,
    ),
    Rule(
        Classification(CONTROLLER_SERVICE_REPOSITORY, 0.08),
        lambda s: bool(
            s.controller_dirs
            and s.service_dirs
            and s.repository_dirs
            and s.controller_to_service
            and s.service_to_repository
        ),
    ),
    Rule(
        Classification(CONTROLLER_SERVICE_MODEL, 0.12),
        lambda s: bool(
            s.controller_dirs
            and s.service_dirs
            and s.model_dirs
            and s.controller_to_service
            and s.service_to_model
        ),
    ),
    Rule(
        Classification(CONTROLLER_MANAGER_MODEL, 0.12),
        lambda s: bool(
            s.controller_dirs
            and s.manager_dirs
            and s.model_dirs
            and s.controller_to_manager
            and s.manager_to_model
        ),
    ),
    Rule(
        Classification(CONTROLLER_MODEL, 0.18),
        lambda s: bool(s.controller_dirs and s.model_dirs and s.controller_to_model),
    ),
    Rule(
        Classification(CONTROLLER_REPOSITORY, 0.3),
        lambda s: bool(s.controller_dirs and s.repository_dirs and s.controller_to_repository),
    ),
    Rule(
        Classification(SERVICE_DATA_ACCESS, 0.2),
        lambda s: bool(s.service_dirs and s.model_dirs),
    ),
    Rule(
        Classification(FEATURE_SERVICE_LAYER, 0.25),
        lambda s: bool(s.feature_service_files),
    ),
    Rule(Classification(FLAT_HANDLERS, 0.25), lambda s: s.declares_resource_router),
    Rule(Classification(FLAT_HANDLERS, 0.45), lambda s: bool(s.handler_dirs)),
)


def _conflicts_for(value: str, signals: LayeringSignals) -> tuple[str, ...]:
    """Return the conflicts implied by a layering conclusion.

    Flat handlers only conflict when routes reach data utilities directly, so
    the conflict cannot be attached to the rules that produce that value.
    """
    if value == CONTROLLER_REPOSITORY:
        return (CONTROLLER_BYPASS_CONFLICT,)
    if value == REPOSITORY_ONLY:
        return (ROUTE_REPOSITORY_CONFLICT,)
    if value == FLAT_HANDLERS and signals.route_direct_data_access:
        return (ROUTE_DATA_ACCESS_CONFLICT,)
    return ()


def _count_import_edges(snapshot: RepoSnapshot) -> Counter[str]:
    """Count layer-to-layer import edges in a single pass over the code files."""
    edges: Counter[str] = Counter()
    route_files = set(snapshot.route_files)
    for path in snapshot.code_files:
        specifiers = snapshot.imports_in(path)
        parts = snapshot.relative_parts(path)
        if CONTROLLER_DIRECTORIES & parts or "controller" in path.stem.lower():
            edges["controller_to_service"] += _count_mentions(specifiers, "service")
            edges["controller_to_repository"] += _count_mentions(specifiers, "repo")
            edges["controller_to_manager"] += _count_mentions(specifiers, "manager")
            edges["controller_to_model"] += _count_mentions(specifiers, "model")
        if "services" in parts:
            edges["service_to_repository"] += _count_mentions(specifiers, "repo")
            edges["service_to_model"] += _count_mentions(specifiers, "model")
        if MANAGER_DIRECTORIES & parts:
            edges["manager_to_model"] += _count_mentions(specifiers, "model")
        if path in route_files:
            edges["route_to_repository"] += _count_mentions(specifiers, "repo")
            edges["route_direct_data_access"] += sum(
                _mentions_any(item, DATA_ACCESS_MARKERS) for item in specifiers
            )
    return edges


class ServiceRepositoryLayeringDetector(Detector):
    """Detect how request handling is layered over data access."""

    convention_name: ClassVar[ConventionTarget] = "service_repository_layering"
    unsupported_values: ClassVar[frozenset[str]] = frozenset({LAYERING_UNCLEAR})

    def detect(self, snapshot: RepoSnapshot) -> DetectorFinding:
        """Return the layering finding for ``snapshot``."""
        signals = self._gather(snapshot)
        matched = first_match(LAYERING_RULES, signals, LAYERING_UNCLEAR_CLASSIFICATION)
        classification = replace(matched, conflicts=_conflicts_for(matched.value, signals))
        return DetectorFinding(
            classification=classification,
            metrics=self._metrics(snapshot, signals, classification),
            evidence=self._evidence(signals),
        )

    @staticmethod
    def _gather(snapshot: RepoSnapshot) -> LayeringSignals:
        edges = _count_import_edges(snapshot)
        named_controllers = sum("controller" in path.stem.lower() for path in snapshot.code_files)
        named_models = sum("model" in path.stem.lower() for path in snapshot.code_files)
        return LayeringSignals(
            controller_dirs=snapshot.directory_count("controllers")
            + snapshot.directory_count("controller")
            + named_controllers,
            service_dirs=snapshot.directory_count("services"),
            repository_dirs=snapshot.directory_count("repositories")
            + snapshot.directory_count("repos"),
            manager_dirs=snapshot.directory_count("manager")
            + snapshot.directory_count("managers"),
            model_dirs=snapshot.directory_count("models")
            + snapshot.directory_count("model")
            + named_models,
            application_dirs=snapshot.directory_count("application"),
            ports_dirs=snapshot.directory_count("ports"),
            infrastructure_dirs=snapshot.directory_count("infrastructure"),
            handler_dirs=snapshot.directory_count("handlers"),
            controller_to_service=edges["controller_to_service"],
            controller_to_repository=edges["controller_to_repository"],
            controller_to_manager=edges["controller_to_manager"],
            controller_to_model=edges["controller_to_model"],
            service_to_repository=edges["service_to_repository"],
            service_to_model=edges["service_to_model"],
            manager_to_model=edges["manager_to_model"],
            route_to_repository=edges["route_to_repository"],
            route_direct_data_access=edges["route_direct_data_access"],
            feature_service_files=sum(
                bool(FEATURE_DIRECTORIES & snapshot.relative_parts(path))
                and "service" in path.stem.lower()
                for path in snapshot.code_files
            ),
            declares_resource_router="resource-router-middleware" in snapshot.package_text,
        )

    @staticmethod
    def _agreement(value: str) -> float:
        if value in STRONGLY_LAYERED:
            return 0.92
        return 0.7 if value != LAYERING_UNCLEAR else 0.5

    @classmethod
    def _metrics(
        cls,
        snapshot: RepoSnapshot,
        signals: LayeringSignals,
        classification: Classification,
    ) -> DetectorMetrics:
        traced_edges = (
            signals.controller_to_service
            + signals.service_to_repository
            + signals.controller_to_repository
            + signals.route_to_repository
            + signals.route_direct_data_access
        )
        layer_directories = (
            signals.controller_dirs
            + signals.service_dirs
            + signals.repository_dirs
            + signals.manager_dirs
            + signals.model_dirs
        )
        return DetectorMetrics(
            parser_match_rate=ratio(traced_edges, max(len(snapshot.code_files), 1) * 2),
            structural_match_rate=ratio(layer_directories, 3),
            independent_detector_agreement=cls._agreement(classification.value),
            test_evidence_rate=snapshot.test_signal,
            ambiguity_rate=classification.ambiguity_rate,
        )

    @staticmethod
    def _evidence(signals: LayeringSignals) -> tuple[str, ...]:
        return (
            f"Controller directories detected: {signals.controller_dirs}.",
            f"Service directories detected: {signals.service_dirs}.",
            f"Repository directories detected: {signals.repository_dirs}.",
            f"Manager directories detected: {signals.manager_dirs}.",
            f"Model directories detected: {signals.model_dirs}.",
            "Application/ports/infrastructure directories: "
            f"{signals.application_dirs}/{signals.ports_dirs}/{signals.infrastructure_dirs}.",
            f"Controller->service imports: {signals.controller_to_service}.",
            f"Service->repository imports: {signals.service_to_repository}.",
            f"Controller->repository imports: {signals.controller_to_repository}.",
            f"Controller->manager imports: {signals.controller_to_manager}.",
            f"Manager->model imports: {signals.manager_to_model}.",
            f"Controller->model imports: {signals.controller_to_model}.",
            f"Service->model imports: {signals.service_to_model}.",
            f"Route->repository imports: {signals.route_to_repository}.",
            f"Route direct-data-access imports: {signals.route_direct_data_access}.",
            f"Feature service files detected: {signals.feature_service_files}.",
        )
