from __future__ import annotations

from pathlib import Path

import yaml

from .models import BenchmarkFixture, BenchmarkGovernance


def find_governance_path(start_path: Path) -> Path | None:
    for directory in [start_path.parent, *start_path.parent.parents]:
        candidate = directory / "benchmark-governance.yaml"
        if candidate.exists():
            return candidate
    return None


def load_governance(path: str | Path) -> BenchmarkGovernance:
    governance_path = Path(path)
    data = yaml.safe_load(governance_path.read_text())
    return BenchmarkGovernance.model_validate(data)


def validate_benchmark_review(fixture: BenchmarkFixture, governance: BenchmarkGovernance) -> None:
    review = fixture.review
    if review.review_mode != governance.review_mode:
        raise ValueError("benchmark review mode must match benchmark governance")

    if governance.review_mode == "bootstrap_self_review":
        sole_maintainer = governance.maintainers[0]
        if review.author != sole_maintainer or review.reviewer != sole_maintainer:
            raise ValueError("bootstrap self-review requires the configured sole maintainer as author and reviewer")
        return

    if review.author == review.reviewer:
        raise ValueError("peer review requires distinct author and reviewer")
    if review.reviewer not in governance.maintainers:
        raise ValueError("peer reviewer must be listed in benchmark governance maintainers")
