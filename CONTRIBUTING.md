# Contributing

## Benchmark Contributions

Benchmarks are manually labeled, versioned source snapshots. They measure convention inference; they are not training data and must never be generated from the analyzer's own output.

Choose repositories under the [public corpus policy](docs/benchmarks/public-corpus-policy.md): public, Express-based, readable, reasonably sized, and permissively licensed under its SPDX allowlist. Do not add a source checkout to this repository. Fixtures store only source URLs, immutable commit SHAs, labels, and reports.

1. Create the required candidate record: license, canonical source, full SHA, scope, verification evidence, and diversity rationale.
2. Inspect the candidate repository at that specific commit.
3. Add its full 40-character SHA to the profile and benchmark fixture.
4. Label each supported convention from source inspection.
5. Run `developable-rest-express prepare-benchmark <fixture>` and confirm requested and resolved revisions match.
6. Run `developable-rest-express evaluate-benchmark <fixture> --output both` and review every mismatch.
7. Update the fixture review metadata and submit the change for review.

Never point a public benchmark at a branch or a mutable tag. Updating a benchmark means deliberately replacing a SHA in a reviewed change; the harness never refreshes pins automatically.

## Label Review

`benchmark-governance.yaml` defines the active review mode and maintainer allowlist.

- During `bootstrap_self_review`, the sole configured maintainer may be both author and reviewer. Every fixture still requires a non-empty rationale and review date.
- Switch governance manually to `peer_review` when another maintainer is available. Thereafter the reviewer must be a listed maintainer and must differ from the author.

The CI check validates this policy. Repository branch protections and maintainers remain responsible for deciding who can merge changes.

## Local Checks

```bash
python -m pip install -e .
python -m unittest discover -s tests -p 'test_*.py' -v
developable-rest-express prepare-benchmark tests/fixtures/benchmarks/local_benchmark.yaml
developable-rest-express evaluate-benchmark tests/fixtures/benchmarks/local_benchmark.yaml --output both
```

The public corpus is intentionally opt-in because it clones external repositories:

```bash
DEVELOPABLE_RUN_PUBLIC_BENCHMARK=1 \
  python -m unittest discover -s tests -p 'test_public_benchmark.py' -v
```

The scheduled workflow runs this check and publishes the JSON and Markdown benchmark reports. It fails for inaccessible repos, invalid labels, or provenance mismatches, but does not yet enforce an accuracy threshold.
