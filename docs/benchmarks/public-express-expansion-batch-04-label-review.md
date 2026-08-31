# Public Express expansion — batch 04 label review

Admitted 2026-08-31. The corpus grows from 34 to 63 SHA-pinned repositories and from 204 to 378
reviewed convention rows.

## Admission

All 30 candidates from [the scout queue](public-express-expansion-batch-04-scouting.md) passed the
objective checks in `public-corpus-policy.md`: publicly accessible, non-fork, non-archived, an allowed
SPDX licence, and a scout SHA that still resolves. None overlapped the existing corpus.

**One candidate was excluded.** `zarif007/ez-node-ts-express-mongoose-boilerplate` is not an
application. Its `src/` holds only `app.ts`, `server.ts`, configuration, shared helpers, error handlers
and two middlewares; the controllers, services, models and routes are emitted by `module-generator.js`
at scaffold time. The policy excludes generated-only examples, so it was not labelled.

The remaining 29 were labelled from source inspection at their pinned SHAs, with the evidence for each
label recorded alongside it.

## Train / test split

Batch 04 repositories are **training data**. The eleven repositories designated in
`changes/2026-08-31-layering-detector-redesign.md` remain **held out** for validation.

The split exists because the same process now authors both labels and detector rules. Keeping the
validation set to repositories labelled before that arrangement is what stops the measurement from
becoming self-confirming.

## Coverage gained

| `service_repository_layering` | count |
| --- | ---: |
| controller_service_model | 9 |
| controller_model | 5 |
| clean_architecture_ports | 5 |
| controller_service_repository | 3 |
| service_data_access | 2 |
| flat_handlers, repository_only, feature_service_layer, controller_repository, layering_unclear | 1 each |

The material gain is **clean architecture**: from one example corpus-wide to six, reached by four
distinct routes — CQRS with a DI container, explicit ports and adapters, presentation/domain/data, and
DDD application/domain/infrastructure. One example was an anecdote; six is enough to design against.

`route_declaration_style` gains four more `feature_router_modules` and two `inline_app_routes`, both
previously thin.

## Judgement calls, recorded

Three labels rest on inference rather than a direct read, and were confirmed by the maintainer:

- **israelmuca/express-i18n-api → `layering_unclear`.** It has `src/controller` and no data layer at
  all. The sentinel means "no usable signal"; the truth here is "no layering exists to have a
  convention about". The vocabulary has no value for that distinction.
- **mrmovas/Express-BetterAuth-Boilerplate → `route_validation_middleware`.** A purpose-built zod
  `validation.middleware.ts` exists but is not wired to either route. The label records the convention,
  not the wiring.
- **eldimious/nodejs-api-showcase → `routes_call_services`.** Route modules import both repositories
  and services; the repositories are constructor arguments injected into the services, so the service
  is the boundary.

## Effect on measured accuracy

Accuracy falls on the larger corpus, which is the expected direction and not a regression:

| Convention | 34 repos | 63 repos |
| --- | ---: | ---: |
| route_declaration_style | 0.7647 | 0.6508 |
| route_controller_boundary | 0.9118 | 0.8254 |
| validation_at_edge_pattern | 0.7353 | 0.7302 |
| service_repository_layering | 0.6471 | 0.5714 |
| auth_middleware_presence | 0.9412 | 0.9048 |
| test_layout_shape | 0.9412 | 0.9365 |
| **mean** | **0.8236** | **0.7699** |

The 34-repo figures were partly fitted to that corpus. The 63-repo figures are the honest baseline.

**One caveat on the held-out numbers.** The eleven held-out repositories were part of the 34 that the
route-boundary vocabulary was tuned against earlier on 2026-08-31, so the held-out boundary figure of
1.0000 is optimistic and should not be read as clean validation of that change. The holdout *is* clean
for the layering redesign, which has not been tuned against any corpus.
