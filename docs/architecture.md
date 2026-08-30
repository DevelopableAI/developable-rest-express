# Architecture

## Core idea

`developable-rest-express` is an evaluation-first harness for inferring conventions from bounded sets of Express REST repositories. Express is its permanent and exclusive scope. It currently stops at evidence, heuristic scoring, and benchmark reports; MCP and skill emission remain future work.

The architecture should separate:

- profile and benchmark definition
- immutable repo materialization
- deterministic detection
- confidence scoring
- calibration and evaluation
- artifact emission

## Recommended module boundaries

### 1. Profile layer

Defines the unit of ingestion.

Responsibilities:
- profile schema validation
- reference vs context repo separation
- safety and output target configuration

### 2. Workspace layer

Handles local paths, GitHub checkouts, and provenance.

V1 responsibilities:
- local repo registration
- GitHub checkout caching
- full-SHA detached checkout for public benchmarks
- cache validation against canonical origin and resolved `HEAD`
- repo snapshots
- language/framework fingerprints
- held-out evaluation manifests

### 3. Detector layer

All Express-aware logic lives in `developable_rest_express/detectors/`. There is no adapter
indirection, because there will never be a second framework: another framework would be a separate
library with its own corpus, labels, and baseline, not a plugin registered here.

`snapshot.py` owns every filesystem read and caches file text, imports, and package roots.
`base.py` owns the `Detector` contract and all scoring plumbing. Each detector module answers one
narrow question, such as:
- how routes are declared
- whether validation lives at the edge
- how auth is propagated
- whether repository access bypasses service layers

Detectors emit structured evidence rather than conclusions only, and never compute their own
confidence: they return a finding, and `base.Detector` hands it to the scorer.

The implemented detectors cover:
- route declaration style
- route/controller boundary
- validation at the route edge
- service/repository layering
- auth middleware presence
- test layout shape

### 4. Scoring layer

Consumes evidence and predicts confidence.

Important rule:
- raw weights can start heuristic
- production confidence should eventually be calibrated against benchmark truth

### 5. Evaluation layer

This is what makes the project credible. Benchmark truth is manually authored and is never inferred from detector output.

Responsibilities:
- benchmark fixtures
- requested and resolved revision provenance
- bootstrap self-review and peer-review governance
- held-out repo evaluation
- precision/recall by convention type
- reliability diagrams and calibration metrics
- threshold tuning for operational buckets

### 6. Emission layer

Not built, and not authorized until benchmark accuracy is consistently useful.

It will consume a scored `AnalysisReport` -- the same model `reporting.py` already renders -- and is
therefore a second family of renderers rather than a new pipeline stage. Emission must be gated on
confidence buckets so that only `high` and `medium` conventions can influence generated tooling and
`low` stays explain-only.

Intended outputs:
- MCP server config and tool manifests
- skill instructions for coding agents
- repo guidance markdown
- machine-readable convention reports

## V1 implementation scope

V1 currently supports:
- local-path and GitHub profile preparation
- SHA-pinned public benchmark preparation
- Express-only deterministic convention assessments
- JSON and Markdown reports with review and revision provenance
- offline fixture tests plus opt-in public integration tests

## Non-goals

- any framework other than Express, permanently
- live MCP server generation
- LLM orchestration
- enterprise auth or hosted control planes
