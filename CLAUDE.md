# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working agreement

This repository was previously maintained with Codex. The following constraints are set by the maintainer and override default behaviour.

1. **Propose, do not apply.** Discuss the change first, then hand over the code so the maintainer applies it manually. Do not edit source files unless explicitly asked to.
2. **Object-oriented, SOLID, YAGNI.** New functionality belongs in cohesive classes with one reason to change. Do not add abstraction for hypothetical future frameworks: Express is the permanent, exclusive scope, so there is no second adapter to design for. Build a seam only when a second consumer actually exists.
3. **No long parameter lists.** Pass a value object instead. The removed `_build_assessment` (11 keyword-only parameters) is the anti-pattern; `detectors/*.py` now pass a frozen `<Name>Signals` dataclass and no function in the package exceeds 4 parameters.
4. **Google-style docstrings; comments are a smell.** If a mid-function comment feels necessary, extract the block into a named method instead. Do not write filler prose, restate the signature, or annotate obvious lines.
5. **Straight control flow.** A reader should follow one path from CLI entry to rendered report. Avoid layered indirection, callback chains, and deep conditional nesting.

## What this project is

A **Python** library and CLI that statically analyzes **Express/Node.js** repositories and infers their engineering conventions with an explicit confidence score. Express is the subject of analysis, not the implementation language — there is no JavaScript source in this repo outside `tests/fixtures/repos/`.

**Express is the permanent, exclusive scope.** Not other Node frameworks, not other languages. A NestJS or FastAPI harness would be a separate library with its own corpus, labels, and baseline — never an adapter registered here. The eventual output is MCP servers and assistive agents for developing on Express.

V1 deliberately stops at *evidence → heuristic score → benchmark report*. MCP config, skill, and guidance emission are future work and are not authorized until benchmark accuracy is consistently useful (`docs/benchmarks/public-express-v1-baseline.md`).

The credibility claim rests on one rule: **benchmark labels are human-authored from source inspection at a pinned SHA and are never derived from analyzer output.**

## Commands

```bash
# Setup (Python >= 3.11)
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -e .

# Full offline suite (19 tests; the public-benchmark test skips by default)
python -m unittest discover -s tests -p 'test_*.py' -v

# One test
python -m unittest tests.test_developable_rest_express.DevelopableRestExpressTests.test_benchmark_evaluation_and_reports

# Regenerate the detector golden — only when an accuracy change is intended
DEVELOPABLE_REGENERATE_DETECTOR_GOLDEN=1 python -m unittest tests.test_detector_characterization

# Opt-in: clones 34 external repos, slow
DEVELOPABLE_RUN_PUBLIC_BENCHMARK=1 python -m unittest discover -s tests -p 'test_public_benchmark.py' -v
```

CLI (`developable-rest-express <command>`; all repo commands accept `--cache-root`, all report commands accept `--output json|md|both`):

```bash
developable-rest-express validate-profile examples/public_express_benchmark_profile.yaml
developable-rest-express prepare-profile   tests/fixtures/profiles/local_profile.yaml
developable-rest-express prepare-benchmark tests/fixtures/benchmarks/local_benchmark.yaml
developable-rest-express analyze-profile   tests/fixtures/profiles/local_profile.yaml --output md
developable-rest-express evaluate-benchmark tests/fixtures/benchmarks/local_benchmark.yaml --output both
developable-rest-express export-calibration-dataset benchmarks/public/express_v1.yaml --output-path benchmarks/public/calibration/express_v1.jsonl
developable-rest-express run-calibration-experiment  benchmarks/public/calibration/express_v1.jsonl --output md
developable-rest-express score-demo
```

No formatter or linter is configured. CI (`.github/workflows/ci.yml`) runs only the unittest suite on Python 3.11. The public benchmark runs weekly via `.github/workflows/public-benchmark.yml` and uploads JSON/Markdown reports as artifacts.

## Architecture

Five stages, each isolated in its own module. Data crosses stage boundaries only as Pydantic models from `models.py`.

