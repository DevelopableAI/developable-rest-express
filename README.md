# developable-rest-express

`developable-rest-express` is the Express-specific library in the broader Developable harness family.

Its job is not to magically understand any codebase. Its job is to ingest a bounded set of representative REST service repositories, infer high-value engineering conventions with explicit confidence, and emit portable AI development artifacts such as MCP-facing tool specs, skills, and repo guidance.

V1 stops before MCP or skill emission. It proves the ingestion, deterministic detection, scoring, and benchmark-evaluation foundation first.

## Product stance

This project is intentionally opinionated:

- bounded inference, unbounded retrieval
- deterministic analysis first, LLM assistance second
- convention profiles instead of whole-company ingestion
- confidence that is measurable and calibratable
- architecture-specific libraries instead of one giant framework blob

## Why a dedicated REST library?

REST services are the best first wedge because they usually expose strong structural signals:

- routes and handlers
- validation boundaries
- auth and ownership patterns
- controller/service/repository layering
- test and CI entrypoints
- environment and runtime conventions

Those signals make `developable-rest-express` a much better candidate for deterministic inference than a generic "backend AI harness".

## V1 goals

V1 is intentionally narrow.

It can now:

- define a convention profile made of reference repos and context repos
- validate profile and benchmark fixture structure locally
- accept local repo paths and GitHub repo URLs
- materialize GitHub repos into a repeatable workspace cache
- pin public benchmark repos to immutable Git commit SHAs
- fingerprint repos for framework and language
- infer first-pass Express conventions deterministically
- compute heuristic signal strength and confidence scores
- emit JSON and Markdown analysis/evaluation reports
- evaluate convention inference against labeled benchmark fixtures

V1 does not yet try to:

- parse every framework
- generate production MCP servers
- learn weights automatically from benchmark data
- operationalize low-confidence conventions

## Library structure

- `developable_rest_express/models.py`: typed models for profiles, evidence, and scoring inputs
- `developable_rest_express/profile_loader.py`: profile YAML loading and validation
- `developable_rest_express/benchmark_loader.py`: benchmark YAML loading and validation
- `developable_rest_express/workspace.py`: repo preparation, caching, and fingerprinting
- `developable_rest_express/adapters/express.py`: Express-only deterministic detectors
- `developable_rest_express/analysis.py`: profile analysis pipeline
- `developable_rest_express/evaluation.py`: benchmark evaluation pipeline
- `developable_rest_express/reporting.py`: JSON and Markdown report rendering
- `developable_rest_express/scoring.py`: signal strength and confidence computation
- `developable_rest_express/cli.py`: small CLI for profile validation and scoring demos
- `docs/architecture.md`: project shape and evolution path
- `docs/convention-profile.md`: ingestion contract for a convention profile
- `docs/scoring.md`: scoring semantics and calibration direction
- `docs/public-benchmarking.md`: how to test the harness on curated public GitHub repos
- `CONTRIBUTING.md`: benchmark contribution and review workflow
- `benchmark-governance.yaml`: bootstrap and peer-review policy for benchmark labels
- `examples/public_express_benchmark_profile.yaml`: pinned public Express example profile

## CLI

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
developable-rest-express validate-profile examples/public_express_benchmark_profile.yaml
developable-rest-express prepare-profile tests/fixtures/profiles/local_profile.yaml
developable-rest-express prepare-benchmark tests/fixtures/benchmarks/local_benchmark.yaml
developable-rest-express analyze-profile tests/fixtures/profiles/local_profile.yaml --output md
developable-rest-express evaluate-benchmark tests/fixtures/benchmarks/local_benchmark.yaml --output both
developable-rest-express score-demo
```

`prepare-profile`, `prepare-benchmark`, `analyze-profile`, and `evaluate-benchmark` accept `--cache-root` if you want the GitHub checkout cache somewhere other than the default `.developable-rest-express/cache/repos/`.

Run the local test suite with:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

## Current Express convention targets

V1 analyzes these deterministic convention targets:

- `route_declaration_style`
- `route_controller_boundary`
- `validation_at_edge_pattern`
- `service_repository_layering`
- `auth_middleware_presence`
- `test_layout_shape`

## Design principles

### Convention profile

A company should not point this at every repo it has. A profile is a bounded unit of inference for one coherent engineering style, such as `public-express-v1`.

### Confidence

Confidence scores are predictions, not vibes. The first heuristic weights are only a starting point. Over time, those weights should be learned and calibrated against labeled benchmark data.

### Safety

High-confidence conventions can influence automated suggestions and generated guidance. Low-confidence conventions should remain explain-only until they are validated.

## Public GitHub repo testing

The recommended V1 workflow is:

1. use a full commit SHA for every public benchmark repository
2. create a benchmark fixture with explicit, human-reviewed convention labels
3. run `prepare-benchmark` and confirm requested/resolved revisions match
4. inspect the JSON/Markdown output and correct bad expectations or weak detectors

The checked-in public corpus is opt-in locally because it clones external repositories. The public GitHub Actions workflow runs it weekly and on manual dispatch. See [CONTRIBUTING.md](CONTRIBUTING.md) for the exact command and label-review rules.

See [docs/public-benchmarking.md](docs/public-benchmarking.md) for a step-by-step process and candidate public repos.

## Near-term roadmap

1. Add richer benchmark fixtures and calibration datasets.
2. Improve Express detectors and repo-level aggregation logic.
3. Add framework adapters for NestJS, FastAPI, and Spring Boot.
4. Learn/calibrate scoring weights from labeled repo data.
5. Add emitters for MCP configs, skills, and repo-facing artifacts after benchmark quality is good enough.
