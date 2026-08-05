from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, List

from ..models import ConventionAssessment, ConventionEvidence, ConventionTarget, DetectorMetrics, RepoHandle
from ..scoring import assess_convention


ROUTE_METHOD_PATTERN = re.compile(r"\b(app|router)\.(get|post|put|delete|patch|options|head)\(")
IMPORT_PATTERN = re.compile(r"(?:from\s+['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+)['\"]\))")
VALIDATION_LIBS = ("joi", "zod", "yup", "express-validator", "celebrate")
AUTH_HINTS = ("auth", "authenticate", "passport", "jwt", "requireAuth", "require-auth")


def analyze_express_repo(repo: RepoHandle) -> List[ConventionAssessment]:
    snapshot = RepoSnapshot(repo.local_path_obj)
    return [
        _detect_route_declaration_style(repo, snapshot),
        _detect_route_controller_boundary(repo, snapshot),
        _detect_validation_at_edge(repo, snapshot),
        _detect_service_repository_layering(repo, snapshot),
        _detect_auth_middleware(repo, snapshot),
        _detect_test_layout(repo, snapshot),
    ]


class RepoSnapshot:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.code_files = self._collect_files({".ts", ".js", ".mjs", ".cjs"})
        self.test_files = [
            path
            for path in self.code_files
            if any(part in {"test", "tests", "__tests__"} for part in path.relative_to(self.root).parts)
            or path.name.endswith((".spec.ts", ".spec.js", ".test.ts", ".test.js"))
        ]
        self.package_data = self._load_package_json()
        self.route_files = self._detect_route_files()

    def _collect_files(self, suffixes: set[str]) -> List[Path]:
        files: List[Path] = []
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in {".git", "node_modules", "dist", "build", "coverage"} for part in path.parts):
                continue
            if path.suffix in suffixes:
                files.append(path)
        return files

    def _load_package_json(self) -> dict[str, object]:
        package_path = self.root / "package.json"
        if not package_path.exists():
            return {}
        try:
            return json.loads(package_path.read_text())
        except json.JSONDecodeError:
            return {}

    def _detect_route_files(self) -> List[Path]:
        route_files: List[Path] = []
        for path in self.code_files:
            text = _read(path)
            lower_parts = {part.lower() for part in path.relative_to(self.root).parts}
            if "routes" in lower_parts or "route" in lower_parts or "router" in lower_parts:
                route_files.append(path)
                continue
            if "express.Router" in text or ROUTE_METHOD_PATTERN.search(text):
                route_files.append(path)
        return route_files


def _detect_route_declaration_style(repo: RepoHandle, snapshot: RepoSnapshot) -> ConventionAssessment:
    router_files = 0
    app_route_hits = 0
    router_route_hits = 0
    route_evidence: List[str] = []

    for path in snapshot.route_files:
        text = _read(path)
        if "express.Router" in text or "Router()" in text:
            router_files += 1
        app_route_hits += len(re.findall(r"\bapp\.(get|post|put|delete|patch|options|head)\(", text))
        router_route_hits += len(re.findall(r"\brouter\.(get|post|put|delete|patch|options|head)\(", text))

    decorator_hits = sum(_read(path).count("@Controller(") for path in snapshot.code_files)
    feature_router_files = sum(
        "router" in path.stem.lower()
        and "routes" not in {part.lower() for part in path.relative_to(snapshot.root).parts}
        and bool({"api", "modules", "features"} & {part.lower() for part in path.relative_to(snapshot.root).parts})
        for path in snapshot.code_files
    )
    resource_router_files = sum("resource-router-middleware" in _read(path) for path in snapshot.code_files)

    if decorator_hits or "routing-controllers" in _package_text(snapshot):
        inferred = "decorator_routing"
        ambiguity = 0.08 if decorator_hits else 0.25
    elif resource_router_files or "resource-router-middleware" in _package_text(snapshot):
        inferred = "resource_router_modules"
        ambiguity = 0.12 if resource_router_files else 0.3
    elif feature_router_files:
        inferred = "feature_router_modules"
        ambiguity = 0.12
    elif router_files > 0 and (app_route_hits == 0 or router_route_hits >= app_route_hits * 2):
        inferred = "express_router_modules"
        ambiguity = 0.15 if app_route_hits else (0.1 if router_route_hits else 0.05)
    elif app_route_hits > 0 and router_files == 0:
        inferred = "inline_app_routes"
        ambiguity = 0.1
    elif router_files > 0 and app_route_hits > 0:
        inferred = "mixed_routes"
        ambiguity = 0.5
    else:
        inferred = "unsupported"
        ambiguity = 0.9

    route_evidence.append(f"Detected {router_files} router-oriented files.")
    route_evidence.append(f"Detected {app_route_hits} app-level route call sites in route candidates.")
    route_evidence.append(f"Detected {router_route_hits} router-level route call sites in route candidates.")
    route_evidence.append(f"Detected {decorator_hits} controller decorators.")
    route_evidence.append(f"Detected {feature_router_files} feature router files.")
    route_evidence.append(f"Detected {resource_router_files} resource-router module files.")
    return _build_assessment(
        repo=repo,
        convention_name="route_declaration_style",
        inferred_value=inferred,
        evidence=route_evidence,
        parser_match_rate=_ratio(router_files + app_route_hits + router_route_hits, max(len(snapshot.route_files), 1) * 4),
        structural_match_rate=_ratio(router_files, max(len(snapshot.route_files), 1)),
        independent_detector_agreement=0.9 if inferred in {"decorator_routing", "feature_router_modules"} else (0.85 if inferred != "unsupported" else 0.2),
        test_evidence_rate=_test_signal(snapshot),
        ambiguity_rate=ambiguity,
        conflicts=["Repo mixes multiple route declaration styles."] if inferred == "mixed_routes" else [],
        supported=inferred != "unsupported",
        ambiguous=inferred in {"mixed_routes", "unsupported"},
    )


