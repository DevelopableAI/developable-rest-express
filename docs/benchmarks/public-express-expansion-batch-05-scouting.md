# Public Express expansion — batch 05 scout queue

**NOT YET BENCHMARK TRUTH.** This queue contains 31 public, permissively licensed Express
application candidates, scout-verified on 2026-09-03 as non-fork, non-archived, carrying exactly one
allowed SPDX identifier, and declaring `express` in `dependencies` at the listed SHA. Each still
requires source inspection, a six-convention label review, and the `public-corpus-policy.md` admission
checks before entering a fixture.

## Purpose: this batch is holdout material

Batch 05 exists to rebuild the holdout, not to grow the training set. The eleven repositories held out
since 2026-08-31 were spent on 2026-09-03 when the route declaration work read them, and two of them
were diagnosed individually. A holdout can only be built from repositories that have never been
inspected, so these 31 become the new held-out set and the previous eleven join the training
data.

Corpus after admission: 63 training + ~31 held out.

## Why these were scouted differently from batch 04

Batch 04 was scouted for **coverage** — deliberately seeking clean/hexagonal layering, decorator
routing and unusual validators, because training data should stress the detectors.

A holdout scouted that way would be biased. Hunting repositories that break the current rules makes
the held-out figure read low and every future change look as though it generalises badly; sampling
boilerplate near-clones makes it read high. A holdout estimates accuracy on the population the
analyzer would actually meet, so this queue **mirrors the corpus distribution instead of probing its
edges**.

The one distribution deliberately matched is language. The existing 63 repositories are 68%
TypeScript / 32% JavaScript; this queue is 61% / 39%. Candidates were sampled across the star
range rather than taken from the top, because the most-starred Express results are dominated by
tutorials and awesome-lists rather than applications.

## Discipline: the analyzer has not been run against any of these

No detector has been executed against any candidate in this queue, and the coverage column records
only observable facts — declared dependencies and `src/` subdirectory names. It contains no predicted
convention value.

This matters more here than for a training batch. `public-corpus-policy.md` forbids labels derived
from analyzer output; a holdout whose candidates had been pre-screened by the analyzer would be
worthless as validation, because the sample would already encode what the analyzer finds easy.

## Vocabulary note for label authors

`validation_at_edge_pattern` gained a fourth value on 2026-09-03: `schema_class_validation`, for
repositories validating by decorators on request classes (class-validator and similar) rather than by
middleware in a route chain. Several candidates below declare `class-validator`. The detector cannot
yet emit this value, so such repositories are expected mismatches until it does — label from source
regardless.

## Candidates

