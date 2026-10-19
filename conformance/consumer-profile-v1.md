# Offline Consumer Implementation Profile v1

Implementation design approved in principle by the user's request to begin
independently written consumers. Client date: 2026-10-19. This narrows an
implementation target; it does not redefine `0.1.0-draft.1` or claim full core
conformance. The previous editorial evidence remains historical.

## Scope and Independent Construction

Write one JavaScript and one Python consumer, sharing only this interface,
SPEC, JSON Schema and public example/profile data. Do not translate, import or
call the other implementation. Do not import OSuite or previous Matoi code.
Separate same-project authors are not independent external institutions.

Implement strict byte parsing, schema-equivalent shape checks, local semantic
reference integrity, explicit support/trust errors, selected-member digests and
one finite synthetic refund projection. No network, signatures, live authority,
provider access, effect-bound analysis, CEL, caching, hidden data or deployment.

## Files and Runtime

JavaScript entry: `implementations/javascript/cli.mjs` (Node >=22).
Python entry: `implementations/python/cli.py` (Python >=3.9, standard library).
Both run from any current directory. Both accept `--basis PATH`; default is the
project's `examples/synthetic-basis.json`, loaded once as a startup snapshot.
The profile manifest is `examples/refund-profile.json`, pinned to SHA-256
`dddac40519b57620ca8b6fec558746ed8fb1f6ddf77263fd93cf5b2b582f2e00`.
An invalid/unreadable startup configuration exits nonzero on stderr. It is not
converted to a semantic review. No installation or paid service is required.

Only the caller launching the process selects configuration; a request cannot
change trusted fixtures, fetch a reference, refresh state or grant authority.
Snapshot comparison is not proof of current external state or truthful evidence.

## Local JSON-Lines Adapter

This is a local test adapter, not a new wire protocol for AuthZEN, MCP or A2A.
One UTF-8 JSON request per line, each an object with exactly these fields:

```json
{"id":"case-1","op":"check","document_b64":"BASE64_OF_RAW_DESCRIPTION_BYTES"}
```

`id` is a string of 1..128 Unicode scalar values. `op` is `check`, `canonicalize`
or `hello`; `hello` has only `id` and `op`, the others also require
`document_b64`. Base64 uses the standard alphabet, canonical padding and no
whitespace. Raw bytes, not already-parsed objects, preserve duplicate-member,
encoding and number tests. Limit a frame to 2 MiB excluding newline; raw document
limit is 1 MiB. Read bounded frames and drain an oversized frame before continuing.
A final nonempty frame without a newline is processed. Blank frames are invalid.

Output exactly one JSON object per frame, stdout free of logs:

```json
{"id":"case-1","result":{"status":"accepted_partial","reason":"declared_partial","authority":"not_evaluated","description_digest":"SHA256_HEX","effect_count":1,"unresolved_count":1}}
```

Failures have only `status`, `reason`, `authority`. Invalid framing uses `id:null`
and `invalid_input/transport`; oversize framing uses `id:null` and
`evaluation_failure/limit_exceeded`. Unexpected code failure uses
`evaluation_failure/internal_error`, no input, stack or secret in output.
An invalid document echoes a valid adapter ID, never the document content.
Continue serving later frames after an individual rejected request.

`hello` returns `status: capabilities`, `reason: offline_snapshot`,
`authority: not_evaluated`, `spec_version: 0.1.0-draft.1`,
`profile: https://example.org/profiles/refund/0.1.0-draft.1`,
`numeric_domain: safe_integer_tokens_only`, `acceptance_cache: false`.

`canonicalize` returns `status: canonicalized`, `reason: supported_subset`,
`authority: not_evaluated`, `canonical_b64` and `sha256`. This diagnostic is not
description acceptance. Supported values are objects/arrays, scalar-valid
strings, null, booleans and integer JSON tokens within +/-9007199254740991.
Numbers with a fraction/exponent or outside that range yield
`unsupported_profile/numeric_domain`, not a claim they are invalid JSON.
`-0` canonicalizes to `0`; quantity string `"-0"` is still schema-invalid.
Sort keys by UTF-16 code units per RFC 8785, preserve arrays and strings, escape
as JSON/ECMAScript requires. No Unicode normalization or full binary64/JCS claim.

## Document Processing Order and Results

For a syntactically valid adapter request, use this precedence:

1. Document bytes >1 MiB or container nesting >64: `evaluation_failure/limit_exceeded`.
   Root container depth is 1. Reject invalid UTF-8, BOM, malformed JSON, duplicate
   decoded member names, lone surrogate strings/keys and non-finite tokens as
   `invalid_input/syntax`. Validate complete syntax before numeric-domain rejection.
