from __future__ import annotations

from pathlib import Path

from .adapters.express import analyze_express_repo
from .models import AnalysisReport, ConventionProfile, RepoAnalysis
from .workspace import prepare_profile


def analyze_profile(
    profile: ConventionProfile,
    profile_path: Path,
    cache_root: Path | None = None,
) -> AnalysisReport:
    repo_handles = prepare_profile(profile, profile_path, cache_root=cache_root)
    repo_reports: list[RepoAnalysis] = []
    unsupported_repos = 0

    for repo in repo_handles:
        if repo.framework != "express":
            unsupported_repos += 1
            repo_reports.append(RepoAnalysis(repo=repo, conventions=[]))
            continue

        repo_reports.append(RepoAnalysis(repo=repo, conventions=analyze_express_repo(repo)))

    summary = {
        "total_repos": len(repo_handles),
        "reference_repos": sum(repo.role == "reference" for repo in repo_handles),
        "context_repos": sum(repo.role == "context" for repo in repo_handles),
        "evaluation_repos": sum(repo.role == "evaluation" for repo in repo_handles),
        "unsupported_repos": unsupported_repos,
    }
    notes = ["Confidence is heuristic and not yet benchmark-calibrated."]
    return AnalysisReport(
        profile_id=profile.profile_id,
        library=profile.library,
        expected_framework=profile.expected_framework,
        repos=repo_handles,
        repo_reports=repo_reports,
        summary=summary,
        notes=notes,
    )
