# Public Express expansion — batch 04 scout queue

**ADMITTED 2026-08-31.** 29 of these 30 entered the corpus; see [the batch 04 label review](public-express-expansion-batch-04-label-review.md). This queue is retained as the scouting record.

This queue contains 30 public, permissively licensed Express application candidates, scout-verified on 2026-08-05 as non-fork and non-archived. They were **not** benchmark truth when scouted: each requires source inspection at the listed SHA, a six-convention label review, and the public corpus-policy admission checks before entering a fixture.

| Candidate | Pinned scout SHA | License | Coverage reason |
| --- | --- | --- | --- |
| Joliwood/osport-server | `2d094a344592f62308a18160c410f855bb036adc` | MIT | Express 5, Zod, Prisma, Vitest. |
| rafaelfl/express-typescript-auth | `514000b2a0dc928762fd408a46e4fd54c4468ead` | MIT | express-validator, Mongoose/Passport/Redis, Jest/Supertest. |
| skarif2/node-rest-starter | `209939b882194bcb78ad035a94d489500e6c3fce` | MIT | Joi middleware and Jest/Supertest. |
| cristian-azocar/microservice-boilerplate | `dbb03956864e5b2b4fcabc41de5760e31972b961` | MIT | Joi microservice, unit and e2e Jest tests. |
| israelmuca/express-i18n-api | `0bff55f378e6485f21967cf464b06837ed2d3fd6` | MIT | Older express-validator with Mocha/Chai HTTP. |
| bush1D3v/tsbank_api | `3e307c1790cd99bfcb3dd09d9a7638fbcfe8eb07` | MIT | Yup, Jest/Supertest, banking domain. |
| lucanovello/starter-express-prisma-jwt | `6bcd86b522e7014658c215d1c3b0372a24d87a30` | MIT | Zod/Prisma/JWT with Vitest/Supertest. |
| frckbrice/farming-product-REST-api | `cc27a2edd77e7dba6e4202cad9b9f001610cc8e5` | MIT | Zod and controller-grouped Vitest tests. |
| KhaledSaeed18/node-express-boilerplate | `438a928d6edba31b1f968b389a57ae53430cfb97` | MIT | Express 5, Zod/Prisma/Vitest. |
| Prasunjais/express-boiler-plate | `faac67244a51fdf8b5c397c6e1d4d8563dbd7199` | MIT | Joi/Objection with colocated tests. |
| Aron-HD/rest-api | `9591fcb9ebea4e33f84d9fd1ff74dce6ce636e27` | MIT | Zod/Mongoose no-test contrast. |
| FawzyMokhtar/TypeScript-in-Nodejs-Starter | `5c94196b267dd534352eb065951e1a0d58ca3f34` | MIT | express-validator no-test contrast. |
| zarif007/ez-node-ts-express-mongoose-boilerplate | `ff2d424b983a4f42bc409765f7f9b00eceade1a4` | MIT | Joi and Zod dual-schema case. |
| yug95/node-mysql | `93828eff9fa89ada918d8198cd3c282e50d210ef` | MIT | AJV/MySQL candidate; verify real AJV call sites. |
| jpedroschmitz/gobarber-api | `794cd7d5e1da9e93ffed8a55f80ec3118ffe5c5b` | MIT | Yup and queue/data-access architecture. |
| Canario0/hexagonal-express | `361c2d81453c00e1ea8c3a9b4dcddd90a9a2775c` | MIT | Context-oriented hexagonal/CQRS shape. |
| LCcodder/nodejs-hexagonal-architecture-boilerplate | `6096e359ca53f10acd08a5041a95bc7fd659473f` | MIT | Ports/use-cases/adapters/repositories. |
| luizomf/clean-architecture-api-boilerplate | `7fb1ba431f8dd3d9f581798c072019eceb72d73e` | MIT | Explicit application ports and adapters. |
| eldimious/nodejs-api-showcase | `6a35edb0b0a14cf3e951ff87c110b89022102d8a` | Apache-2.0 | Clean/hexagonal data repositories and HTTP routes. |
| vyancharuk/nodejs-api-boilerplate | `9b8343b05fee2677a392262146a08e94443ca718` | MIT | Vertical feature modules with routes/controllers/services/repos. |
| Shyam-Chen/Express-Starter | `90d73b02836c734c2256fe71b741cd3b0823dd19` | MIT | Feature co-location across controller/model/service. |
| mrmovas/Express-BetterAuth-Boilerplate | `5ff1b6a4d2d435e8718b631e380d6cc748d859c4` | MIT | Better Auth/Kysely route and adapter shape. |
| EQuimper/nodejs-api-boilerplate | `cc702d73f14aec7e3eb88547bdbb2837ec0d6d7a` | MIT | Conventional control with broad route tests. |
| aichbauer/express-rest-api-boilerplate | `fa0fa7cf8979bfc6d5b12283286b4a5d4b3d43ed` | MIT | Config-routes/controller/service organization. |
| hamidukarimi/authforge-express | `30268316c31b388a8bc5bfc04b2d2f5bcf628411` | MIT | Express 5 auth/session service. |
| pallavi-shekhar/twitter-clone-backend | `7b8e0a6d22f00cff54fcc8b3d9e51f4478f57f77` | Apache-2.0 | Versioned routes and controller/model domains. |
| maitraysuthar/rest-api-nodejs-mongodb | `6a1ba2da70a26b010d5aa1791a778a69b8ce7396` | MIT | Direct routes/controllers/Mongoose baseline. |
| smaje99/express-typescript-hexagonal-architecture | `ebb82d19597bc08b38d20e590876f5eae3a29b2a` | MIT | Hexagonal user-repository structure. |
| jerrychong25/node-express-mongo-passport-jwt-typescript | `d6148da8af71b400ddf1f1a74ab72f3a620485c5` | MIT | Mongoose with Passport Local/JWT and no-test contrast. |
| antonio-lazaro/prisma-express-typescript-boilerplate | `346d60f6eb21dcee98f9ad63794958283091f248` | MIT | Prisma/Joi/Passport/Jest-Supertest reserve. |

Prioritize candidates that add a class with fewer than five examples, especially clean/hexagonal layering, AJV/Yup validation, handler boundaries, and non-Jest test layouts. Avoid admitting near-duplicate boilerplates together; retain the listed SHA only as a scout pin and re-verify it at fixture admission.