| Candidate | Pinned scout SHA | License | Coverage reason |
| --- | --- | --- | --- |
| acellam/ment | `a230ef99c789fd1021cc85da5be1e33f39901af4` | Apache-2.0 | express-validator; Mongoose; JWT/Passport; src/__tests__, src/api, src/config, src/controllers; tests present |
| AlbertHernandez/express-typescript-service-template | `65a84b4c669c3ae5d3b48fa283496fba71c968f7` | MIT | src/app, src/contexts; tests present |
| alfaarghya/alfa-leetcode-api | `783321143eb21b847a9b0119a37920f04ba3324a` | MIT | Zod; src/Controllers, src/FormatUtils, src/GQLQueries, src/schema; tests present |
| Babadinho/todo-jobs | `c7c139a966ee5eafa49066a89222b56ba8233c27` | MIT | Mongoose; JWT/bcrypt; no test files |
| Bot-Rakshit/backend_bm | `4b19ee16f102d3ece339a778bf22349e2a75f499` | MIT | Joi; Prisma; JWT/Passport; src/config, src/controllers, src/middlewares, src/models; no test files **(generator files present -- verify before labelling)** |
| bytesleo/nodetomic | `2a7e4646a60e466d6bfe604cc776f9f9b12c3172` | MIT | Mongoose; JWT/bcrypt; src/business, src/constants, src/controllers, src/libs; tests present |
| cptdanko/node_typescript_crud_notes | `b223965c96c576ae6b945bd6d583d9d6ef4fd802` | Apache-2.0 | JWT; src/api, src/datastore, src/logFuncs, src/routes; tests present |
| DevilsAutumn/Quizry | `14e747611c22b6f608c1962612fde94192ad13f4` | MIT | Mongoose; JWT/bcrypt; no test files |
| djizco/mern-boilerplate | `c6ec2427801c9cd48aaa54a84afd1b3d94c1fae3` | MIT | Mongoose; Passport/bcrypt; tests present |
| ecitlm/Node-SpliderApi | `0c3a360d62c623121686c3e85c5c705c02d83d62` | MIT | express-validator; Sequelize/mysql2; JWT; src/config, src/controller, src/entity, src/middlewares; no test files |
| HADMARINE/quick-nodejs-backend | `1e6ba453846760c724b30bd4c9ab0d1316a5dfa6` | Apache-2.0 | Mongoose; JWT; src/__tests__, src/error, src/io, src/lib; tests present |
| Ido-Barnea/Doctor-Who-API | `aff72ba23e5935a9b08bbe07de54b8947f2058d0` | Apache-2.0 | src/routes, src/utils; tests present |
| JaouherK/proxy-gateway | `36620da32688fa8faa3f4b741e0a05de7e8c80c6` | MIT | Sequelize/mysql2; JWT/Passport; src/config, src/const, src/domains, src/exceptions; tests present |
| jeffersonRibeiro/react-nodejs-mongodb-crud | `59e4e856d6f4617cfa09276e369e7ec3faa680d3` | MIT | Mongoose; JWT/Passport; src/components, src/scenes, src/services; tests present |
| Leonardpepa/Pepaverse | `d26489d9f09c243808ed1d2c7f67a1fff1f391b0` | MIT | Mongoose; JWT/Passport; no test files |
| ludengz/claude-usage-dashboard | `ee0c39dbdeb6cc22ce6a5067b414ea6f3a7d3709` | ISC | tests present |
| makee-workshop/Huayra | `3f8bb957063f4c754058a590ed17eb26bbfe7641` | MIT | Mongoose; JWT/Passport; src/__tests__, src/account, src/admin, src/components; tests present |
| MarkKhramko/nodejs-express-jwt | `e606d0a209da6034d6c33b3a6fdfeb474511ded7` | MIT | Sequelize/mysql2; JWT/bcrypt; no test files |
| mehmet-dogru/samu-api | `c6506effdd9e01c55fa1cee896317cefa4b48091` | MIT | Joi; Mongoose; JWT; no test files |
| MochiDay/auto-apply-applet | `4ae6c9585352a5533a72bb8d8e9ca5b919010db2` | MIT | src/drivers, src/types, src/utils; no test files |
| Mohamed-Ramadan1/wordNest | `de515d5153ed4c7ed88ea237f4ae13841d756527` | MIT | Joi/class-validator; Mongoose; JWT/bcrypt; src/config, src/features, src/jobs, src/logging; tests present |
| Open-Source-Kigali/osk-backend | `97f45a12405b3b18d322b0ee23044556dda2e7de` | MIT | Zod; Prisma/pg; src/config, src/controllers, src/middlewares, src/routes; tests present |
| oslabs-beta/ditto | `fa80cb2429f0de54951b6580ef893b2ed08ac698` | MIT | pg; JWT/bcrypt; tests present |
| rikvermeulen/co-op-gitlab | `04425f89a124473415e3f1e2723e44aec3170335` | MIT | src/controllers, src/helpers, src/middlewares, src/routers; tests present |
| rocambille/start-express-react | `07bdce128445e0599c4a81170f86232789f9efac` | MIT | Zod; JWT; src/database, src/env, src/express, src/react; tests present |
| run-llama/liteparse-server | `70cee35fb429f531d657d3328dc9939c89c0312b` | MIT | tests present |
| sabiss/bibliotecaNERDS | `99833f974ce679794bc9f47a21cfc4022e161cd1` | MIT | Mongoose; JWT/bcrypt; src/config, src/controllers, src/funcoesAuxiliares, src/middlewares; no test files |
| SanHsien/gpt-ai-assistant | `920a2376d705ce1accc16ca79fd954e30747651e` | MIT | pg; tests present |
| shanhuiyang/TypeScript-MERN-Starter | `e8470167d4e8d939ca0446a70db0d7b40a94ef83` | MIT | express-validator; Mongoose; Passport; tests present |
| shunny2/jwt-prisma | `9dad56130e095338eea4bebdedb8bf61afd70891` | MIT | Joi; Prisma; JWT/bcrypt; src/@types, src/controllers, src/docs, src/helpers; no test files |
| wednesday-solutions/node-express-graphql-template | `114609ce127eba31df8dbc5e921a5eee679029d9` | MIT | Sequelize/pg; JWT; tests present |

## Scouting method

Candidates were found by GitHub topic search (`topic:express`, `topic:expressjs` combined with
`rest-api`, `nodejs`, `mongodb`, `postgresql`, `typescript`, `backend`), filtered to non-fork,
non-archived, `stars:>5`, `pushed:>2023-06-01`, `size:<40000`, then verified individually against the
GitHub API for an allowed SPDX identifier, an `express` entry in `dependencies`, and a resolvable
40-character SHA on the default branch.

Description- and README-matched search was tried first and abandoned: of the 40 highest-starred hits,
24 were not Express projects at all and 9 declared `express` only in `devDependencies`. Topic search
raised the hit rate from roughly 10% to 42%.

Rejected during scouting: `jackypan1989/express-query-parser`, `rohanmistry231/Medium-Blogs-Categorization-Website-Backend`
`sherman-yang/nvidia-model-info` and `Quincunx33/Stress-Tester`, each too small or too unstructured to
be an application with a readable layout. Three further candidates were rejected as published
libraries rather than applications.

Two candidates were rejected for **holdout correlation** rather than for any policy breach.
`hamidukarimi/SchoolOS-backend` and `jerrychong25/node-express-sqlite-jwt-typescript-typeorm` share an
author with `hamidukarimi/authforge-express` and `jerrychong25/node-express-mongo-passport-jwt-typescript`,
which are training repositories. A developer reuses their own conventions, so a held-out repository by a
training repository's author is partly predictable from the training set and would inflate the held-out
figure for reasons unrelated to generalisation. Same-author overlap is a stricter bar for holdout
material than the corpus policy applies to training data.

## Still required before admission

- Source inspection at each pinned SHA, confirming an Express application with a readable layout.
- SPDX licence re-verified at the pinned SHA rather than at repository head.
- Six human-authored convention labels per admitted repository, with evidence recorded per label.
- Confirmation that `Bot-Rakshit/backend_bm` is not a generated-only scaffold, the ground on which
  `zarif007/ez-node-ts-express-mongoose-boilerplate` was excluded from batch 04.
