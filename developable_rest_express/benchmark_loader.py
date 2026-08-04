from __future__ import annotations

from pathlib import Path

import yaml

from .models import BenchmarkFixture
from .governance import find_governance_path, load_governance, validate_benchmark_review


def load_benchmark(path: str | Path) -> BenchmarkFixture:
    benchmark_path = Path(path)
    data = yaml.safe_load(benchmark_path.read_text())
    fixture = BenchmarkFixture.model_validate(data)
    governance_path = find_governance_path(benchmark_path)
    if governance_path is not None:
        validate_benchmark_review(fixture, load_governance(governance_path))
    return fixture