def _detect_route_controller_boundary(repo: RepoHandle, snapshot: RepoSnapshot) -> ConventionAssessment:
    controller_imports = 0
    service_imports = 0
    repository_imports = 0
    evidence: List[str] = []

    for path in snapshot.route_files:
        imports = _extract_imports(_read(path))
        controller_imports += sum("controller" in item.lower() for item in imports)
        service_imports += sum("service" in item.lower() for item in imports)
        repository_imports += sum("repo" in item.lower() or "repository" in item.lower() for item in imports)

    if controller_imports > 0 and controller_imports >= max(service_imports, repository_imports):
        inferred = "routes_call_controllers"
        ambiguity = 0.1
    elif service_imports > 0 and service_imports >= repository_imports:
        inferred = "routes_call_services"
        ambiguity = 0.25
    elif repository_imports > 0:
        inferred = "routes_call_repositories"
        ambiguity = 0.35
    else:
        inferred = "boundary_unclear"
        ambiguity = 0.85

    evidence.append(f"Route files import controllers {controller_imports} times.")
    evidence.append(f"Route files import services {service_imports} times.")
    evidence.append(f"Route files import repositories {repository_imports} times.")
    return _build_assessment(
        repo=repo,
        convention_name="route_controller_boundary",
        inferred_value=inferred,
        evidence=evidence,
        parser_match_rate=_ratio(controller_imports + service_imports + repository_imports, max(len(snapshot.route_files), 1) * 3),
        structural_match_rate=_ratio(controller_imports, max(controller_imports + service_imports + repository_imports, 1)),
        independent_detector_agreement=0.9 if inferred == "routes_call_controllers" else 0.55,
        test_evidence_rate=_test_signal(snapshot),
        ambiguity_rate=ambiguity,
        conflicts=["Route layer bypasses controllers."] if inferred in {"routes_call_services", "routes_call_repositories"} else [],
        supported=inferred != "boundary_unclear",
        ambiguous=inferred == "boundary_unclear",
    )


def _detect_validation_at_edge(repo: RepoHandle, snapshot: RepoSnapshot) -> ConventionAssessment:
    route_validation_hits = 0
    controller_validation_hits = 0
    validation_dir_hits = 0
    evidence: List[str] = []

    for path in snapshot.route_files:
        text = _read(path)
        route_validation_hits += sum(token in text for token in VALIDATION_LIBS)
        route_validation_hits += text.lower().count("validate(")
        route_validation_hits += text.lower().count("validator")

    for path in snapshot.code_files:
        lower_parts = {part.lower() for part in path.relative_to(snapshot.root).parts}
        text = _read(path)
        if "controllers" in lower_parts:
            controller_validation_hits += sum(token in text for token in VALIDATION_LIBS)
        if "validator" in path.name.lower() or "validators" in lower_parts:
            validation_dir_hits += 1

    if route_validation_hits > 0 or validation_dir_hits > 0:
        inferred = "route_validation_middleware"
        ambiguity = 0.15 if route_validation_hits else 0.3
    elif controller_validation_hits > 0:
        inferred = "controller_validation"
        ambiguity = 0.35
    else:
        inferred = "no_clear_validation"
        ambiguity = 0.8

    evidence.append(f"Route-level validation signals: {route_validation_hits}.")
    evidence.append(f"Controller-level validation signals: {controller_validation_hits}.")
    evidence.append(f"Validator directory/file signals: {validation_dir_hits}.")
    return _build_assessment(
        repo=repo,
        convention_name="validation_at_edge_pattern",
        inferred_value=inferred,
        evidence=evidence,
        parser_match_rate=_ratio(route_validation_hits + controller_validation_hits + validation_dir_hits, max(len(snapshot.route_files), 1) * 4),
        structural_match_rate=_ratio(route_validation_hits + validation_dir_hits, max(route_validation_hits + controller_validation_hits + validation_dir_hits, 1)),
        independent_detector_agreement=0.85 if inferred == "route_validation_middleware" else 0.5,
        test_evidence_rate=_test_signal(snapshot),
        ambiguity_rate=ambiguity,
        conflicts=["Validation appears to happen inside controllers instead of at the route edge."] if inferred == "controller_validation" else [],
        supported=inferred != "no_clear_validation",
        ambiguous=inferred == "no_clear_validation",
    )