| Stage | Module | Responsibility |
| --- | --- | --- |
| Load | `profile_loader.py`, `benchmark_loader.py`, `governance.py` | YAML → validated model; benchmark loading also enforces label-review policy |
| Materialize | `workspace.py` | Resolve local paths, clone/cache GitHub repos at an exact SHA, verify provenance, fingerprint framework/language |
| Detect | `detectors/` | Six `Detector` subclasses, one per file; `snapshot.py` owns every filesystem read |
| Score | `scoring.py` | The only place weights and thresholds live |
| Report | `reporting.py`, `evaluation.py`, `calibration.py` | JSON/Markdown rendering, label comparison, offline calibration experiment |

Dependencies are `pydantic` and `PyYAML` only. `calibration.py` implements logistic regression on stdlib `math` on purpose — do not introduce numpy/scikit-learn to "clean it up".

### Workflow 1 — `analyze-profile` (inference, no ground truth)

```
cli.main()
  -> cli.run_analyze_profile()
  -> profile_loader.load_profile(path)                       -> ConventionProfile   (Pydantic validates)
  -> analysis.analyze_profile(profile, path)
       -> workspace.prepare_profile()
            -> workspace._prepare_repo_groups()              # reference / context / evaluation groups
                 -> workspace.prepare_repo_reference()       # once per repo
                      -> _resolve_local_source() | _prepare_github_repo()   # git clone --no-checkout + checkout --detach
                      -> _cache_matches()                    # canonical origin + SHA provenance check
                      -> fingerprint_repo()                  -> (framework, language)
                      -> resolve_commit_sha()                -> RepoHandle
       -> detectors.analyze_repo(handle)                     # skipped unless framework == "express"
            -> RepoSnapshot(root)                            # one walk; caches file text, imports, package roots
            -> for detector in DETECTORS:                    # six subclasses, declaration order
                 detector.assess(repo, snapshot)             # base.Detector template method
                   -> detector.detect(snapshot)
                        -> _gather(snapshot)                 -> <Name>Signals  (frozen dataclass)
                        -> _classify(signals)                -> Classification
                           or first_match(RULES, signals, fallback)
                        -> _metrics(...)                     -> DetectorMetrics
                        -> _evidence(signals)                -> tuple[str, ...]
                                                             -> DetectorFinding
                   -> Detector._build_evidence()             -> ConventionEvidence
                        # base owns repo_quality, coverage, conflict_penalty,
                        # and the supported / ambiguous flags
                   -> scoring.assess_convention()
                        -> compute_signal_strength()
                        -> compute_confidence()
                        -> bucket_confidence()               -> ConventionAssessment
       -> RepoAnalysis per repo                              -> AnalysisReport
  -> reporting.render_analysis_json() / render_analysis_markdown()
  -> reporting.render_output_bundle()                        -> stdout
```

### Workflow 2 — `evaluate-benchmark` (inference measured against human labels)

Identical from `prepare_*` onward; it diverges at load and at the tail.

```
cli.main()
  -> cli.run_evaluate_benchmark()
  -> benchmark_loader.load_benchmark(path)                   -> BenchmarkFixture
       -> governance.find_governance_path()                  # walks parents for benchmark-governance.yaml
       -> governance.validate_benchmark_review()             # author/reviewer vs review_mode
  -> evaluation.evaluate_benchmark(fixture, path)
       -> workspace.prepare_benchmark()                      # require_remote_revision=True: GitHub repos MUST be SHA-pinned
       -> detectors.analyze_repo()                           # same detector path as Workflow 1
       -> compare each assessment to ConventionExpectation   -> ComparisonResult (matched / confidence / bucket)
       -> aggregate accuracy-by-convention, precision-by-bucket, false positives/negatives
                                                             -> EvaluationResult
  -> reporting.render_evaluation_json() / render_evaluation_markdown() -> stdout
```

