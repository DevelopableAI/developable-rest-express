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
| service_repository_layering | 0.8254 | 0.8462 | 0.7273 |
| auth_middleware_presence | 0.9048 | 0.9038 | 0.9091 |
| test_layout_shape | 0.9365 | 0.9423 | 0.9091 |
| **mean** | **0.8122** | | |

Precision by confidence bucket: high `0.9091`, medium `0.7875`, low `0.6800`.
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

## Layering redesign

`service_repository_layering` was redesigned on 2026-08-31 after this baseline was first recorded,
moving from 0.5714 to 0.8254 overall (training 0.8462, held out 0.7273) with no other convention
changing by a single repository. Layer membership now comes from per-file role assignment rather than
directory presence, repository layers that exist only as ORM call sites are detected, and the rules run
narrow to broad with magnitude comparisons. See
`changes/2026-08-31-layering-detector-redesign.md`.

The table above reflects the redesigned detector.

### On the train/holdout gap

The held-out estimate is 0.7273 with a standard error of +/- 0.1343 on eleven repositories. It moved in
the same direction as the training subset, so the changes generalise rather than merely memorise.

**The train/holdout difference is not evidence of overfitting.** Holding the label author constant and
varying only whether the repository was tuned against gives 0.8261 (23 repositories, tuned) versus
0.7273 (11, not tuned) -- a difference of 0.63 standard errors, and worth about 1.1 repositories, since
one repository moves an 11-repository set by 0.0909. Labels authored during batch 04 score 0.8621
against 0.8261 for the original labels on equally-tuned repositories, so label provenance is not
driving the number either.

A fitting procedure was used -- roughly five accept-if-training-improves decisions over 52
repositories -- so some overfitting is plausible a priori. It simply has not been observed. An
eleven-repository holdout can catch a catastrophic overfit, where held-out accuracy falls while
training rises, but it cannot adjudicate a gap this size in either direction. Growing it is the fix.

## Standing gate

MCP and skill emission remain unauthorized. `route_declaration_style` at 0.6508 is now the weakest
convention and the binding constraint.
