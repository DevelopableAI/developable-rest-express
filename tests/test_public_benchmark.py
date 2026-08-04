from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from developable_rest_express.benchmark_loader import load_benchmark
from developable_rest_express.evaluation import evaluate_benchmark
from developable_rest_express.workspace import prepare_benchmark


PROJECT_ROOT = Path(__file__).parents[1]
PUBLIC_BENCHMARK = PROJECT_ROOT / "benchmarks" / "public" / "express_v1.yaml"


@unittest.skipUnless(
    os.environ.get("DEVELOPABLE_RUN_PUBLIC_BENCHMARK") == "1",
    "Set DEVELOPABLE_RUN_PUBLIC_BENCHMARK=1 to run the pinned public benchmark.",
)
class PublicBenchmarkTests(unittest.TestCase):
    def test_every_pinned_public_repo_resolves_to_its_requested_sha(self) -> None:
        fixture = load_benchmark(PUBLIC_BENCHMARK)
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_root = Path(os.environ.get("DEVELOPABLE_PUBLIC_BENCHMARK_CACHE", Path(tmp_dir) / "cache"))
            prepared = prepare_benchmark(fixture, PUBLIC_BENCHMARK, cache_root=cache_root)
            result = evaluate_benchmark(fixture, PUBLIC_BENCHMARK, cache_root=cache_root)

        self.assertEqual(result.total_conventions_evaluated, len(fixture.repos) * 6)
        requested_by_id = {repo.repo_id: repo.revision for repo in fixture.repos}
        for repo in prepared:
            self.assertEqual(repo.commit_sha, requested_by_id[repo.repo_id])