def _detect_service_repository_layering(repo: RepoHandle, snapshot: RepoSnapshot) -> ConventionAssessment:
    controllers_dir = _dir_count(snapshot.code_files, "controllers") + _dir_count(snapshot.code_files, "controller")
    services_dir = _dir_count(snapshot.code_files, "services")
    repositories_dir = _dir_count(snapshot.code_files, "repositories") + _dir_count(snapshot.code_files, "repos")
    managers_dir = _dir_count(snapshot.code_files, "manager") + _dir_count(snapshot.code_files, "managers")
    models_dir = _dir_count(snapshot.code_files, "models") + _dir_count(snapshot.code_files, "model")
    application_dir = _dir_count(snapshot.code_files, "application")
    ports_dir = _dir_count(snapshot.code_files, "ports")
    infrastructure_dir = _dir_count(snapshot.code_files, "infrastructure")
    controllers_dir += sum("controller" in path.stem.lower() for path in snapshot.code_files)
    models_dir += sum("model" in path.stem.lower() for path in snapshot.code_files)
    controller_to_service = 0
    service_to_repo = 0
    controller_to_repo = 0
    controller_to_manager = 0
    manager_to_model = 0
    controller_to_model = 0
    service_to_model = 0

    for path in snapshot.code_files:
        imports = _extract_imports(_read(path))
        lower_parts = {part.lower() for part in path.relative_to(snapshot.root).parts}
        if {"controllers", "controller"} & lower_parts or "controller" in path.stem.lower():
            controller_to_service += sum("service" in item.lower() for item in imports)
            controller_to_repo += sum("repo" in item.lower() or "repository" in item.lower() for item in imports)
            controller_to_manager += sum("manager" in item.lower() for item in imports)
            controller_to_model += sum("model" in item.lower() for item in imports)
        if "services" in lower_parts:
            service_to_repo += sum("repo" in item.lower() or "repository" in item.lower() for item in imports)
            service_to_model += sum("model" in item.lower() for item in imports)
        if {"manager", "managers"} & lower_parts:
            manager_to_model += sum("model" in item.lower() for item in imports)

    feature_service_files = sum(
        bool({"api", "modules", "features"} & {part.lower() for part in path.relative_to(snapshot.root).parts})
        and "service" in path.stem.lower()
        for path in snapshot.code_files
    )

    if application_dir and ports_dir and infrastructure_dir:
        inferred = "clean_architecture_ports"
        ambiguity = 0.12
    elif controllers_dir and services_dir and repositories_dir and controller_to_service and service_to_repo:
        inferred = "controller_service_repository"
        ambiguity = 0.08
    elif controllers_dir and services_dir and models_dir and controller_to_service and service_to_model:
        inferred = "controller_service_model"
        ambiguity = 0.12
    elif controllers_dir and managers_dir and models_dir and controller_to_manager and manager_to_model:
        inferred = "controller_manager_model"
        ambiguity = 0.12
    elif controllers_dir and models_dir and controller_to_model:
        inferred = "controller_model"
        ambiguity = 0.18
    elif controllers_dir and repositories_dir and controller_to_repo:
        inferred = "controller_repository"
        ambiguity = 0.3
    elif services_dir and models_dir:
        inferred = "service_data_access"
        ambiguity = 0.2
    elif feature_service_files:
        inferred = "feature_service_layer"
        ambiguity = 0.25
    elif "resource-router-middleware" in _package_text(snapshot):
        inferred = "flat_handlers"
        ambiguity = 0.25
    elif _dir_count(snapshot.code_files, "handlers"):
        inferred = "flat_handlers"
        ambiguity = 0.45
    else:
        inferred = "layering_unclear"
        ambiguity = 0.85

    evidence = [
        f"Controller directories detected: {controllers_dir}.",
        f"Service directories detected: {services_dir}.",
        f"Repository directories detected: {repositories_dir}.",
        f"Manager directories detected: {managers_dir}.",
        f"Model directories detected: {models_dir}.",
        f"Application/ports/infrastructure directories: {application_dir}/{ports_dir}/{infrastructure_dir}.",
        f"Controller->service imports: {controller_to_service}.",
        f"Service->repository imports: {service_to_repo}.",
        f"Controller->repository imports: {controller_to_repo}.",
        f"Controller->manager imports: {controller_to_manager}.",
        f"Manager->model imports: {manager_to_model}.",
        f"Controller->model imports: {controller_to_model}.",
        f"Service->model imports: {service_to_model}.",
        f"Feature service files detected: {feature_service_files}.",
    ]
    return _build_assessment(
        repo=repo,
        convention_name="service_repository_layering",
        inferred_value=inferred,
        evidence=evidence,
        parser_match_rate=_ratio(controller_to_service + service_to_repo + controller_to_repo, max(len(snapshot.code_files), 1) * 2),
        structural_match_rate=_ratio(controllers_dir + services_dir + repositories_dir + managers_dir + models_dir, 3),
        independent_detector_agreement=0.92 if inferred in {"controller_service_repository", "controller_service_model", "controller_manager_model"} else 0.7 if inferred != "layering_unclear" else 0.5,
        test_evidence_rate=_test_signal(snapshot),
        ambiguity_rate=ambiguity,
        conflicts=["Controller layer bypasses services and reaches repositories directly."] if inferred == "controller_repository" else [],
        supported=inferred != "layering_unclear",
        ambiguous=inferred == "layering_unclear",
    )


