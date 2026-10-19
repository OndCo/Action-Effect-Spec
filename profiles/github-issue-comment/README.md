# GitHub Issue Comment Profile 1

Prepared 18 October 2026, America/Toronto. Additive experimental domain profile. The
release is `v0.2.0-draft.1`; the unchanged core wire version is
`0.1.0-draft.1`. The legacy refund profile is not rewritten or generalized.

This profile describes one direct API mutation, not arbitrary GitHub tools,
workflow closures, source-code safety, credential authority or provider internals.
It is usable without OSuite. It does not grant GitHub or local-policy permission.

## Native Input and Configuration

SDK input: `{"lane":"sdk","call":{"owner":"OndCo","repo":"Action-Effect-Bench","issue_number":1,"body":"Synthetic test"}}`.
MCP input: `{"lane":"mcp","call":{"name":"add_issue_comment","arguments":{"owner":"OndCo","repo":"Action-Effect-Bench","issue_number":1,"body":"Synthetic test"}}}`.
These are local capture envelopes. The MCP lane uses actual MCP `tools/call`
transport; this envelope is not a replacement protocol.

Only the shown keys are accepted. Names are ASCII and path-safe: owner matches
`[A-Za-z0-9][A-Za-z0-9-]{0,38}`; repo matches
`[A-Za-z0-9_.-]{1,100}` but is neither `.` nor `..`. Issue number is a positive
integer at most 2147483647, excluding booleans. Body is a nonempty Unicode-scalar
string with at most 8192 UTF-8 bytes. No normalization, path unescaping, URL
resolution, template expansion or caller-supplied endpoint is supported.

The caller configures `context` with a nonempty `principal`, nonempty
`data_class`, and `implementation: "github-comment-bridge/1"`. Missing facts
produce `untrusted_evidence/missing_context`; a different implementation produces
`untrusted_evidence/implementation_binding`. This is a declared implementation
identity, not attestation of arbitrary SaaS code. Executable/package source
hashes are recorded separately by the experiment. Classification comes from the
trusted test configuration, not text analysis; no DLP classifier is claimed.

## Deterministic Processing

1. Reject malformed native shape or parameters as `invalid_input/native_input`.
2. An otherwise shaped MCP invocation with another tool name produces
   `unsupported_profile/operation`; no arguments of that tool are executed.
3. Check context presence, then implementation identity.
4. Produce a direct, partial declaration. The downstream unknown is retained.
5. A consumer validates core structure and every binding, then the exact coupled
   tuple and required body-digest extension. Unsupported critical extensions
   cannot be stripped. A failed binding yields
   `untrusted_evidence/description_binding`, never permission.

The complete native envelope, complete context and the profile manifest are
separate JSON digest preimages. The declared implementation preimage is
`{"id":"github-comment-bridge/1","kind":"declaration"}`. The declaration
artifact is `{"native":N,"context":C,"profile_digest":H(P)}`. Canonical JSON
uses the core's safe-integer subset of RFC 8785. No reference is fetched.
Local references are `urn:action-effect:github-comment:invocation`, `:context`,
`:implementation`, and `:declaration` respectively. Mapping id is the manifest
URI with `#mapping`, revision `1`, digest H(P). Evidence source is manifest URI.

Acceptance returns `accepted_partial/declared_partial`,
`authority: not_evaluated`, full description digest, and a checked projection:

```json
{"operation":"create_issue_comment","repository":"OndCo/Action-Effect-Bench","issue_number":1,"endpoint":"https://api.github.com/repos/OndCo/Action-Effect-Bench/issues/1/comments","body_sha256":"hex SHA-256 of exact UTF-8 body","body_bytes":14,"data_class":"synthetic-public"}
```

This illustration's digest label is explanatory, not a valid test vector.
Runtime equivalence compares checked projections. Full description digests
differ when the native lane differs; they are not cross-runtime semantic IDs.

## Remote Mutation

Exactly one effect, id `comment`, modality `may`, describes comment creation.
No observation, zero-effect bound, transitive completeness or causal graph is
inferred. Coverage and effect both refer to declaration evidence `declaration`.
Relations are empty. Exactly one `unobserved_descendants` entry retains the
manifest's unknown scope. Provider readback is a separate observation artifact.
GitHub's API description explicitly declares that creation triggers
notifications. The unknown scope concerns recipients, delivery and downstream
effects; it must not be read as claiming notifications do not happen.

## Create Comment

The operation is creation of one issue comment through GitHub REST. An update,
delete, release, repository creation or arbitrary request is unsupported.

## GitHub Issue

The resource slot is known, namespace from the manifest, and value
`owner/repo#issue_number`. Comparison is exact, conservatively case-sensitive.

## HTTPS Endpoint

The known destination value is
`https://api.github.com/repos/owner/repo/issues/issue_number/comments`.
Only this endpoint is constructed. Authenticated provider identity and actual
dispatch permission still need separate validation.

## Caller Classification

The known data slot retains the caller-configured class. Live demonstrations
accept only `synthetic-public`; text must contain no customer/private data.

## Body Bytes

The single quantity uses the manifest's byte URI, exact decimal string UTF-8
length, unit `byte`, scale `0`. It counts bytes, not JavaScript UTF-16 units.

## Body SHA256

The manifest's extension URI is required in `critical_extensions`. `extensions`
contains only that key, with lowercase 64-hex SHA-256 of the exact UTF-8 body.
It supplements, not replaces, the native-invocation binding.

## Authority and Unknowns

The experiment authorizer consumes the checked projection and separately loaded
principal/policy state. Grants couple repository, issue and class. Revocation,
principal mismatch, absent coupled grant or byte-limit violation denies.
Otherwise partial scope requires explicit `allow_partial_direct: true`; without
it, review is required. This policy accepts unknown provider descendants only
for a dedicated synthetic public test. No API response proves their absence.
Malformed policy or evaluator failure is an operational failure and withholds
dispatch, not a correct semantic denial. Policy checks and SaaS mutation are
not atomic across organizations; that time-of-check/use boundary remains.