Two offshoots reuse the same spine: `export-calibration-dataset` runs `evaluation.export_calibration_rows()` to emit one JSONL row per (repo, convention) with raw detector metrics; `run-calibration-experiment` feeds those rows to `calibration.run_repository_grouped_logistic_experiment()`, which does leave-one-repository-out validation and compares its Brier score against the heuristic. That experiment is explicitly **non-operational** (`"operational": False`) and must not feed product confidence.

## Domain rules that constrain changes

- **SHA pinning is absolute.** Benchmark GitHub repos require a full 40-character lowercase SHA (`RepoReference.finalize`). If a resolved `HEAD` differs from the request, `prepare_repo_reference` raises rather than proceeding. Never point a benchmark at a branch or tag; never auto-refresh a pin.
- **Pins survive upstream force-pushes.** `_prepare_github_repo` runs `git fetch origin <revision>` between clone and checkout, because a clone only downloads objects reachable from refs and a force-push orphans the pinned commit. A `fatal: reference is not a tree` failure means that fetch was skipped, never that the corpus entry is stale — do not re-pin in response to it.
- **Governance gates labels.** `benchmark-governance.yaml` is currently `bootstrap_self_review` with a single maintainer, so author and reviewer may match. Switching to `peer_review` requires distinct author/reviewer, both in the maintainer list. Fixture `review.review_mode` must equal the governance mode.
- **Confidence is heuristic, not calibrated.** `agreement` is fed by the detector *and* contributes to `signal_strength`, so scores double-count by design (`docs/scoring.md`). Buckets: `>=0.85` high, `>=0.65` medium, `>=0.40` low, else `do_not_operationalize`. Changing weights or thresholds invalidates the committed baseline — rerun the benchmark and record the delta.
- **Adding a seventh convention target touches everything.** `ConventionTarget` (literal), `ConventionExpectation` (all fields required), a new `Detector` subclass file registered in `detectors/__init__.py::DETECTORS`, every one of the 63 entries in `benchmarks/public/express_v1.yaml` plus the test fixtures, the golden in `tests/fixtures/golden/`, and the hardcoded `len(fixture.repos) * 6` assertion in `tests/test_public_benchmark.py`. Confirm the maintainer wants that blast radius first.
- **Corpus admission has a written policy.** `docs/benchmarks/public-corpus-policy.md` — public, non-fork, non-archived Express *application*, one of five allowed SPDX licenses, SHA-pinned, with a diversity rationale. No third-party source checkouts are committed.

## Current progress

Read `docs/benchmarks/` for state; it is the running log.

- Corpus: 63 SHA-pinned public repos, 378 reviewed convention rows (batch 04 admitted 2026-08-31).
- Batch 04's 29 repos are **training data**; eleven repos named in `changes/2026-08-31-layering-detector-redesign.md` are **held out** for validation.
- On the 63-repo corpus: `service_repository_layering` 0.57 and `route_declaration_style` 0.65 are weakest; `route_controller_boundary` is 0.83 after the 2026-08-31 vocabulary fix. Clean/hexagonal layering is the main remaining gap.
- Strongest: `test_layout_shape` 0.94 and `auth_middleware_presence` 0.90.
- The layering redesign landed 2026-08-31: `service_repository_layering` 0.57 -> 0.83 via a role census, ORM call-site signals, and comparison-based rules.
- Current accuracy (63 repos): `route_declaration_style` 0.65 is weakest, then `validation_at_edge_pattern` 0.73; boundary and layering both 0.83; auth 0.90; test layout 0.94. Mean 0.81.
- Confidence buckets: high 143 rows at 0.9091, medium 160 at 0.7875, low 75 at 0.6800.
- Next planned step: `changes/2026-09-01-route-declaration-accuracy.md`. Merge `detector-accuracy-and-batch-04` first — `main` still lacks the revision fetch and its scheduled benchmark fails without it.
- Tuning discipline: 52 repos are training data, 11 are held out (listed in `changes/2026-08-31-layering-detector-redesign.md`). Measure on training only; open the holdout once, at the end.


