# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working agreement

This repository was previously maintained with Codex. The following constraints are set by the maintainer and override default behaviour.

1. **Propose, do not apply.** Discuss the change first, then hand over the code so the maintainer applies it manually. Do not edit source files unless explicitly asked to.
2. **Object-oriented, SOLID, YAGNI.** New functionality belongs in cohesive classes with one reason to change. Do not add abstraction for hypothetical future frameworks — the roadmap names NestJS/FastAPI/Spring, but only build the seam when a second adapter is actually being written.
3. **No long parameter lists.** Pass a value object instead. `adapters/express.py::_build_assessment` (11 keyword-only parameters) is the anti-pattern to avoid, not to copy.
4. **Google-style docstrings; comments are a smell.** If a mid-function comment feels necessary, extract the block into a named method instead. Do not write filler prose, restate the signature, or annotate obvious lines.
5. **Straight control flow.** A reader should follow one path from CLI entry to rendered report. Avoid layered indirection, callback chains, and deep conditional nesting.

## What this project is

A **Python** library and CLI that statically analyzes **Express/Node.js** repositories and infers their engineering conventions with an explicit confidence score. Express is the subject of analysis, not the implementation language — there is no JavaScript source in this repo outside `tests/fixtures/repos/`.

V1 deliberately stops at *evidence → heuristic score → benchmark report*. MCP config, skill, and guidance emission are future work and are not authorized until benchmark accuracy is consistently useful (`docs/benchmarks/public-express-v1-baseline.md`).

The credibility claim rests on one rule: **benchmark labels are human-authored from source inspection at a pinned SHA and are never derived from analyzer output.**

## Commands

```bash
# Setup (Python >= 3.11)
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -e .

# Full offline suite (17 tests; the public-benchmark test skips by default)
python -m unittest discover -s tests -p 'test_*.py' -v

# One test
python -m unittest tests.test_developable_rest_express.DevelopableRestExpressTests.test_benchmark_evaluation_and_reports

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
| Detect | `adapters/express.py` | Six deterministic detectors emitting structured evidence, never conclusions-only |
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
       -> adapters.express.analyze_express_repo(handle)      # skipped unless framework == "express"
            -> RepoSnapshot(root)                            # single walk: code_files, test_files, route_files, package.json
            -> _detect_route_declaration_style()      \
               _detect_route_controller_boundary()     |
               _detect_validation_at_edge()            |-- six detectors, each ->
               _detect_service_repository_layering()   |
               _detect_auth_middleware()               |
               _detect_test_layout()                  /
                 -> _build_assessment()                      -> ConventionEvidence
                      -> scoring.assess_convention()
                           -> compute_signal_strength()
                           -> compute_confidence()
                           -> bucket_confidence()            -> ConventionAssessment
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
       -> adapters.express.analyze_express_repo()            # same detector path as Workflow 1
       -> compare each assessment to ConventionExpectation   -> ComparisonResult (matched / confidence / bucket)
       -> aggregate accuracy-by-convention, precision-by-bucket, false positives/negatives
                                                             -> EvaluationResult
  -> reporting.render_evaluation_json() / render_evaluation_markdown() -> stdout
```

Two offshoots reuse the same spine: `export-calibration-dataset` runs `evaluation.export_calibration_rows()` to emit one JSONL row per (repo, convention) with raw detector metrics; `run-calibration-experiment` feeds those rows to `calibration.run_repository_grouped_logistic_experiment()`, which does leave-one-repository-out validation and compares its Brier score against the heuristic. That experiment is explicitly **non-operational** (`"operational": False`) and must not feed product confidence.

## Domain rules that constrain changes

- **SHA pinning is absolute.** Benchmark GitHub repos require a full 40-character lowercase SHA (`RepoReference.finalize`). If a resolved `HEAD` differs from the request, `prepare_repo_reference` raises rather than proceeding. Never point a benchmark at a branch or tag; never auto-refresh a pin.
- **Governance gates labels.** `benchmark-governance.yaml` is currently `bootstrap_self_review` with a single maintainer, so author and reviewer may match. Switching to `peer_review` requires distinct author/reviewer, both in the maintainer list. Fixture `review.review_mode` must equal the governance mode.
- **Confidence is heuristic, not calibrated.** `agreement` is fed by the detector *and* contributes to `signal_strength`, so scores double-count by design (`docs/scoring.md`). Buckets: `>=0.85` high, `>=0.65` medium, `>=0.40` low, else `do_not_operationalize`. Changing weights or thresholds invalidates the committed baseline — rerun the benchmark and record the delta.
- **Adding a seventh convention target touches everything.** `ConventionTarget` (literal), `ConventionExpectation` (all fields required), a new detector registered in `analyze_express_repo`, every one of the 34 entries in `benchmarks/public/express_v1.yaml` plus the test fixtures, and the hardcoded `len(fixture.repos) * 6` assertion in `tests/test_public_benchmark.py`. Confirm the maintainer wants that blast radius first.
- **Corpus admission has a written policy.** `docs/benchmarks/public-corpus-policy.md` — public, non-fork, non-archived Express *application*, one of five allowed SPDX licenses, SHA-pinned, with a diversity rationale. No third-party source checkouts are committed.

## Current progress

Read `docs/benchmarks/` for state; it is the running log.

- Corpus: 34 SHA-pinned public repos, 204 reviewed convention rows.
- Weakest detectors per `express-v1-calibration-analysis.md`: `service_repository_layering` (0.65 accuracy) and `route_controller_boundary` (0.71). Clean/hexagonal architectures, request-handler boundaries, and direct ORM access are the known blind spots.
- Strongest: `auth_middleware_presence` and `test_layout_shape` (0.94 each).
- Next planned step: batch 04 corpus expansion — 30 scouted candidates await label review in `public-express-expansion-batch-04-scouting.md`. Those SHAs are scout pins, not benchmark truth.

## Known deviations from the working agreement

Written by the previous toolchain; treat as debt to pay down when touching the area, not as precedent.

- `adapters/express.py` is 550 lines of module-level functions with one class (`RepoSnapshot`). The six detectors are near-duplicates of each other and each ends in a long-signature `_build_assessment` call. This is the prime candidate for an OOP refactor: a `Detector` base with a small evidence-returning method per subclass.
- `_detect_service_repository_layering` is a ~90-line function with a fourteen-branch `if/elif` chain — the opposite of the straight control flow required above.
- `RepoSnapshot` caches file *lists* but not file *contents*; `_read()` re-reads every file from disk once per detector, and `_dir_count()` calls `_infer_repo_root()` (which stats the filesystem) once per path per call.
- `cli.py` uses function-local `import json` in four handlers and dispatches through a flat `if` chain in `main()`.
