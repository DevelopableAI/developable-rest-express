from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Iterable, List
from urllib.parse import urlparse

from .models import BenchmarkFixture, ConventionProfile, RepoHandle, RepoReference, RepoRole


DEFAULT_CACHE_ROOT = Path(".developable-rest-express/cache/repos")


class RepoPreparationError(RuntimeError):
    """Raised when a repo cannot be prepared for analysis."""


def prepare_profile(profile: ConventionProfile, profile_path: Path, cache_root: Path | None = None) -> List[RepoHandle]:
    return _prepare_repo_groups(
        source_groups=[
            ("reference", profile.reference_repos),
            ("context", profile.context_repos),
            ("evaluation", profile.evaluation_set),
        ],
        source_path=profile_path,
        cache_root=cache_root,
        require_remote_revision=False,
    )


def prepare_benchmark(
    fixture: BenchmarkFixture,
    fixture_path: Path,
    cache_root: Path | None = None,
) -> List[RepoHandle]:
    return _prepare_repo_groups(
        source_groups=[("evaluation", fixture.repos)],
        source_path=fixture_path,
        cache_root=cache_root,
        require_remote_revision=True,
    )


def _prepare_repo_groups(
    source_groups: list[tuple[RepoRole, Iterable[RepoReference]]],
    source_path: Path,
    cache_root: Path | None = None,
    require_remote_revision: bool = False,
) -> List[RepoHandle]:
    handles: List[RepoHandle] = []
    effective_cache_root = _resolve_cache_root(source_path, cache_root)
    seen_ids: set[str] = set()

    for role, refs in source_groups:
        for repo_ref in refs:
            if repo_ref.repo_id in seen_ids:
                raise RepoPreparationError(f"duplicate repo_id encountered during preparation: {repo_ref.repo_id}")
            handles.append(
                prepare_repo_reference(
                    repo_ref,
                    role,
                    source_path.parent,
                    effective_cache_root,
                    require_remote_revision=require_remote_revision,
                )
            )
            seen_ids.add(repo_ref.repo_id)

    return handles


def prepare_repo_reference(
    repo_ref: RepoReference,
    role: RepoRole,
    source_base: Path,
    cache_root: Path,
    require_remote_revision: bool = False,
) -> RepoHandle:
    if repo_ref.source_kind == "local_path":
        resolved_path = _resolve_local_source(repo_ref.source, source_base)
        if not resolved_path.exists():
            raise RepoPreparationError(f"local repo path does not exist: {resolved_path}")
        notes = ["Prepared from local path."]
        prepared_from_cache = False
    else:
        if require_remote_revision and not repo_ref.revision:
            raise RepoPreparationError(f"GitHub benchmark repo requires a revision: {repo_ref.repo_id}")
        resolved_path, prepared_from_cache = _prepare_github_repo(
            repo_ref.source,
            repo_ref.repo_id,
            cache_root,
            revision=repo_ref.revision,
        )
        notes = ["Prepared from GitHub URL cache."]
        if prepared_from_cache:
            notes.append("Reused cached checkout.")
        else:
            notes.append("Created new cached checkout.")

    framework, language = fingerprint_repo(resolved_path)
    commit_sha = resolve_commit_sha(resolved_path)
    if repo_ref.revision and commit_sha != repo_ref.revision:
        raise RepoPreparationError(
            f"repo '{repo_ref.repo_id}' resolved revision {commit_sha or 'unknown'} instead of requested {repo_ref.revision}"
        )

    if framework != "express":
        notes.append(f"Detected framework '{framework}', which is outside the current V1 scope.")

    return RepoHandle(
        repo_id=repo_ref.repo_id,
        source=repo_ref.source,
        source_kind=repo_ref.source_kind,
        role=role,
        local_path=str(resolved_path),
        requested_revision=repo_ref.revision,
        commit_sha=commit_sha,
        framework=framework,
        language=language,
        prepared_from_cache=prepared_from_cache,
        notes=notes,
    )


def _resolve_cache_root(source_path: Path, cache_root: Path | None) -> Path:
    return cache_root or (source_path.parent / DEFAULT_CACHE_ROOT)


def _resolve_local_source(source: str, source_base: Path) -> Path:
    source_path = Path(source).expanduser()
    if not source_path.is_absolute():
        source_path = (source_base / source_path).resolve()
    return source_path


