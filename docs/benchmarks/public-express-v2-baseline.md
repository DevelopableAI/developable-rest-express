# Public Express V2 baseline

The V2 baseline is [Public Benchmark run 33436574252](https://github.com/DevelopableAI/developable-rest-express/actions/runs/33436574252),
dispatched on 2026-08-31 against branch `detector-accuracy-and-batch-04`. Every step passed, including
the calibration assertion, so the uploaded `public-express-benchmark` artifact is the authoritative
JSON and Markdown report.

It supersedes [the V1 baseline](public-express-v1-baseline.md), which measured 6 repositories and 36
conventions and has been out of date since the batch 01 expansion.

## Corpus

63 SHA-pinned public repositories, 378 human-reviewed convention rows.

Batch 04's 29 repositories are **training data**. Eleven repositories, named in
`changes/2026-08-31-layering-detector-redesign.md`, are **held out** for validation.

## Exact-match accuracy

| Convention | Overall | Training (52) | Held out (11) |
| --- | ---: | ---: | ---: |
| route_declaration_style | 0.6508 | 0.6346 | 0.7273 |
| route_controller_boundary | 0.8254 | 0.7885 | 1.0000 |
| validation_at_edge_pattern | 0.7302 | 0.7115 | 0.8182 |
| service_repository_layering | 0.5714 | 0.5577 | 0.6364 |
| auth_middleware_presence | 0.9048 | 0.9038 | 0.9091 |
| test_layout_shape | 0.9365 | 0.9423 | 0.9091 |
| **mean** | **0.7699** | | |

Precision by confidence bucket: high `0.9265`, medium `0.7125`, low `0.6220`.
44 ambiguous repositories, 68 unsupported conventions, 55 false positives, 32 false negatives.

## Reading these numbers honestly

**This is not comparable to V1.** V1 measured 6 repositories. Comparing 0.7699 against any V1 figure
compares two different corpora, not two versions of the analyzer.

**It is lower than the last 34-repo measurement, on purpose.** The same code scored a mean of 0.8236
across 34 repositories on 2026-08-31 before batch 04 landed. Those figures were partly fitted to that
corpus, including a route-boundary vocabulary chosen by testing variants against it. 0.7699 across 63
repositories is the honest number.

**The held-out column is not yet clean for every convention.** The eleven held-out repositories were
part of the 34 that the route-boundary vocabulary was tuned against earlier the same day, so the
held-out figure of 1.0000 for `route_controller_boundary` is optimistic and must not be cited as
independent validation. The holdout *is* clean for `service_repository_layering`, which has never been
tuned successfully against any corpus, and for any future change measured against it first.

## What changed since the last measurement

Two detector changes landed before this run, both cases of one component lacking vocabulary another
component in the package already had:

- `RepoSnapshot._declares_routes` now accepts `routers/`, a bare `Router()`, and
  `@Controller` / `@JsonController`. Repositories using decorator routing previously reported zero
  route files, starving every detector that reads them.
- `route_controller_boundary` gained the shared `DATA_ACCESS_MARKERS` and now classifies each import
  into exactly one role, testing data access first, so a module at `services/db.js` counts as data
  access rather than as a service.

On the 34-repo corpus those moved `route_controller_boundary` from 0.7059 to 0.9118 and
`route_declaration_style` from 0.7353 to 0.7647.

## Standing gate

MCP and skill emission remain unauthorized. `service_repository_layering` at 0.5714 is the binding
constraint; the redesign that addresses it is planned in
`changes/2026-08-31-layering-detector-redesign.md` and must be validated on the held-out set rather
than on the corpus it is fitted to.
