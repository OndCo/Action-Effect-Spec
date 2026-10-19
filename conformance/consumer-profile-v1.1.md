# Offline Consumer Implementation Profile v1.1

Contract ID: `offline-consumer-v1.1`. Date: 19 October 2026.

This opt-in processing contract clarifies startup configuration and final-stage
error precedence for the finite synthetic refund consumer. It supplements
[v1](consumer-profile-v1.md); all v1 rules apply except where explicitly clarified
below. It is not a new core wire schema or a new refund domain profile.
`spec_version` remains `0.1.0-draft.1`, the profile URI remains
`https://example.org/profiles/refund/0.1.0-draft.1`, and the full canonical
manifest SHA-256 remains
`dddac40519b57620ca8b6fec558746ed8fb1f6ddf77263fd93cf5b2b582f2e00`.
The seven original contract/example files and their bytes are unchanged.

## Selection and Compatibility

Both existing entry points accept `--contract offline-consumer-v1.1`, optionally
with `--basis PATH` in either order. Contract selection is a caller-controlled
startup option, never a request field or a value inferred from a description.
Only `offline-consumer-v1` and `offline-consumer-v1.1` are supported. An unknown,
empty, missing-value or repeated contract option is a fatal startup error, not
an `unsupported_profile` response and not a fallback to v1.

Omitting `--contract`, or selecting `--contract offline-consumer-v1`, retains the
old v1 behavior and output. In particular, default `hello` gains no new field.
In v1.1, `hello` returns exactly:

```json
{"status":"capabilities","reason":"offline_snapshot","authority":"not_evaluated","spec_version":"0.1.0-draft.1","profile":"https://example.org/profiles/refund/0.1.0-draft.1","numeric_domain":"safe_integer_tokens_only","acceptance_cache":false,"contract":"offline-consumer-v1.1"}
```

The adapter wraps this result with the request's `id` as in v1. The extra
`contract` member identifies processing behavior, not a replacement
`spec_version` or profile binding. `check` and `canonicalize` result shapes,
description digests, framing, limits and continuation after rejected frames
are unchanged. A request or description with an extra `contract` field remains
invalid under the unchanged adapter or core structure rules, respectively.

The language-local API options are:

```javascript
const options = { contract: 'offline-consumer-v1.1' };
const check = createConsumer(options); // optional basis and profile as in v1
capabilities(options);
handleFrame(frameBytes, check, options); // optional third argument for hello
```

```python
consumer = Consumer(load_snapshot(basis_path), contract="offline-consumer-v1.1")
consumer.hello()
consumer.check(document_bytes)
```

API callers receive a startup exception for an unsupported contract or unusable
configuration, not a per-document result. Omitted API contract options retain
v1; JavaScript's `undefined` contract option also means omitted. Explicit `null`
or non-string contract values are invalid. The legacy Python `Consumer.hello()`
class-level query continues to report v1 capabilities.

## Startup Configuration Versus Applicability

Before serving any frame, the consumer MUST load and validate its caller-selected
local snapshot. The following are invalid configuration:

- An unreadable selected file, invalid UTF-8/JSON, duplicate decoded keys, invalid
  Unicode scalars, exceeded input/nesting limits, or numbers outside v1's
  safe-integer-token-only startup JSON subset.
- A manifest that does not match the pinned complete canonical content.
- A basis root that is not an object, or a missing/nonobject `input`,
  `implementation`, `context`, `mapping` or `declaration` member. Arrays, null,
  strings, booleans and numbers are not objects for this purpose.

Such configuration MUST terminate the CLI with a nonzero exit, no stdout frames
(including no `hello`), and a fixed diagnostic on stderr. Diagnostics MUST NOT
include fixture/input contents, supplied argument values, paths, secrets or a
stack trace. API exceptions likewise MUST NOT embed supplied configuration
contents. Only an omitted basis selection uses the bundled basis in v1.1;
an explicitly supplied null basis is invalid, not a request for that default.
For the JavaScript API this also applies to explicitly supplied `undefined`
basis/profile values. This opt-in rule does not change JavaScript v1's legacy
nullish configuration fallback.