def _prepare_github_repo(
    source: str,
    repo_id: str,
    cache_root: Path,
    revision: str | None = None,
) -> tuple[Path, bool]:
    parsed_owner, parsed_name = parse_github_repo(source)
    cache_key = f"{parsed_owner}__{parsed_name}"
    if revision:
        cache_key = f"{cache_key}__{revision}"
    dest = cache_root / cache_key
    canonical_source = canonical_github_source(source)
    if dest.exists():
        if _cache_matches(dest, canonical_source, revision):
            return dest, True
        raise RepoPreparationError(f"cached checkout failed provenance validation: {dest}")

    dest.parent.mkdir(parents=True, exist_ok=True)
    temporary_dest = dest.parent / f".{cache_key}.tmp-{uuid.uuid4().hex}"
    try:
        clone_command = ["git", "clone"]
        if revision:
            clone_command.append("--no-checkout")
        else:
            clone_command.extend(["--depth", "1"])
        clone_command.extend([source, str(temporary_dest)])
        _run_git(clone_command, f"clone repo from {source}")
        if revision:
            _run_git(
                ["git", "-C", str(temporary_dest), "checkout", "--detach", revision],
                f"checkout requested revision {revision}",
            )
        if not _cache_matches(temporary_dest, canonical_source, revision):
            raise RepoPreparationError(f"cloned checkout did not match requested provenance for {repo_id}")
        temporary_dest.replace(dest)
    except Exception:
        if temporary_dest.exists():
            shutil.rmtree(temporary_dest)
        raise
    return dest, False


def canonical_github_source(source: str) -> str:
    owner, name = parse_github_repo(source)
    return f"https://github.com/{owner}/{name}.git"


def _cache_matches(repo_path: Path, canonical_source: str, revision: str | None) -> bool:
    if not (repo_path / ".git").exists():
        return False
    try:
        origin = _run_git(
            ["git", "-C", str(repo_path), "config", "--get", "remote.origin.url"],
            "read remote origin",
        )
        if canonical_github_source(origin) != canonical_source:
            return False
        if revision:
            return resolve_commit_sha(repo_path) == revision
        return True
    except RepoPreparationError:
        return False


def parse_github_repo(source: str) -> tuple[str, str]:
    normalized = source.strip().rstrip("/")
    if normalized.endswith(".git"):
        normalized = normalized[:-4]

    if normalized.startswith("git@github.com:"):
        remainder = normalized.split(":", 1)[1]
        owner, name = remainder.split("/", 1)
        return owner, name

    parsed = urlparse(normalized)
    if "github.com" not in parsed.netloc:
        raise RepoPreparationError(f"unsupported remote source; expected a GitHub URL: {source}")

    path_bits = [bit for bit in parsed.path.split("/") if bit]
    if len(path_bits) < 2:
        raise RepoPreparationError(f"could not derive owner/repo from GitHub URL: {source}")
    return path_bits[0], path_bits[1]


def _run_git(command: list[str], action: str) -> str:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RepoPreparationError(f"Failed to {action}: {stderr}")
    return result.stdout.strip()


def resolve_commit_sha(repo_path: Path) -> str | None:
    if not (repo_path / ".git").exists():
        return None
    try:
        return _run_git(["git", "-C", str(repo_path), "rev-parse", "HEAD"], "read commit sha")
    except RepoPreparationError:
        return None


def fingerprint_repo(repo_path: Path) -> tuple[str, str]:
    package_json_path = repo_path / "package.json"
    package_data: dict[str, object] = {}
    if package_json_path.exists():
        try:
            package_data = json.loads(package_json_path.read_text())
        except json.JSONDecodeError:
            package_data = {}

    dependencies = {}
    for key in ("dependencies", "devDependencies"):
        value = package_data.get(key, {})
        if isinstance(value, dict):
            dependencies.update(value)

    if "@nestjs/core" in dependencies:
        framework = "nestjs"
    elif "express" in dependencies or _repo_contains_pattern(repo_path, "express.Router") or _repo_contains_pattern(repo_path, "require('express')") or _repo_contains_pattern(repo_path, 'from "express"'):
        framework = "express"
    else:
        framework = "unknown"

    tsconfig_exists = (repo_path / "tsconfig.json").exists()
    ts_files = list(repo_path.rglob("*.ts"))
    js_files = list(repo_path.rglob("*.js"))
    if tsconfig_exists or ts_files:
        language = "typescript"
    elif js_files:
        language = "javascript"
    else:
        language = "unknown"

    return framework, language


def _repo_contains_pattern(repo_path: Path, pattern: str) -> bool:
    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", "node_modules", "dist", "build", "coverage"} for part in path.parts):
            continue
        if path.suffix not in {".js", ".ts", ".mjs", ".cjs", ".json"}:
            continue
        try:
            if pattern in path.read_text(errors="ignore"):
                return True
        except OSError:
            continue
    return False
