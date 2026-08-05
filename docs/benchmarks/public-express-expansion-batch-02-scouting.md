# Public Express expansion — batch 02 scouting

This is the retained candidate pool for the next benchmark expansion. The ten entries in the verified table below were admitted on 2026-08-05; all other candidates remain unpinned and unlabeled until they pass the [public corpus policy](public-corpus-policy.md).

## Zod and contract-driven APIs

- `RobinTail/express-zod-api`
- `betterstack-community/node-redis-backend`
- `muneebhashone/typescript-backend-toolkit`
- `KhaledSaeed18/node-express-boilerplate`
- `JDIZM/supabase-express-api`
- `ckdnd99/node-express-drizzle-api`
- `kevmok/drizzle-express-starter`

## Decorator and generated routing

- `typestack/routing-controllers`
- `Q00/api_server_boilerplate`
- `DavidRodarte/Prisma-Express-Template`
- `Panenco/node-course`
- `davesag/swagger-routes-express`
- `jarradseers/express-load`

## Express-validator and alternate validation

- `levelopers/Ecommerce-Nodejs`
- `bhimrazy/express-blog-api`
- `esron/systranca-server`
- `jaimin1618/nodejs-backend`
- `NishiGaba/User-Login-System`
- `sayedazharsabri/Quiz-App-REST-API-TS-Mongoose`

## Joi and middleware validation

- `afteracademy/nodejs-backend-architecture-typescript` (admitted; verified record below)
- `shunny2/jwt-prisma`
- `octo-woapi/api-with-express`
- `jbutko/express-ts-api-boilerplate`
- `cristian-azocar/microservice-boilerplate`
- `LeeJeongYeop/nayak-express-skeleton`

## Screening rules

- Prefer runnable Express API applications over middleware or framework libraries.
- Retain only public, non-fork, license-clear repositories.
- Avoid near-duplicate boilerplate families and route-framework-only examples.
- Intentionally include controller-side, middleware-side, and no-clear-validation examples.

## Verified and admitted candidates

| Candidate | Status | Source and pinned SHA | License | App path | Verification evidence |
| --- | --- | --- | --- | --- | --- |
| [afteracademy/nodejs-backend-architecture-typescript](https://github.com/afteracademy/nodejs-backend-architecture-typescript) | Admitted and labeled | `https://github.com/afteracademy/nodejs-backend-architecture-typescript.git` at `9a49d09c77d9c58772cb724f4c4fa144a66b68d4` | `Apache-2.0` | `.` | Express router modules, direct repository access, validation middleware, auth, Jest/Supertest. |
| [betterstack-community/node-redis-backend](https://github.com/betterstack-community/node-redis-backend) | Admitted and labeled | `https://github.com/betterstack-community/node-redis-backend.git` at `ab89f44f109ea8b4f859b3379978827031a5a6ff` | `MIT` | `.` | Express router modules, Zod middleware validation, direct Redis data access, no committed tests. |
| [JDIZM/supabase-express-api](https://github.com/JDIZM/supabase-express-api) | Admitted and labeled | `https://github.com/JDIZM/supabase-express-api.git` at `bd4369e69a84e5321a069db169ee746eb72150e5` | `MIT` | `.` | Inline application routes that call handlers, handler-side Zod validation, direct Drizzle access, Vitest. |
| [ckdnd99/node-express-drizzle-api](https://github.com/ckdnd99/node-express-drizzle-api) | Admitted and labeled | `https://github.com/ckdnd99/node-express-drizzle-api.git` at `c74b517053f7b079f7b288b7c3c5741100f52836` | `MIT` | `.` | Router/controller layout, controller-side Zod and Drizzle access, no committed tests. |
| [Q00/api_server_boilerplate](https://github.com/Q00/api_server_boilerplate) | Admitted and labeled | `https://github.com/Q00/api_server_boilerplate.git` at `80f18f59d07fb5a52fc51e33e1ef89d0ae38afe5` | `MIT` | `.` | `routing-controllers` decorators, TypeORM service/repository layer, JWT checker, Jest/Supertest. |
| [DavidRodarte/Prisma-Express-Template](https://github.com/DavidRodarte/Prisma-Express-Template) | Admitted and labeled | `https://github.com/DavidRodarte/Prisma-Express-Template.git` at `3c05b98befd2419021c4acabf4dd8ca8f2606fa4` | `MIT` | `.` | `routing-controllers` decorators, services that own Prisma access, authorization checker, no committed tests. |
| [levelopers/Ecommerce-Nodejs](https://github.com/levelopers/Ecommerce-Nodejs) | Admitted and labeled | `https://github.com/levelopers/Ecommerce-Nodejs.git` at `0c3ba844b4d4ff5a4a64109050dd906b6334a532` | `MIT` | `.` | Router handlers directly use Mongoose models, route-local express-validator calls, auth module, no tests. |
| [bhimrazy/express-blog-api](https://github.com/bhimrazy/express-blog-api) | Admitted and labeled | `https://github.com/bhimrazy/express-blog-api.git` at `30464a263a21b85cadfa095e09fe16444e610357` | `MIT` | `.` | Router/controller/service/model stack, explicit validators, auth middleware, Mocha/Chai HTTP tests. |
| [esron/systranca-server](https://github.com/esron/systranca-server) | Admitted and labeled | `https://github.com/esron/systranca-server.git` at `f891722a678e8d60a0f16279066e3d05e95d02df` | `MIT` | `.` | Router/controllers/models, route-passed controller validation, auth controller middleware, Jest/Supertest. |
| [jaimin1618/nodejs-backend](https://github.com/jaimin1618/nodejs-backend) | Admitted and labeled | `https://github.com/jaimin1618/nodejs-backend.git` at `1038a49084a5e0d176a41079c7d2bc1340fd22c6` | `MIT` | `.` | Router/controller/model stack, express-validator middleware, auth implementation not wired into reviewed routes, no tests. |

The [batch 02 label review](public-express-expansion-batch-02-label-review.md) records the six source-backed labels. The remaining candidates are not benchmark truth.

## Excluded during this pass

- `sayedazharsabri/Quiz-App-REST-API-TS-Mongoose`: no recognized SPDX license in GitHub metadata; exclude until its license is verified under the corpus policy.
