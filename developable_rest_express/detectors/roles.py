"""Architectural role assignment for the files of one repository.

A file's layer is a property of the file, not of the directory holding it. Repositories organise by
layer (``src/services/``), by feature (``src/users/user.service.ts``), or by neither, and decorator
routing puts the route definition inside the controller. Assigning a role per file from several
signals lets the layering detector reason about which layers exist without requiring any particular
directory to be present.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from .snapshot import RepoSnapshot


ROUTE = "route"
CONTROLLER = "controller"
SERVICE = "service"
REPOSITORY = "repository"
MANAGER = "manager"
MODEL = "model"

REPOSITORY_DIRECTORIES = frozenset({"repositories", "repos", "repository"})
MODEL_DIRECTORIES = frozenset(
    {"models", "model", "entities", "entity", "schema", "schemas", "db", "database"}
)
SERVICE_DIRECTORIES = frozenset({"services", "service", "use-cases", "usecases"})
MANAGER_DIRECTORIES = frozenset({"manager", "managers"})
CONTROLLER_DIRECTORIES = frozenset(
    {"controllers", "controller", "request-handlers", "handlers"}
)

MODEL_STEMS = ("model", "entity", "schema", "prisma", "drizzle", "knex", "sequelize", "mongoose")

CONTROLLER_DECORATOR = re.compile(r"@(?:Json)?Controller\(")
ORM_REPOSITORY_CALL = re.compile(r"getRepository\(|getCustomRepository\(|@InjectRepository")


@dataclass(frozen=True)
class RoleCensus:
    """How many files play each architectural role.

    Attributes:
        routes: Files declaring HTTP routes.
        controllers: Files handling a request and delegating onward.
        services: Files holding application or domain logic.
        repositories: Files encapsulating persistence access.
        managers: Files playing the manager variant of a service.
        models: Files defining data shapes, ORM schemas, or database clients.
    """

    routes: int
    controllers: int
    services: int
    repositories: int
    managers: int
    models: int


def role_of(snapshot: "RepoSnapshot", path: Path) -> Optional[str]:
    """Return the architectural role ``path`` plays, or None when unclear.

    Roles are tested most-specific first. A controller carrying routing decorators is a controller
    rather than a route, because the delegation boundary is what the layering question asks about.
    """
    parts = snapshot.relative_parts(path)
    stem = path.stem.lower()
    if REPOSITORY_DIRECTORIES & parts or "repositor" in stem:
        return REPOSITORY
    if MODEL_DIRECTORIES & parts or any(token in stem for token in MODEL_STEMS):
        return MODEL
    if SERVICE_DIRECTORIES & parts or "service" in stem:
        return SERVICE
    if MANAGER_DIRECTORIES & parts or "manager" in stem:
        return MANAGER
    if CONTROLLER_DIRECTORIES & parts or "controller" in stem:
        return CONTROLLER
    if CONTROLLER_DECORATOR.search(snapshot.text(path)):
        return CONTROLLER
    if path in snapshot.route_file_set:
        return ROUTE
    return None


def assign_roles(snapshot: "RepoSnapshot") -> Dict[Path, Optional[str]]:
    """Return the role of every code file in ``snapshot``."""
    return {path: role_of(snapshot, path) for path in snapshot.code_files}


def take_census(roles: Dict[Path, Optional[str]]) -> RoleCensus:
    """Return how many files play each role."""
    counts: Dict[Optional[str], int] = {}
    for role in roles.values():
        counts[role] = counts.get(role, 0) + 1
    return RoleCensus(
        routes=counts.get(ROUTE, 0),
        controllers=counts.get(CONTROLLER, 0),
        services=counts.get(SERVICE, 0),
        repositories=counts.get(REPOSITORY, 0),
        managers=counts.get(MANAGER, 0),
        models=counts.get(MODEL, 0),
    )


def count_orm_repository_calls(snapshot: "RepoSnapshot") -> int:
    """Count call sites where a repository is obtained from the ORM.

    Some repositories have a repository layer with no repository file and no
    repository directory: TypeORM hands one back from ``getRepository(Entity)``.
    File-based role assignment cannot see that layer, so it is counted separately.
    """
    return sum(len(ORM_REPOSITORY_CALL.findall(snapshot.text(path))) for path in snapshot.code_files)
