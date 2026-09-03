# Public Express V2 baseline

The V2 baseline is [Public Benchmark run 33805790142](https://github.com/DevelopableAI/developable-rest-express/actions/runs/33805790142),
dispatched on 2026-09-03 against `main` at 9c509ec. Every step passed, including the calibration
assertion, so the uploaded `public-express-benchmark` artifact is the authoritative JSON and Markdown
report. It replaces run 33436574252 of 2026-08-31, whose figures predate the route declaration work
recorded below.

It supersedes [the V1 baseline](public-express-v1-baseline.md), which measured 6 repositories and 36
conventions and has been out of date since the batch 01 expansion.

## Corpus

63 SHA-pinned public repositories, 378 human-reviewed convention rows.

Batch 04's 29 repositories are **training data**. Eleven repositories, named in
`changes/2026-08-31-layering-detector-redesign.md`, are **held out** for validation.

## Exact-match accuracy

| Convention | Overall | Training (52) | Held out (11) |
| --- | ---: | ---: | ---: |
| route_declaration_style | 0.8254 | 0.8462 | 0.7273 |
| route_controller_boundary | 0.8254 | 0.7885 | 1.0000 |
| validation_at_edge_pattern | 0.7302 | 0.7115 | 0.8182 |
| service_repository_layering | 0.8254 | 0.8462 | 0.7273 |
| auth_middleware_presence | 0.9048 | 0.9038 | 0.9091 |
| test_layout_shape | 0.9365 | 0.9423 | 0.9091 |
| **mean** | **0.8413** | | |

Precision by confidence bucket: high `0.9216` (153 rows), medium `0.8400` (150), low `0.6800` (75).
36 ambiguous repositories, 58 unsupported conventions, 38 false positives, 22 false negatives.

## Reading these numbers honestly

**This is not comparable to V1.** V1 measured 6 repositories. Comparing 0.8413 against any V1 figure
compares two different corpora, not two versions of the analyzer.

**Nor is it comparable to the 34-repo measurement.** The same code scored a mean of 0.8236 across 34
repositories on 2026-08-31 before batch 04 landed. The current 0.8413 across 63 repositories is higher,
but that is not a like-for-like improvement: the 34-repo figures were partly fitted to that corpus,
including a route-boundary vocabulary chosen by testing variants against it. Only the 63-repo figure
should be quoted.

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

## Route declaration accuracy

`route_declaration_style` moved from 0.6508 to 0.8254 overall (training 0.6346 -> 0.8462) on
2026-09-03, with no other convention changing by a single row. Five changes, each measured separately
against the training subset; see `changes/2026-09-01-route-declaration-accuracy.md`.

- `ROUTER_ROUTE_PATTERN` counts any `*Router` receiver, not the literal identifier `router`.
- `APP_ROUTE_PATTERN` no longer matches `res.app.get()`, which reads an Express setting rather than
  declaring a route.
- `ROUTE_CHAIN_PATTERN` counts `router.route('/x')` chains, which were previously invisible.
- `_router_modules_lead` gained an incidental-app-routes arm, so a health endpoint beside genuine
  router modules is not read as mixing styles.
- `_is_feature_router` matches a `route` stem rather than `router`, and recognises `components/`.

### The held-out column did not move

All eleven held-out rows are byte-identical before and after: the same three misses, with the same
inferred values. Training rose 0.2116 and the holdout rose 0.0000. Nothing regressed, so this is not
the catastrophic overfit an eleven-repository holdout can detect, but it is also no positive evidence
of generalisation.

The one testable prediction available came back negative. `h3nrzi` was named in the plan as the
held-out member of Family B, the family the feature-router widening targeted. The widening fixed five
training repositories of that family and did not fix `h3nrzi`, whose feature directory is named `core`
and therefore falls outside the four-name allowlist. `steve-lebleu` remains a false positive because
`router.class.ts` and `proxy-router.service.ts` match on stem while being framework infrastructure;
that predates these changes, but widening the stem to `route` enlarges the surface for it.

Neither was fixed. The holdout was spent as validation the moment it was read, and tuning against it
afterwards would convert it into a second training set.

**Directory allowlists are the structural weakness.** `FEATURE_DIRECTORIES` now holds four names and
`h3nrzi` needs a fifth. Every new repository can extend it, which is a sign the rule is enumerating
instances rather than recognising a shape.


## Standing gate

MCP and skill emission remain unauthorized **as a blanket capability**. `validation_at_edge_pattern`
at 0.7302 is now the weakest convention, having displaced `route_declaration_style`.

### Reassessing a high-confidence-only emitter

The high bucket now carries 153 of 378 rows at 0.9216 precision, up from 143 at 0.9091. Both the
count and the precision rose, which means the ten rows promoted into the bucket were well-evidenced
rather than borderline. That makes a high-confidence-only emitter more arguable than it was.

The aggregate hides a spread wide enough that it should not be gated on:

| Convention | High-bucket rows | Precision |
| --- | ---: | ---: |
| validation_at_edge_pattern | 19 | 1.0000 |
| test_layout_shape | 6 | 1.0000 |
| route_controller_boundary | 37 | 0.9730 |
| auth_middleware_presence | 40 | 0.9250 |
| route_declaration_style | 34 | 0.8824 |
| service_repository_layering | 17 | 0.7647 |

`service_repository_layering` is the blocker, and for a reason worth naming: it is the only convention
whose high-bucket precision (0.7647) is *worse* than its overall accuracy (0.8254). Its confidence is
inverted -- it is least reliable exactly where it claims most certainty. A blanket high-confidence
emitter would ship four confidently wrong layering judgements out of seventeen.

**Recommendation: gate per convention, not on the bucket alone.** Emission for a given repository and
convention requires `bucket == high` *and* the convention being one whose high-bucket precision has
been measured acceptable. On these figures that admits `validation_at_edge_pattern`,
`test_layout_shape`, `route_controller_boundary`, and `auth_middleware_presence` -- 102 rows at 0.9608
combined -- and excludes `service_repository_layering` outright.

Two caveats before acting on this. `test_layout_shape` has only 6 high-bucket rows, too few to
distinguish 1.0000 from 0.8000. And the calibration experiment in `calibration.py` remains explicitly
non-operational, so none of this is a calibrated probability: these are observed frequencies on one
63-repository corpus.
