# Public Benchmarking

This project’s V1 benchmark is a **convention inference benchmark**, not a language-model benchmark.

The goal is to measure whether `developable-rest-express` can inspect public Express repositories and infer a small set of architectural conventions with useful confidence and explainable evidence.

## Recommended workflow

1. Curate 6 to 12 public Express repos manually.
2. Split them into:
   - 3 to 5 reference-style repos for detector development
   - 3 to 7 held-out evaluation repos for reporting
3. Pin each repository to a full 40-character Git commit SHA.
4. Write a benchmark fixture with explicit, human-reviewed convention labels.
5. Run `developable-rest-express prepare-benchmark <fixture.yaml>` and confirm requested and resolved SHAs match.
6. Run `developable-rest-express evaluate-benchmark <fixture.yaml> --output both`.
7. Review mismatches, detector blind spots, and low-confidence patterns.

Each benchmark also records the label author, reviewer, review mode, date, and rationale. `benchmark-governance.yaml` starts in `bootstrap_self_review` for the sole maintainer; switch it manually to `peer_review` when another maintainer can review labels.

## Candidate public repos

The initial checked-in corpus uses these pinned, MIT-licensed repositories:

- [hagopj13/node-express-boilerplate](https://github.com/hagopj13/node-express-boilerplate)
- [OsamaShahid/node-express-typeorm-boilerplate](https://github.com/OsamaShahid/node-express-typeorm-boilerplate)
- [w3tecch/express-typescript-boilerplate](https://github.com/w3tecch/express-typescript-boilerplate)
- [santiq/bulletproof-nodejs](https://github.com/santiq/bulletproof-nodejs)
- [edwinhern/express-typescript](https://github.com/edwinhern/express-typescript)
- [kunalkapadia/express-mongoose-es6-rest-api](https://github.com/kunalkapadia/express-mongoose-es6-rest-api)

These are starting points only. Before using any repo in the benchmark, verify that:

- it is still public and accessible
- it is actually Express-based
- it is not a giant monorepo
- it has a readable project layout
- it is not mostly a toy CRUD sample

## What to label manually

For each repo, label:

- `route_declaration_style`
- `route_controller_boundary`
- `validation_at_edge_pattern`
- `service_repository_layering`
- `auth_middleware_presence`
- `test_layout_shape`

Those labels should be human-reviewed and explicit. Do not let the tool generate its own benchmark truth.

## Reproducibility and CI

`prepare-benchmark` clones a SHA-pinned repository into a SHA-specific cache directory, checks out the revision detached, and verifies both the canonical `origin` URL and resolved `HEAD`. The JSON and Markdown reports preserve this provenance.

Normal CI runs only offline fixture tests. The public benchmark workflow runs weekly and on manual dispatch, verifies every pinned checkout, and uploads JSON and Markdown reports. It currently reports accuracy without enforcing an accuracy threshold.

## Practical benchmark loop

Start with one or two repos and a very small fixture:

```bash
developable-rest-express validate-profile my_profile.yaml
developable-rest-express prepare-profile my_profile.yaml
developable-rest-express prepare-benchmark my_benchmark.yaml
developable-rest-express analyze-profile my_profile.yaml --output md
developable-rest-express evaluate-benchmark my_benchmark.yaml --output both
```

Then iterate:

- if the detector is wrong but confident, improve the heuristic
- if the detector is right but low-confidence, improve the evidence signals
- if the repo is truly mixed or unclear, keep the lower confidence and mark it as ambiguous rather than forcing a false clean answer

## What success looks like in V1

V1 is successful if:

- the benchmark fixture is easy to author and rerun
- public repos can be normalized into cache predictably
- Express detectors produce understandable evidence
- confidence buckets separate strong predictions from weak ones
- mistakes are visible enough to drive detector improvements
