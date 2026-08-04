# Architecture

## Core idea

`developable-rest-express` is an evaluation-first harness for inferring conventions from bounded sets of Express REST repositories. It currently stops at evidence, heuristic scoring, and benchmark reports; MCP and skill emission remain future work.

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

### 3. Adapter layer

Framework-aware logic lives here.

Expected first adapters:
- Express + TypeScript
- NestJS
- FastAPI
- Spring Boot

Adapters should expose small deterministic capabilities rather than giant inference blobs.

### 4. Detector layer

Each detector should answer one narrow question, such as:
- how routes are declared
- whether validation lives at the edge
- how auth is propagated
- whether repository access bypasses service layers

Detectors should emit structured evidence instead of conclusions only.

V1 detectors are implemented only for Express repos and cover:
- route declaration style
- route/controller boundary
- validation at the route edge
- service/repository layering
- auth middleware presence
- test layout shape

### 5. Scoring layer

Consumes evidence and predicts confidence.

Important rule:
- raw weights can start heuristic
- production confidence should eventually be calibrated against benchmark truth

### 6. Evaluation layer

This is what makes the project credible. Benchmark truth is manually authored and is never inferred from detector output.

Responsibilities:
- benchmark fixtures
- requested and resolved revision provenance
- bootstrap self-review and peer-review governance
- held-out repo evaluation
- precision/recall by convention type
- reliability diagrams and calibration metrics
- threshold tuning for operational buckets

### 7. Emission layer

Generates the actual artifacts for AI tooling.

Possible outputs:
- MCP config and tool manifests
- skill instructions for Codex / Claude Code
- repo guidance markdown
- machine-readable convention reports

## V1 implementation scope

V1 currently supports:
- local-path and GitHub profile preparation
- SHA-pinned public benchmark preparation
- Express-only deterministic convention assessments
- JSON and Markdown reports with review and revision provenance
- offline fixture tests plus opt-in public integration tests

## Non-goals for V1

- multi-framework code parsing
- live MCP server generation
- LLM orchestration
- enterprise auth or hosted control planes