def _detect_auth_middleware(repo: RepoHandle, snapshot: RepoSnapshot) -> ConventionAssessment:
    auth_file_hits = 0
    route_auth_imports = 0
    middleware_dir_hits = _dir_count(snapshot.code_files, "middleware")

    for path in snapshot.code_files:
        lowered = path.name.lower()
        if any(token.lower() in lowered for token in AUTH_HINTS):
            auth_file_hits += 1

    for path in snapshot.route_files:
        imports = _extract_imports(_read(path))
        route_auth_imports += sum(any(token.lower() in item.lower() for token in AUTH_HINTS) for item in imports)

    if route_auth_imports > 0 or auth_file_hits > 0:
        inferred = "auth_middleware_present"
        ambiguity = 0.15 if route_auth_imports else 0.35
    else:
        inferred = "auth_middleware_unclear"
        ambiguity = 0.8

    evidence = [
        f"Auth-related file names detected: {auth_file_hits}.",
        f"Route imports that look auth-related: {route_auth_imports}.",
        f"Middleware directory signals: {middleware_dir_hits}.",
    ]
    return _build_assessment(
        repo=repo,
        convention_name="auth_middleware_presence",
        inferred_value=inferred,
        evidence=evidence,
        parser_match_rate=_ratio(auth_file_hits + route_auth_imports, max(len(snapshot.route_files), 1) * 2),
        structural_match_rate=_ratio(middleware_dir_hits + auth_file_hits, max(middleware_dir_hits + auth_file_hits + route_auth_imports, 1)),
        independent_detector_agreement=0.88 if inferred == "auth_middleware_present" else 0.35,
        test_evidence_rate=_test_signal(snapshot),
        ambiguity_rate=ambiguity,
        conflicts=[],
        supported=inferred != "auth_middleware_unclear",
        ambiguous=inferred == "auth_middleware_unclear",
    )


