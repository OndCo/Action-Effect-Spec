# Requirements-to-Case Traceability

This is design coverage, not executable conformance evidence. One linked case
per requirement does not exhaust all branches of a requirement. Stable release
requires executable positive/negative vectors and independent consumers.

| Requirement | Design case | Purpose |
| --- | --- | --- |
| CORE-001 | V01 | Accepted description confused with permission |
| CORE-002 | V02 | Signed declaration confused with true observation |
| CORE-003 | V03 | Internal-read tuple mixed with external-send tuple |
| CORE-004 | V04 | One source and two destinations given without pairing |
| CORE-005 | V05 | Unknown category or empty effects interpreted as safe |
| CORE-006 | V06 | git push --force treated as proof of history rewrite |
| CORE-007 | V07 | Partial trace supplied as complete descendant bound |
| CORE-008 | V08 | Known transfer plus unknown destination |
| CORE-009 | V09 | Duplicate JSON member or lone surrogate |
| CORE-010 | V10 | Quantity -0, 01, exponent, currency change or overflow |
| CORE-011 | V11 | Confusable/case-folded identity without resolver |
| CORE-012 | V12 | Digest with changed relevant object or Unicode normalization |
| CORE-013 | V13 | One witness applied to untested future implementations |
| CORE-014 | V14 | Correct category on a different input/context/occurrence |
| CORE-015 | V15 | Two reviewers used to erase conflicts or claim independence |
| CORE-016 | V16 | CEL false && error versus worker timeout |
| CORE-017 | V17 | Mapper crash represented as successful review |
| CORE-018 | V18 | Human approve used to repair invalid proof |
| CORE-019 | V19 | Published mapping silently rewritten |
| CORE-020 | V20 | Changed relevant dependency without invalidation |
| CORE-021 | V21 | Expired trusted snapshot accepted as current |
| CORE-022 | V22 | Cached mapping used after live grant revoked |
| CORE-023 | V23 | Unknown critical extension removed and request retried |
| CORE-024 | V24 | Oversized/deep input truncated and accepted |
| CORE-025 | V25 | Evidence URL resolves to internal metadata endpoint |
| CORE-026 | V26 | Locator-only telemetry assumed anonymous |
| CORE-027 | V27 | HTTP timeout treated as non-execution and resent |
| CORE-028 | V28 | Self-test badge presented as certified secure/legally compliant |

No consumer passed these cases during this drafting task. The local draft check
validates links, schema examples, synthetic digest identities and structure only.
A real conformance report must enumerate all failed, unsupported and skipped
cases and must not substitute this table for execution.

## Adversarial Review Additions

There are now 40 designed scenarios for the 28 clauses, not 40 executed tests.
The rows below extend the one-per-clause seed table; executable payloads,
consumer oracles and branch coverage still must be implemented and reviewed.

| Cases | Clauses | Additional obligation |
| --- | --- | --- |
| V29-V30 | CORE-004/015 | Unique typed local IDs, no dangling/ambiguous evidence |
| V31-V32 | CORE-011/012/014/019 | Exact digest preimages, effective profile and combined binding |
| V33 | CORE-020/022 | Checker/trust/freshness invalidation distinct from live authorization |
| V34-V35 | CORE-004/008/010 | Required/unknown quantities, scale, repetition and exact targets |
| V36 | CORE-015 | Artifact reference and digest both required |
| V37 | CORE-023 | Critical extension versions and missing/marker-only payloads |
| V38 | CORE-005/007 | Empty report versus checked empty scoped bound |
| V39 | CORE-019/026 | Immutable identity versus sensitive-content withdrawal |
| V40 | CORE-028 | No full conformance with unmet mandatory obligations |