## Detector package conventions

The detectors were refactored from a single 550-line module into `detectors/`, then flattened out of `adapters/` when the Express-only scope was made explicit. Follow the resulting shape when touching them.

**Import direction is one-way and load-bearing.**

```
__init__.py  ->  <detector>.py  ->  base.py
                 <detector>.py  ->  snapshot.py  ->  base.py
```

A detector must never import from `__init__.py`, and `base.py` must never import `snapshot` at runtime -- `snapshot` needs `ratio` from `base`, so the `if TYPE_CHECKING:` guard around `from .snapshot import RepoSnapshot` is required, not stylistic. Use relative imports, and mind the depth: `detectors/` sits directly under the package root, so it is `from ..models import`, not `...`. An absolute `from developable_rest_express.detectors import X` hides the direction. Detectors do not import each other; a small duplicated helper is preferred over cross-detector coupling.

**Detector anatomy.** Each subclass declares `convention_name` and `unsupported_values`, and implements `detect()` returning a `DetectorFinding` assembled from four private helpers: `_gather` (signals), `_classify` or `first_match` (conclusion), `_metrics`, `_evidence`. The base owns `repo_quality`, `coverage`, `conflict_penalty`, and the `supported` / `ambiguous` flags -- never set those in a subclass. Conflicts go in the `Classification`; the base derives the penalty.

`ambiguous_values` defaults to `unsupported_values`. Only `route_declaration` overrides it: `mixed_routes` is supported *and* ambiguous.

**Rule tables vs conditionals.** `test_layout`, `route_declaration`, and `service_repository_layering` use an ordered `Rule` table resolved by `first_match`; the three shorter detectors use plain `if`/`elif`. Both expose the same `Classification`-returning shape. Where a branch's ambiguity depends on signals, split it into narrower rules rather than teaching `Rule` about callables. Where a conflict depends on a signal the guard does not test (`flat_handlers`), apply it after matching with `dataclasses.replace`.

**Two notions of relative path.** `RepoSnapshot.directory_count()` measures from each file's nearest ancestor `package.json`; `RepoSnapshot.relative_parts()` measures from the snapshot root. They agree only while no corpus repo is a monorepo. Do not unify them.

**Value objects use stdlib `dataclasses`, frozen.** Pydantic models belong in `models.py`, where they cross stage boundaries. A one-element `conflicts` tuple needs its trailing comma.

**Verification.** `tests/test_detector_characterization.py` pins all 54 fixture assessments to `tests/fixtures/golden/express_assessments.json`. Regenerate it only when an accuracy change is intended, never to make a failing assertion pass. `.github/workflows/public-benchmark.yml` re-exports the calibration dataset and diffs it against the committed 378-row `benchmarks/public/calibration/express_v1.jsonl` -- that is the corpus-wide guard.

## Known deviations from the working agreement

Written by the previous toolchain; treat as debt to pay down when touching the area, not as precedent. The detector entries were cleared by the decomposition refactor; these are what remain.

- `evaluation.py::evaluate_benchmark` is a 93-line function that prepares repos, compares against labels, aggregates four different metrics, and builds the result. It is the clearest remaining candidate for the same treatment the detectors got, but note it has no characterization net — the golden covers detectors, not evaluation, so it would need its own step 0.
- `reporting.py::render_evaluation_markdown` is 79 lines of sequential `lines.extend` blocks; `render_analysis_markdown` is 41. Both are line-buffer accumulation rather than composed section renderers.
- `cli.py` uses function-local `import json` in four handlers and dispatches through a flat `if` chain in `main()`.
- `workspace.py::prepare_repo_reference` takes 5 parameters and runs 51 lines; `_prepare_github_repo` takes 4. The module is otherwise plain functions over one exception class.
- `calibration.py` is deliberately stdlib-only maths; its 5-parameter `_fit_regularized_logistic` is inherent to the algorithm and is not worth restructuring.
