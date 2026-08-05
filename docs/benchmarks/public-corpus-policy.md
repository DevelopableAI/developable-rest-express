# Public Express benchmark corpus policy

This policy governs admission to every public Express benchmark fixture. It applies to candidate scouting, SHA pinning, labeling, and later fixture changes. It does not change the committed V1 results.

## Eligible sources

A candidate must satisfy all of the following at the specific revision being reviewed:

- Publicly accessible Git repository; not private, disabled, archived, or a fork.
- An Express-based API **application** with a readable source layout. Libraries, middleware packages, routing frameworks, generated-only examples, and toy/tutorial-only CRUD samples are out of scope.
- Reasonably sized for manual review and benchmark checkout. A monorepo is eligible only when one Express application is clearly isolated and its package subdirectory is recorded.
- Licensed under exactly one allowed SPDX identifier: `MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, or `ISC`. Unclear, custom, copyleft, proprietary, or unverified licensing is ineligible until resolved.
- Pinned to a full, immutable 40-character Git commit SHA; branches and tags are never benchmark inputs.

We store URLs, SHAs, labels, reports, and review evidence—not third-party source checkouts—in this repository. This policy is a curation rule, not legal advice.

## Required admission record

Before a candidate can enter a scored fixture, its reviewed candidate record must include:

- canonical source URL, full SHA, default branch, and verification date;
- SPDX license observed at that SHA;
- application subdirectory when applicable (otherwise `.`);
- evidence that the application uses Express and has a readable application layout;
- a short diversity rationale; and
- human-reviewed, source-backed labels for every supported convention.

The scored fixture remains the reproducible execution contract. Candidate records hold the additional curation evidence until the fixture format carries that metadata directly.

## Corpus balance and exclusions

- Prefer real API applications and avoid near-duplicate boilerplate families; do not admit another candidate if it adds no meaningful convention coverage.
- Deliberately cover distinct route declarations, validation placement, service/data-access layering, authentication, and test frameworks, including clear negative/no-evidence cases.
- Keep detector-development references distinct from held-out reporting repositories when practical, and record the role.
- Do not derive labels from analyzer output. A label must be supported by source inspection at the pinned SHA and reviewed under `benchmark-governance.yaml`.
- Exclude a candidate when the application boundary, license, provenance, or source evidence cannot be verified. Do not substitute a moving revision.

## Change control

Additions and label corrections are reviewed changes. They must pass `prepare-benchmark` (including canonical-origin and SHA checks) and `evaluate-benchmark`; every mismatch is reviewed before merge. Existing benchmark releases and their uploaded reports remain immutable comparators—an expansion is recorded as a new reviewed corpus state, not a rewritten historical result.
