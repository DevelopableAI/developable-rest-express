"""Detection of how a repository layers its request handling and data access."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from typing import ClassVar, Iterable, Sequence

from ..models import ConventionTarget, DetectorMetrics
from .roles import CONTROLLER, MANAGER, SERVICE, assign_roles, count_orm_repository_calls, take_census
from .base import (
    DATA_ACCESS_MARKERS,
    Classification,
    Detector,
    DetectorFinding,
    Rule,
    first_match,
    ratio,
)
from .snapshot import RepoSnapshot


CONTROLLER_DIRECTORIES = frozenset({"controllers", "controller"})
MANAGER_DIRECTORIES = frozenset({"manager", "managers"})
FEATURE_DIRECTORIES = frozenset({"api", "modules", "features"})

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

    Layer membership comes from per-file role assignment rather than from the
    presence of a directory, so a repository organised by feature counts the
    same as one organised by layer. Import edges are attributed from the source
    file's role to the token named in the specifier.
    """

    controllers: int
    services: int
    repositories: int
    managers: int
    models: int
    application_dirs: int
    ports_dirs: int
    infrastructure_dirs: int
    domain_dirs: int
    usecase_dirs: int
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
    route_to_service: int
    orm_repository_calls: int
    feature_service_files: int
    layered_service_dirs: int
    declares_resource_router: bool

    @property
    def is_feature_organised(self) -> bool:
        """Return whether services exist only inside feature modules."""
        if self.has_repository_layer:
            return False
        return bool(self.feature_service_files) and not self.layered_service_dirs

    @property
    def has_repository_layer(self) -> bool:
        """Return whether a repository layer exists as files or as ORM call sites."""
        return bool(self.repositories or self.orm_repository_calls)

    @property
    def reaches_repository_over_service(self) -> bool:
        """Return whether controllers reach repositories rather than services.

        Two shapes count. Controllers may import a repository module more often
        than a service, or the repository may exist only as ORM call sites with
        no service layer to go through at all.
        """
        if self.controller_to_repository > self.controller_to_service:
            return True
        return bool(self.orm_repository_calls) and not self.services

    @property
    def is_layered_architecture(self) -> bool:
        """Return whether the tree separates an application core from adapters."""
        core = self.application_dirs or self.usecase_dirs or self.domain_dirs
        edge = self.ports_dirs or self.infrastructure_dirs
        if core and edge:
            return True
        return bool(self.usecase_dirs and self.domain_dirs)


LAYERING_RULES: tuple[Rule[LayeringSignals], ...] = (
    Rule(
        Classification(CLEAN_ARCHITECTURE_PORTS, 0.12),
        lambda s: s.is_layered_architecture,
    ),
    Rule(
        Classification(REPOSITORY_ONLY, 0.18),
        lambda s: bool(s.route_to_repository) and not s.controllers,
    ),
    Rule(
        Classification(FLAT_HANDLERS, 0.2),
        lambda s: bool(s.route_direct_data_access)
        and not s.controllers
        and not s.route_to_service,
    ),
    Rule(
        Classification(CONTROLLER_REPOSITORY, 0.3),
        lambda s: bool(s.controllers)
        and s.has_repository_layer
        and s.reaches_repository_over_service,
    ),
    Rule(
        Classification(FEATURE_SERVICE_LAYER, 0.25),
        lambda s: s.is_feature_organised,
    ),
    Rule(
        Classification(CONTROLLER_SERVICE_REPOSITORY, 0.08),
        lambda s: bool(s.controllers and s.services and s.controller_to_service)
        and s.has_repository_layer
        and bool(s.service_to_repository or s.orm_repository_calls),
    ),
    Rule(
        Classification(CONTROLLER_SERVICE_MODEL, 0.12),
        lambda s: bool(
            s.controllers and s.services and s.controller_to_service and s.service_to_model
        ),
    ),
    Rule(
        Classification(CONTROLLER_MANAGER_MODEL, 0.12),
        lambda s: bool(
            s.controllers and s.managers and s.models
            and s.controller_to_manager and s.manager_to_model
        ),
    ),
    Rule(
        Classification(CONTROLLER_MODEL, 0.18),
        lambda s: bool(s.controllers and s.models and s.controller_to_model),
    ),
    Rule(
        Classification(SERVICE_DATA_ACCESS, 0.2),
        lambda s: bool(s.services and s.models) and not s.controllers,
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


def _count_import_edges(snapshot: RepoSnapshot, roles: dict) -> Counter[str]:
    """Count layer-to-layer import edges in a single pass over the code files.

    The source layer is the file's assigned role; the target layer is inferred
    from the tokens in the import specifier.
    """
    edges: Counter[str] = Counter()
    route_files = snapshot.route_file_set
    for path in snapshot.code_files:
        specifiers = snapshot.imports_in(path)
        role = roles.get(path)
        if role == CONTROLLER:
            edges["controller_to_service"] += _count_mentions(specifiers, "service")
            edges["controller_to_repository"] += _count_mentions(specifiers, "repo")
            edges["controller_to_manager"] += _count_mentions(specifiers, "manager")
            edges["controller_to_model"] += _count_data_access(specifiers)
        elif role == SERVICE:
            edges["service_to_repository"] += _count_mentions(specifiers, "repo")
            edges["service_to_model"] += _count_data_access(specifiers)
        elif role == MANAGER:
            edges["manager_to_model"] += _count_data_access(specifiers)
        if path in route_files:
            edges["route_to_repository"] += _count_mentions(specifiers, "repo")
            edges["route_direct_data_access"] += _count_data_access(specifiers)
            edges["route_to_service"] += _count_mentions(specifiers, "service")
    return edges


def _count_data_access(specifiers: Sequence[str]) -> int:
    """Count specifiers addressing a data-access module of any kind."""
    return sum(_mentions_any(item, DATA_ACCESS_MARKERS) for item in specifiers)


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
        roles = assign_roles(snapshot)
        census = take_census(roles)
        edges = _count_import_edges(snapshot, roles)
        return LayeringSignals(
            controllers=census.controllers,
            services=census.services,
            repositories=census.repositories,
            managers=census.managers,
            models=census.models,
            application_dirs=snapshot.directory_count("application"),
            ports_dirs=snapshot.directory_count("ports"),
            infrastructure_dirs=snapshot.directory_count("infrastructure"),
            domain_dirs=snapshot.directory_count("domain"),
            usecase_dirs=snapshot.directory_count("use-cases")
            + snapshot.directory_count("usecases"),
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
            route_to_service=edges["route_to_service"],
            orm_repository_calls=count_orm_repository_calls(snapshot),
            feature_service_files=sum(
                bool(FEATURE_DIRECTORIES & snapshot.relative_parts(path))
                and "service" in path.stem.lower()
                for path in snapshot.code_files
            ),
            layered_service_dirs=snapshot.directory_count("services"),
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
            signals.controllers
            + signals.services
            + signals.repositories
            + signals.managers
            + signals.models
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
            f"Controller directories detected: {signals.controllers}.",
            f"Service directories detected: {signals.services}.",
            f"Repository directories detected: {signals.repositories}.",
            f"Manager directories detected: {signals.managers}.",
            f"Model directories detected: {signals.models}.",
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
