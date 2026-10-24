# Partial Profile Accountability

The [machine-readable matrix](core-accountability.json) accounts for every
CORE-001..028 at Spec source revision
`a9b86f4b529a5e330c2a9bf1b8c4c259a7b36e40`. It is a non-normative, same-project
source assessment, not a passed-case report, stable release, security badge or
full conformance claim. `externallyIndependentEvaluations` remains **0**.

## Read the Matrix

Each requirement names accountable roles, a literal anchor in unchanged
`SPEC.md`, role gaps and all three assessed implementations. Each implementation
assessment includes role-specific support, finite scope, implementation anchors,
positive/negative test anchors and explicit untested obligations. Role attribution
is an accountability aid, not an amendment to the normative clause.

| Role support | Meaning within this partial assessment |
| --- | --- |
| `supported_subset` | Only the stated finite behavior has implementation and positive/negative source anchors; not the whole CORE clause. |
| `partial` | Some behavior is present, but broader obligations or direct test coverage are missing. |
| `unsupported` | The obligation is not implemented; a refusal test does not establish its positive branch. |
| `not_applicable` | That target does not perform the relevant role or conditional feature. This is not a pass or exemption for an adopter that does. |

Empty test arrays deliberately mean no cited test, not an implicit pass. A test
may contain both positive and negative assertions, and a test may be reused by
several requirements. Anchor counts are not executed cases, percentages or scores.

`files` records exact repository-relative paths and local raw-byte SHA-256 pins;
`anchors` records exact source selectors. Local code/test bytes are tied to the
stated source revision, but the checker does not authenticate Git history or
prove that a test assertion establishes the prose claim. Review both together.

The GitHub domain consumer is external evidence from Bench commit
`6d4f3c358ca5f68040a1416d751328e9aab041f5`, in
[`runtime-pilot/python`](https://github.com/OndCo/Action-Effect-Bench/tree/6d4f3c358ca5f68040a1416d751328e9aab041f5/runtime-pilot/python),
with exact test selectors in the matrix. These citations were source-reviewed;
the Spec-local checker only checks their metadata shape. It neither reads a
sibling Bench checkout nor fetches URLs, validates external anchors or runs
external tests. Bench policy, gate, ledger, provider and OPA results are outside
this assessment. The two local refund consumers do not implement this domain.

## Verify Offline

From the Spec checkout, with Node.js 22+ and no installation or account:

```sh
node scripts/check-coverage.mjs
node scripts/verify-candidate.mjs
node --test scripts/tests/*.test.mjs
```

The first two commands check source/candidate integrity only and always report
`testsExecuted: 0`. The third actually executes sidecar tests, not the cited
consumer tests. CI separately executes the existing JavaScript and Python
consumer suites. Both commands accept only an optional `--root PATH` for an
offline copy; output is one JSON result, or a fixed JSON error on stderr with
exit code 2. Missing/changed files and invalid metadata fail, never downgrade.

The checker bounds matrix bytes to 512 KiB, depth to 64, file entries to 64,
anchors to 256 and each source file to 1 MiB. Unknown keys, lost requirements,
unsupported role/status labels, missing declared subset evidence and broken
local anchors fail. Paths are canonical relative paths; symlinks below the
caller-selected root are rejected. This is an integrity tool for a quiescent
checkout, not protection against an attacker concurrently rewriting the host.

## Adopt Deliberately

The [GitHub candidate](../profiles/github-issue-comment/candidate/README.md)
adds immutable archival pins without changing the existing wire identifiers,
`profile_digest`, consumers or normative text. Its original direct/partial
scope, unknown descendants and failure semantics remain. It is not stable or
security certified. Run its verifier separately; existing consumers do not
automatically consume the sidecar.

Authority grants, signature checking, CEL, current revocation, remote registries,
enforcement and provider observation are not supplied by these offline consumers.
Use a separate current authority/enforcement system before execution. Unknown
effects remain unknown; hashes and agreement do not establish semantic truth.

For source changes, review the affected implementation, tests, assessment and
pins together. Do not update hashes merely to silence CI. Changed candidate
semantics/components need a new candidate revision and explicit compatibility
review, not reassignment of the old identifier. No live calls, private fixtures
or new legal promises are part of this sidecar. The existing [MIT license](../LICENSE)
and publication limitations remain unchanged.
