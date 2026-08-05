# Public Express expansion — batch 01

This is a pinned candidate queue for expanding the benchmark beyond its six-repository V1 corpus. Each repository was checked on 2026-08-04: it is public, non-archived, non-fork, MIT-licensed, and its root `package.json` declares `express`. It is governed by the [public corpus policy](public-corpus-policy.md).

These candidates are **not** benchmark truth yet. Before adding one to `benchmarks/public/express_v1.yaml`, inspect the pinned checkout and have all six convention labels manually reviewed.

| Repository | Default branch | Pinned revision | Why include it |
| --- | --- | --- | --- |
| [danielfsousa/express-rest-boilerplate](https://github.com/danielfsousa/express-rest-boilerplate) | `main` | `b8bed6d7cfce3cf2ef89ec1b5e47b52dfc50e874` | JavaScript, Mongoose, Mocha/Supertest. |
| [mkosir/typeorm-express-typescript](https://github.com/mkosir/typeorm-express-typescript) | `main` | `117f6647c5aabf97b5d40af060106230a103c714` | TypeORM and TypeScript. |
| [gothinkster/node-express-prisma-v1-official-app](https://github.com/gothinkster/node-express-prisma-v1-official-app) | `main` | `6ac99ea5aeadc4e001dd4d6933c2e269f878a969` | Prisma RealWorld application and Jest. |
| [developit/express-es6-rest-api](https://github.com/developit/express-es6-rest-api) | `master` | `9b8c005a38a0de820eac7e319e81b4318c320630` | ES-module/minimal router conventions. |
| [satishbabariya/nodejs-boilerplate](https://github.com/satishbabariya/nodejs-boilerplate) | `master` | `d49fce2ba412232813945e594d07d22f7a603dd9` | Clean architecture, TypeORM/Typedi, Jest. |
| [watscho/express-mongodb-rest-api-boilerplate](https://github.com/watscho/express-mongodb-rest-api-boilerplate) | `master` | `889fd1679326e9e2124ada1d67f59abb297dc0ed` | Express 5, TypeScript, Mongoose. |
| [mzubair481/express-boilerplate](https://github.com/mzubair481/express-boilerplate) | `main` | `b43318dc59fb8c7f3b47eac870e54d5226349143` | Express 5, Drizzle, Zod, Vitest. |
| [ascii-16/expressjs-typescript-prisma-boilerplate](https://github.com/ascii-16/expressjs-typescript-prisma-boilerplate) | `main` | `c27ad6522d8221f5ce35662a1b854b6a9f612530` | TypeScript/Prisma and multiple Jest suites. |
| [Louis3797/express-ts-auth-service](https://github.com/Louis3797/express-ts-auth-service) | `main` | `fc6722badf8b43c02adba9de7e11bb342c09a6f1` | Focused authentication service, Prisma, Jest. |
| [sidhantpanda/docker-express-typescript-boilerplate](https://github.com/sidhantpanda/docker-express-typescript-boilerplate) | `master` | `4c7c5863c5e16799c9f59dd11032e1e58658b4fb` | TypeScript/Mongoose with a conventional Jest API stack. |

## Admission checklist

- Prepare a detached checkout at the listed revision and verify its canonical origin.
- Identify the REST API package if the repository has multiple packages.
- Record explicit evidence and reviewed labels for all six conventions.
- Add only the reviewed entry to the scored fixture; keep it held out from detector development when possible.