2. Syntactically valid but unsupported numeric token: `unsupported_profile/numeric_domain`.
3. For `canonicalize`, return the diagnostic result. For `check`, require a root
   object with string `spec_version`; missing/type error is `invalid_input/structure`.
   A different string version is `unsupported_profile/spec_version`.
4. Enforce all constraints of the published effect-description schema, including
   required/extra members, enum/type/length/array limits and URI fields. Failure
   is `invalid_input/structure`. URI validation requires an absolute scheme,
   nonempty scheme-specific part, ASCII URI characters, valid percent escapes,
   no controls/whitespace/backslash; it performs no network or normalization.
5. Duplicate effect/evidence IDs; dangling relation/evidence targets; duplicate
   quantity names; unknown-quantity target absent/wrong/duplicate, or also known:
   `invalid_input/references`. Compare decoded strings exactly. A quantity target
   must identify an existing effect and the selected profile's amount name.
6. Any critical extension: `unsupported_profile/critical_extension`. This consumer
   implements none; it never strips and retries. Noncritical metadata is retained
   in the full digest, ignored for semantic widening, not executed.
7. Unknown profile URI: `unsupported_profile/profile`. Wrong digest for the pinned
   profile: `untrusted_evidence/profile_binding`. No URL resolution is attempted.
8. Coverage other than direct/partial, observed modality or non-declaration
   evidence: `unsupported_profile/evidence_scope`. This consumer cannot check
   an empty upper bound or provider observation and does not fake doing so.
9. Invocation/implementation/context references and mapping ID/revision must match
   the profile's finite local table. Evidence artifact references must match its
   declaration row. Any mismatch: `untrusted_evidence/artifact_binding`. Recompute
   SHA-256 on the complete selected JSON member, never the enclosing file or URL.
   Any digest mismatch has the same result. Every evidence source must equal
   `basis.declaration.issuer` and be a declaration; scope text is not proof.
10. Enforce the synthetic projection below. Bad fixture applicability:
    `untrusted_evidence/applicability`; description disagrees with supported
    projection: `untrusted_evidence/effect_projection`.
11. Return `accepted_partial/declared_partial`, complete canonical description
    SHA-256, number of effects and number of unknown entries. This accepts an
    internally bound declaration only, not truth, authority, a bound or execution.

Stages 4/5 are schema/semantic-reference validation, not policy decisions.
Resource-limit failures never earn correct block/review credit.

## Finite Synthetic Projection

The fixture must have object members `input`, `implementation`, `context`,
`mapping`, `declaration`. Implementation name/version are exactly the profile's
`synthetic-refund-tool` / `1.0.0`; visibility is `declared`. Input operation is
`refund`; `order` and context `account` are nonempty scalar strings; currency is
`USD`. Context destination is `original-payment`, environment `synthetic`.
Mapping ID/revision match the manifest; declaration issuer is an absolute URI.
Remaining fixture strings are bound, not interpreted as code or trusted facts.

Exactly one effect is described, with any unique local `effect_id`:
category `https://example.org/effects/funds-transfer/1`, operation
`https://example.org/operations/refund/1`; known resource namespace
`https://example.org/resource-types/order` with `input.order`; known destination
namespace `https://example.org/destination-types/payment` with context destination;
known data namespace `https://example.org/classification`, value
`synthetic-transaction`; modality `may`, no `occurrence_ref`.
Relations are empty. Coverage and the effect each reference at least one local
declaration evidence item. At least one `unobserved_descendants` unknown remains.

If `input.amount_minor` is present, it must be a nonnegative exact integer string
in the profile range 0..999999999999. The effect has exactly one matching amount,
unit USD, scale `"2"`, and no unknown quantity. If absent, amounts are empty and
exactly one `unknown_quantity` targets this effect and the profile's amount URI.
Missing explicit amount/unknown representation is `invalid_input/structure` at
this final domain stage; a represented but wrong value/unit/scale is
`untrusted_evidence/effect_projection`. Invalid fixture values are applicability
failures, not invented unknowns. Other unknown kinds remain recorded but do not
erase the known projection. No current authorization is evaluated in either case.

## Test and Claim Boundaries

Freeze public development cases before comparing consumer outputs. A separate
case author derives expected statuses/canonical bytes from this interface and
the spec, not either implementation. These cases are exposed internal tests,
not Shuwen holdouts or an external independent benchmark. Preserve discrepancies,
fix records and all-run outcomes; never count two agreeing bugs as correctness.

Results identify exact source/case hashes and runtimes, separate expected-result
matches from cross-consumer agreement, and report unsupported features. Faulty
adapters must make the harness fail, not appear as successful rejections. No
speed ranking, production readiness or full CORE-001..028 conformance follows.
