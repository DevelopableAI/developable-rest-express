# Public Express expansion — batch 02 label review

These labels were approved on 2026-08-05 after manual inspection of the SHA-pinned checkouts recorded in [batch 02](public-express-expansion-batch-02-scouting.md). They are promoted to the public benchmark fixture.

| Repo | Route style | Route boundary | Validation | Layering | Auth | Test layout |
| --- | --- | --- | --- | --- | --- | --- |
| afteracademy | `express_router_modules` | `routes_call_repositories` | `route_validation_middleware` | `repository_only` | `auth_middleware_present` | `jest_supertest_layout` |
| betterstack | `express_router_modules` | `routes_call_repositories` | `route_validation_middleware` | `flat_handlers` | `auth_middleware_unclear` | `no_clear_tests` |
| JDIZM | `inline_app_routes` | `routes_call_controllers` | `controller_validation` | `flat_handlers` | `auth_middleware_present` | `vitest_test_layout` |
| ckdnd99 | `express_router_modules` | `routes_call_controllers` | `controller_validation` | `controller_model` | `auth_middleware_unclear` | `no_clear_tests` |
| Q00 | `decorator_routing` | `routes_call_controllers` | `no_clear_validation` | `controller_service_repository` | `auth_middleware_present` | `jest_supertest_layout` |
| DavidRodarte | `decorator_routing` | `routes_call_controllers` | `no_clear_validation` | `service_data_access` | `auth_middleware_present` | `no_clear_tests` |
| levelopers | `express_router_modules` | `routes_call_repositories` | `route_validation_middleware` | `flat_handlers` | `auth_middleware_present` | `no_clear_tests` |
| bhimrazy | `express_router_modules` | `routes_call_controllers` | `route_validation_middleware` | `controller_service_model` | `auth_middleware_present` | `mocha_test_layout` |
| esron | `express_router_modules` | `routes_call_controllers` | `route_validation_middleware` | `controller_model` | `auth_middleware_present` | `jest_supertest_layout` |
| jaimin1618 | `express_router_modules` | `routes_call_controllers` | `route_validation_middleware` | `controller_model` | `auth_middleware_unclear` | `no_clear_tests` |

## Evidence and deliberate boundary decisions

- Afteracademy routes import and call `database/repository/*Repo` directly. Its `repository_only` label preserves this architecture rather than incorrectly calling it a service layer.
- Betterstack and levelopers perform data access in route handlers. They are deliberately labeled `flat_handlers`; their route boundary is `routes_call_repositories` because it bypasses controller/service layers.
- JDIZM routes call handler modules; those handlers perform Zod validation and Drizzle access. They are treated as controllers for the route boundary, but as controller-side validation and flat data access for the other two conventions.
- ckdnd99 controllers call Drizzle directly and perform `safeParse` in those controllers. Its authentication checks are helper calls inside handlers, not a reviewed route middleware.
- Q00 and DavidRodarte use `routing-controllers`. The reviewed server configuration did not establish request-body validation at the route edge, so `class-validator` dependencies alone do not justify a validation label.
- bhimrazy's Mocha test uses Chai HTTP rather than Supertest; this preserves the non-Supertest Mocha regression category.
- jaimin1618 contains an authentication middleware implementation, but the reviewed route composition does not wire it in; this is intentionally `auth_middleware_unclear`.

Architecture-specific truth labels (`repository_only`, `routes_call_repositories`, and `mocha_test_layout`) are intentional even when detector support is incomplete. They make capability gaps and calibration failures measurable rather than hiding them behind a generic label.
