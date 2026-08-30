# Convention Profile

A convention profile is the unit of inference for `developable-rest-express`.

It should represent one coherent engineering style for one REST-service family, not an entire company.

## Why profiles exist

Different teams often use different conventions even inside the same company. A single ingestion set that mixes those styles will create noisy and untrustworthy outputs.

Profiles solve that by isolating convention learning.

Every profile is an Express profile; they differ by which Express codebases they bound.

Examples:
- `public-express-v1`
- `customer-platform-express`
- `partner-integrations-express`

## Repo categories

### Reference repos

These define the main convention signal.

Recommended size:
- minimum: 2
- healthy: 3 to 7
- maximum for weighted inference: 10

Reference repos should be:
- actively maintained
- representative
- internally trusted
- low on one-off exceptions
- provided either as local filesystem paths or GitHub repo URLs

### Context repos

These are available for lookup and broader context, but should not dominate convention inference.

Use them for:
- edge cases
- legacy repos
- additional examples
- broader retrieval after conventions are established

## Profile fields

### profile_id
Stable slug for the profile.

### library
For this project, always `developable-rest-express`.

### purpose
Short human description of what this profile is for.

### repo_metadata
Per-repo metadata such as framework, language, and maturity.

The metadata key should match the effective `repo_id`, whether that id was derived from a path/URL or provided explicitly.

### revision

Optional full Git commit SHA for a repository input. Profiles can omit it when they intentionally track a moving repository, but public benchmark profiles should always pin it.

```yaml
- repo_id: public-api
  source: https://github.com/example/public-api.git
  revision: 0123456789abcdef0123456789abcdef01234567
```

When supplied, the workspace checks that the resolved local `HEAD` matches the requested revision. GitHub benchmark fixtures require this field.

### inference_scope
The subset of conventions the harness is allowed to infer.

### safety_policy
Operations that must stay approval-gated in downstream tooling.

### output_targets
Artifacts intended for emission later, such as MCP config or skills.

### evaluation_set
Held-out repos to test whether inferred conventions generalize.

## Fitness rule

If the same profile shows high contradiction across route style, auth model, or layering pattern, the harness should recommend splitting it into multiple profiles.
