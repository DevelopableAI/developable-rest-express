# Public Express expansion — batch 01 label review

These labels were approved on 2026-08-05 after inspection of the SHA-pinned checkouts listed in [batch 01](public-express-expansion-batch-01.md) and promoted to the public benchmark fixture.

| Repo | Route style | Route boundary | Validation | Layering | Auth | Test layout |
| --- | --- | --- | --- | --- | --- | --- |
| danielfsousa | `express_router_modules` | `routes_call_controllers` | `route_validation_middleware` | `controller_service_model` | `auth_middleware_present` | `mocha_supertest_layout` |
| mkosir | `express_router_modules` | `routes_call_controllers` | `route_validation_middleware` | `controller_service_repository` | `auth_middleware_present` | `mocha_test_layout` |
| gothinkster | `express_router_modules` `review` | `routes_call_controllers` | `controller_validation` `review` | `controller_service_model` | `auth_middleware_present` | `jest_test_layout` |
| developit | `resource_router_modules` `review` | `routes_call_services` `review` | `no_clear_validation` | `flat_handlers` `review` | `auth_middleware_unclear` | `no_clear_tests` |
| satishbabariya | `express_router_modules` | `routes_call_services` | `route_validation_middleware` | `service_data_access` `review` | `auth_middleware_present` | `no_clear_tests` |
| watscho | `express_router_modules` | `routes_call_controllers` | `controller_validation` `review` | `controller_service_model` | `auth_middleware_present` | `no_clear_tests` |
| mzubair481 | `feature_router_modules` | `routes_call_services` | `route_validation_middleware` | `clean_architecture_ports` `review` | `auth_middleware_present` | `vitest_test_layout` |
| ascii-16 | `feature_router_modules` | `routes_call_controllers` | `route_validation_middleware` | `feature_service_layer` | `auth_middleware_present` | `jest_supertest_layout` |
| Louis3797 | `express_router_modules` `review` | `routes_call_controllers` | `route_validation_middleware` | `controller_service_repository` `review` | `auth_middleware_present` | `jest_test_layout` |
| sidhantpanda | `inline_app_routes` `review` | `routes_call_controllers` `review` | `route_validation_middleware` `review` | `controller_model` `review` | `auth_middleware_unclear` | `jest_supertest_layout` |

## Evidence reviewed

- Router/module evidence: `src/**/routes`, `src/modules/*/*.route.ts`, `src/modules/*/http/*.routes.ts`, and the Express app composition files.
- Layering evidence: controller, service, model, TypeORM/Prisma, repository/port, and feature-module source paths and their imports.
- Test evidence: package scripts/dependencies and Jest/Vitest/Mocha configuration plus discovered test files.
- Auth and validation evidence: route middleware imports and authentication/validation modules, rather than package dependencies alone.

## Review decisions needed

1. Keep architecture-specific truth labels such as `resource_router_modules`, `clean_architecture_ports`, and `mocha_supertest_layout`, even though the current detector does not support them; this is preferred because it exposes capability gaps honestly.
2. Confirm the six `review` layering/boundary labels by opening the indicated implementation imports before moving the table into `benchmarks/public/express_v1.yaml`.
3. Decide whether repos with no committed runnable test files but a Jest dependency are `no_clear_tests` (the current recommendation) or `jest_test_layout`.