def _detect_test_layout(repo: RepoHandle, snapshot: RepoSnapshot) -> ConventionAssessment:
    test_dir_hits = len(snapshot.test_files)
    supertest_hits = 0
    jest_config = any(path.name.startswith("jest.config") for path in snapshot.root.glob("jest.config.*"))
    vitest_config = any(path.name.startswith("vitest.config") for path in snapshot.root.glob("vitest.config.*"))
    package_text = _package_text(snapshot)
    uses_vitest = vitest_config or '"vitest"' in package_text
    uses_jest = jest_config or "jest" in package_text or any("jest" in _read(path).lower() for path in snapshot.test_files)

    for path in snapshot.test_files:
        text = _read(path)
        supertest_hits += text.count("supertest")

    if test_dir_hits and uses_vitest:
        inferred = "vitest_test_layout"
        ambiguity = 0.1
    elif test_dir_hits and supertest_hits and uses_jest:
        inferred = "jest_supertest_layout"
        ambiguity = 0.1
    elif test_dir_hits and uses_jest:
        inferred = "jest_test_layout"
        ambiguity = 0.2
    elif test_dir_hits:
        inferred = "basic_test_layout"
        ambiguity = 0.35
    else:
        inferred = "no_clear_tests"
        ambiguity = 0.85

    evidence = [
        f"Test files detected: {test_dir_hits}.",
        f"supertest mentions detected: {supertest_hits}.",
        f"Jest config present: {'yes' if jest_config else 'no'}.",
        f"Vitest detected: {'yes' if uses_vitest else 'no'}.",
    ]
    return _build_assessment(
        repo=repo,
        convention_name="test_layout_shape",
        inferred_value=inferred,
        evidence=evidence,
        parser_match_rate=_ratio(test_dir_hits + supertest_hits, max(len(snapshot.code_files), 1)),
        structural_match_rate=_ratio(test_dir_hits, max(len(snapshot.code_files), 1)),
        independent_detector_agreement=0.86 if inferred in {"jest_supertest_layout", "jest_test_layout", "vitest_test_layout"} else 0.4,
        test_evidence_rate=_ratio(supertest_hits + test_dir_hits, max(test_dir_hits + 1, 1)),
        ambiguity_rate=ambiguity,
        conflicts=[],
        supported=inferred != "no_clear_tests",
        ambiguous=inferred == "no_clear_tests",
    )


def _build_assessment(
    *,
    repo: RepoHandle,
    convention_name: ConventionTarget,
    inferred_value: str,
    evidence: List[str],
    parser_match_rate: float,
    structural_match_rate: float,
    independent_detector_agreement: float,
    test_evidence_rate: float,
    ambiguity_rate: float,
    conflicts: List[str],
    supported: bool,
    ambiguous: bool,
) -> ConventionAssessment:
    repo_quality = _repo_quality(repo)
    evidence_model = ConventionEvidence(
        convention_name=convention_name,
        inferred_value=inferred_value,
        agreement=independent_detector_agreement,
        repo_quality=repo_quality,
        coverage=1.0,
        conflict_penalty=0.1 if conflicts else 0.0,
        detector_metrics=DetectorMetrics(
            parser_match_rate=parser_match_rate,
            structural_match_rate=structural_match_rate,
            independent_detector_agreement=independent_detector_agreement,
            test_evidence_rate=test_evidence_rate,
            ambiguity_rate=ambiguity_rate,
        ),
        evidence=evidence,
        affected_repos=[repo.repo_id],
        conflicts=conflicts,
        supported=supported,
        ambiguous=ambiguous,
    )
    return assess_convention(evidence_model)


def _repo_quality(repo: RepoHandle) -> float:
    if repo.language == "typescript" and repo.framework == "express":
        return 0.9
    if repo.framework == "express":
        return 0.8
    return 0.45


def _ratio(numerator: int | float, denominator: int | float) -> float:
    if denominator <= 0:
        return 0.0
    return round(min(max(float(numerator) / float(denominator), 0.0), 1.0), 4)


def _extract_imports(text: str) -> List[str]:
    imports: List[str] = []
    for match in IMPORT_PATTERN.findall(text):
        imports.extend([item for item in match if item])
    return imports


def _package_text(snapshot: RepoSnapshot) -> str:
    return json.dumps(snapshot.package_data).lower()


def _dir_count(paths: Iterable[Path], name: str) -> int:
    count = 0
    for path in paths:
        repo_root = _infer_repo_root(path)
        relative_parts = path.relative_to(repo_root).parts if repo_root else path.parts
        if name in {part.lower() for part in relative_parts}:
            count += 1
    return count


def _infer_repo_root(path: Path) -> Path | None:
    for parent in [path] + list(path.parents):
        if (parent / "package.json").exists():
            return parent
    return None


def _test_signal(snapshot: RepoSnapshot) -> float:
    if not snapshot.test_files:
        return 0.0
    supertest_hits = sum("supertest" in _read(path) for path in snapshot.test_files)
    return max(0.3, _ratio(supertest_hits + len(snapshot.test_files), len(snapshot.test_files) * 2))


def _read(path: Path) -> str:
    try:
        return path.read_text(errors="ignore")
    except OSError:
        return ""