The five required member objects may be empty at startup. Once their shape and
the startup JSON subset are valid, missing nested scalar fields or unsupported
scalar values are fixture applicability issues, not startup errors. For example,
`input.currency: "EUR"`, `input.order: null`, a wrong implementation version,
or `input.amount_minor: 7300` load successfully but cannot establish applicable
refund semantics. A present amount must be an exact decimal integer string in
0..999999999999; null, booleans, numbers, signs, leading zeros, whitespace and
out-of-range strings do not become unknown amounts. Only an absent
`input.amount_minor` permits the explicit unknown-amount projection from v1.

Applicability is a final-domain check, not a new early rejection stage. Document
syntax, numeric support, schema, local references, critical extensions, profile
binding, evidence scope and selected-member artifact binding still precede it.
For example, a stale invocation digest wins over unsupported fixture currency.
A malformed evidence source fails structure, and a source unequal to the
configured declaration issuer fails artifact binding, even if that issuer is
itself inapplicable. No stage is skipped to manufacture an applicability result.
After earlier stages succeed, unsupported fixture values MUST yield
`untrusted_evidence/applicability`, never an invented unknown or acceptance.

## Final Projection Precedence

Replace the ambiguity within v1 document-processing stage 10 with this ordered
sequence. This does not move any check ahead of stages 1 through 9:

1. **Fixture applicability.** Apply all finite synthetic fixture constraints in
   v1. Any failure yields `untrusted_evidence/applicability`, even if the
   description also has a wrong effect count or projection.
2. **Effect cardinality.** Require exactly one effect. Zero or multiple effects
   yield `untrusted_evidence/effect_projection`. Do not pick a first/last tuple
   or inspect one tuple's missing amount as if cardinality had succeeded.
3. **Missing required amount representation.** In that single effect, require a
   quantity named `https://example.org/quantities/amount` OR an
   `unknown_quantity` targeting that effect and exact name. If neither exists,
   yield `invalid_input/structure`, even with unrelated quantities or other
   projection defects. This is a final-domain structure error, not an earlier
   schema check. Duplicate, dangling, wrong-name and known/unknown-collision
   targets already fail reference validation at stage 5.
4. **Remaining coupled projection.** Apply all remaining v1 projection rules:
   category, operation, exact resource/destination/data-class tuple, no
   occurrence reference, empty relations, nonempty coverage/effect evidence
   references, unobserved descendants, and the exact known/unknown amount rule.
   Any mismatch yields `untrusted_evidence/effect_projection`. A represented
   but wrong amount/value/unit/scale, unknown amount when the fixture supplies
   one, or known amount when the fixture omits it belongs here, not at step 3.

Checks within step 4 have the same public result; their internal order is not
specified. Tuples are never recombined. If all stages succeed, return the v1
`accepted_partial/declared_partial` result. Every result retains
`authority: not_evaluated`; none is permission, observation or a checked bound.

The language-local tests exercise each pair of priority classes and repair the
higher-priority defect to expose the lower one. In particular:

| Simultaneous defects | First result |
| --- | --- |
| Bad applicability + cardinality, missing amount or coupled mismatch | `untrusted_evidence/applicability` |
| Multiple effects + missing required amount | `untrusted_evidence/effect_projection` |
| Multiple effects + coupled mismatch | `untrusted_evidence/effect_projection` |
| Missing amount representation + coupled mismatch | `invalid_input/structure` |
| Represented wrong amount + another coupled mismatch | `untrusted_evidence/effect_projection` |

## Verification and Claim Boundary

Run both suites locally without dependencies or network:

```sh
node --test implementations/javascript/*.test.mjs
python3 -B -W error -m unittest discover -s implementations/python/tests
```

CI runs both the frozen v1 and opt-in v1.1 test files through discovery. The
published v1 corpus continues to select v1 explicitly; its results are not
silently relabeled as v1.1 results.

These are exposed same-project implementation and regression tests, not external
validation, new holdouts, certification or full core conformance. The previously
separate JavaScript and Python implementations remain language-local; neither
imports or invokes the other. This hardening adds no domain, dependency,
network access, authorization, provider effect, cache or production-readiness
claim. Frozen v1 publications and historical results are not relabeled as v1.1.
