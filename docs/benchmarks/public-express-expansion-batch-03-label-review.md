# Public Express expansion — batch 03 label review

These labels were approved on 2026-08-05 following source inspection at the SHA-pinned snapshots in [batch 03](public-express-expansion-batch-03.md).

| Repo | Route style | Route boundary | Validation | Layering | Auth | Test layout |
| --- | --- | --- | --- | --- | --- | --- |
| PhlexPlexico/G5API | `express_router_modules` | `routes_call_repositories` | `no_clear_validation` | `flat_handlers` | `auth_middleware_present` | `jest_supertest_layout` |
| alexleboucher | `express_router_modules` | `routes_call_controllers` | `controller_validation` | `clean_architecture_ports` | `auth_middleware_present` | `jest_supertest_layout` |
| cham11ng | `express_router_modules` | `routes_call_controllers` | `route_validation_middleware` | `controller_service_model` | `auth_middleware_present` | `jest_supertest_layout` |
| h3nrzi | `feature_router_modules` | `routes_call_controllers` | `route_validation_middleware` | `controller_service_repository` | `auth_middleware_present` | `jest_supertest_layout` |
| Shaisolaris | `express_router_modules` | `routes_call_controllers` | `controller_validation` | `controller_model` | `auth_middleware_present` | `no_clear_tests` |
| masb0ymas | `express_router_modules` | `routes_call_services` | `no_clear_validation` | `service_data_access` | `auth_middleware_present` | `no_clear_tests` |
| gonzaloplaza | `express_router_modules` | `routes_call_controllers` | `route_validation_middleware` | `clean_architecture_ports` | `auth_middleware_present` | `jest_test_layout` |
| steve-lebleu | `express_router_modules` | `routes_call_controllers` | `route_validation_middleware` | `controller_repository` | `auth_middleware_present` | `mocha_supertest_layout` |

## Evidence decisions

- G5API route files import and query the shared SQL client directly; route comments and hand-written guards are not a validation middleware.
- alexleboucher uses router/request-handler/use-case/repository wiring. Zod parsing occurs in request handlers, so it is controller-side rather than edge middleware validation.
- h3nrzi's routers are feature-specific core modules; controllers call services, and services call repositories.
- Shaisolaris controllers call Prisma and `safeParse` source-backed schemas directly; its auth is mounted middleware.
- masb0ymas route handlers call services, while Zod parsing is owned by those services rather than a route validation layer.
- gonzaloplaza has explicit application/domain/infrastructure layers and route-wired express-validator arrays.
- steve-lebleu routers pass Joi validator middleware to controllers, whose data access is directly through TypeORM repositories.
