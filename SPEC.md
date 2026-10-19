# Conditional Action Effect Descriptions

Version `0.1.0-draft.1` | 18 October 2026 | America/Toronto

**Status:** proposed normative text for review. Not an IETF, OpenID, W3C, IEEE,
ISO, MCP, A2A or other adopted standard. No interoperability certification or
general-purpose effect inference is claimed.

## 1. Purpose and Non-Goals

An invocation's name or syntax is insufficient to determine its consequences.
Its implementation, arguments, credentials, configuration, environment and
downstream services may matter. This draft defines an interchange contract for
conditional effect descriptions and their evidence, not a universal effect
detector. An unresolved effect is not an authorization decision.

The core is independent of model vendors, transports, policy languages,
commercial control planes, CAVA fingerprints and PCAA receipts. Adopters may
use existing PDPs, enforcement points and evidence stores. No OSuite endpoint,
account, module or proprietary identifier is necessary to implement it.

Out of scope: granting authority; proving arbitrary program behavior; proving
absence of hidden SaaS effects from a trace; remote transaction atomicity;
cross-organization legal compliance; automatic discovery of every consequence
path; a globally correct taxonomy; and prevention of all covert channels.

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT,
RECOMMENDED, NOT RECOMMENDED, MAY, and OPTIONAL in this document are to be
interpreted as described in BCP 14 (RFC 2119 and RFC 8174) when, and only when,
they appear in all capitals. All normative obligations below have CORE IDs.

## 2. Roles and Trust Boundaries

**Producer:** describes effects, possibly using a mapper or analyzer.
**Registry publisher:** publishes versioned mapping records and evidence links.
**Evidence checker:** tests a specified claim within a stated profile.
**Consumer:** interprets a description under configured trust and capability.
**Authority:** decides what the authenticated principal is permitted to do.
**Enforcement point:** controls an actual execution boundary.
**Observer:** records evidence of an occurrence or provider outcome.

A party may perform multiple roles, but a role name creates no trust. A vendor
may truthfully describe its tool without being independent of that tool.

**CORE-001:** A consumer MUST keep description acceptance, evidence checking,
authorization, dispatch and observed completion as distinct states. Acceptance
of a description MUST NOT itself grant execution permission.

**CORE-002:** A consumer MUST record the trust basis for material facts: issuer,
acquisition mechanism, implementation identity, context binding and evidence
scope. Transport authentication or a valid signature MUST NOT be interpreted
as proof that the described semantics or observations are correct.

## 3. Semantic Objects

A description D binds an invocation reference, mapping revision, implementation
claim and context reference to a set of effect tuples and evidence. The core
does not redefine the adopter's semantic action ID or execution occurrence ID.

An effect tuple is conceptually:

`(category, operation, resource, destination, data_class, quantities, modality)`.

Identifiers denote profile-defined concepts. `resource` and `destination` have
an explicit known, unknown or none state; an empty string is not a substitute.
Quantities carry exact value, unit and scale. Effects may have evidence-backed
relations such as `may_trigger`; the relation does not establish causation by
itself. Conditions and implementation assumptions belong to a mapping profile.

**CORE-003:** A consumer MUST evaluate coupled fields within each tuple. It
MUST NOT combine a resource from one alternative with a destination, quantity
or data class from another to construct an unasserted tuple.

**CORE-004:** Distinct destinations/resources in one description MUST use
separate tuples or an explicitly supported collection profile. A consumer MUST
NOT assume an unstated Cartesian product, wildcard scope or collection
membership. A relation MUST reference existing effect IDs in the description.
Effect IDs MUST be unique within `effects`, and evidence IDs MUST be unique
within `evidence`, using exact string comparison. Each relation endpoint and
quantity-unknown target MUST resolve to exactly one local effect; every
`evidence_refs` entry MUST resolve to exactly one local evidence item. Duplicate,
mistyped or dangling targets MUST produce `invalid_input`, without guessing,
remote lookup or choosing a first/last match. Resolution alone establishes no
support for the referencing claim.

**CORE-005:** Category identifiers MUST resolve to definitions from a configured,
versioned profile. A familiar label, an unknown namespace, an unresolved URI or
an empty effect list by itself MUST NOT be interpreted as harmlessness or
completeness. A slot with `state: none` MUST NOT imply the entire invocation has
no effects.
Identifier resolution MUST NOT automatically fetch or execute untrusted URLs.

## 4. Possibility, Observation and Coverage

The core distinguishes `may` (possible under the stated conditions) from
`observed` (reported for a particular occurrence). It does not define `must
happen` or infer universal behavior from an observed witness. A future profile
may add a proof obligation for inevitability without redefining these terms.

Let E be the set of effects possible under an actual implementation and state.
A sound upper bound U would establish `E subseteq U` within explicit assumptions.
An observed set O only reports a witnessed subset, not that `E subseteq O`.
An ordinary registry entry generally establishes neither complete bound.

**CORE-006:** A producer MUST declare modality, direct/transitive scope and
coverage as `partial` or `bounded_claim`. An observed effect MUST identify its
occurrence and supporting observation evidence. A consumer MUST NOT upgrade
`may` to `observed`, an observation to an upper bound, or direct to transitive
coverage without additional profile-defined evidence.

**CORE-007:** A `bounded_claim` MUST identify its implementation, invocation and
context bindings, assumptions and supporting evidence. A consumer MUST treat
it as unestablished until its configured profile checker accepts those exact
bindings and assumptions. A `verified` flag, digest or registry signature alone
does not meet this obligation.
An explicitly checked empty upper bound establishes absence only within its
declared effect universe, scope and assumptions; it does not establish general
harmlessness. Unknowns inside that claimed bound prevent its establishment.

**CORE-008:** The consumer MUST preserve known effects alongside unknowns.
Unknown destination, incomplete descendants, unsupported tooling, conflicting
evidence and unresolved identity MUST remain distinguishable. Unknowns MUST
NOT erase a known effect or invent a benign value.

## 5. Syntax, Identity and Numerical Meaning

The initial exchange is a JSON document using the proposed JSON Schema 2020-12
dialect. Schema validity is only structural validity; the obligations here and
profile checks remain necessary. There is no new registered media type, URI
scheme, authorization endpoint or global number allocator in this draft.

**CORE-009:** Inputs MUST be UTF-8 JSON with unique member names, valid Unicode
scalar values and no non-finite numbers. Consumers MUST detect duplicate names
before a normal parser discards them. Invalid encoding, duplicates and malformed
input MUST be reported as invalid input, not semantic uncertainty.

**CORE-010:** Monetary amounts, counters and other decision-relevant quantities
MUST use profile-defined exact decimal integer strings with explicit unit and
scale. The base syntax is `0` or an optional minus sign followed by a nonzero
digit and decimal digits. `-0`, leading zeros and exponent notation are invalid.
Consumers MUST NOT round, silently convert units/currencies or use lossy binary
floating point for their authorization interpretation. A profile may disallow
negative values; the synthetic refund profile does so. The mathematical amount
is `integer(value) * 10^(-integer(scale))` in the stated unit. A profile MUST
define permitted units/scales, signs/ranges, and which named quantities each
operation requires or treats as inapplicable. Within a tuple, a quantity name
MUST occur at most once. An unresolved required quantity MUST be omitted from
`quantities` and represented by an `unknown_quantity` entry targeting that
effect ID and exact quantity name. A name MUST NOT be both known and unknown.
Duplicate unknown targets for the same effect and quantity MUST be rejected.
An absent required name without such a target is invalid input; omission MUST
NOT mean zero, unlimited authority or an inapplicable constraint. Alternative
amounts require separate tuples or a separately supported collection profile.

**CORE-011:** Identity comparison MUST follow the declared profile. By default,
opaque identity strings are compared exactly and are case-sensitive. Consumers
MUST NOT infer URI, email, path, alias, case-folded or Unicode-normalized
equivalence without a supported resolver/profile and bound evidence.
The `profile` URI MUST identify an immutable, version-specific effective profile
manifest; `profile_digest` MUST bind that manifest's full RFC 8785 JSON content.
It MUST fix the spec revision and domain, identity, condition and binding
semantics, including immutable revisions/digests of any component profiles.
Consumers MUST use configured resolution and verify this binding, not interpret
a mutable `latest` URL or an unavailable private convention as a shared profile.

**CORE-012:** When a profile uses a JSON content digest, it MUST apply RFC 8785
after validating this document's stricter input and quantity rules, use an
explicit algorithm identifier, and include the complete relevant object.
Arrays retain order; strings are not silently Unicode-normalized. The digest
MUST NOT be treated as a signature, authority grant or semantic correctness proof.
The selected profile MUST specify the preimage's type, exact object selection,
encoding and reference-resolution rules. A locator, an enclosing file and a
selected member are different possible targets, not interchangeable preimages.
Non-JSON artifacts require a separately declared byte-level digest rule. A
reference MUST NOT acquire ambient base-URI or fragment semantics by accident.

## 6. Bindings and Registry Mappings

A locator identifies a tool interface; an implementation binding identifies
what actually implements it. A version string may be useful but insufficient.
Artifacts, deployment measurements, authenticated provider identities or scoped
observations have different strengths. Unsupported binaries remain supported
as identifiers, not automatically as analyzable implementations.

**CORE-013:** A mapping MUST state applicable implementation/version constraints,
required context, its own immutable revision and evidence sources. Version-range
syntax MUST identify the ecosystem comparator. A consumer MUST NOT assume all
future releases are covered by one witness or apply generic SemVer to every
ecosystem. Unresolved applicability is not a positive match.

**CORE-014:** A consumer using a description for a concrete invocation MUST bind
it to that invocation and the relevant current context. Observations MUST also
bind an occurrence. A matching tool name, category, action ID or timestamp
alone MUST NOT substitute for these bindings.
Any stored or attested acceptance MUST associate the complete description,
effective profile digest, mapping revision/digest and those concrete bindings.
Verifying disconnected component hashes MUST NOT be represented as evidence
that an accepted statement covers their combination. This obligation does not
define a replacement signature envelope or authorize execution.

**CORE-015:** Evidence MUST distinguish declarations, observations, analyses and
reviews. Each item MUST carry an identified source, an artifact reference AND
its digest, along with applicable scope. The digest MUST cover the artifact
selected by that reference under the effective profile's rules. Supporting
evidence MUST cover the claimed effect/occurrence/bound under that profile; a
resolved reference, digest or prose scope label alone is insufficient.
Reviewer count MUST NOT imply independence,
semantic truth or completeness; conflicting evidence remains visible.

**CORE-016:** Conditions MUST be interpreted only by an explicitly supported,
versioned condition profile. The proposed CEL profile is optional, not a core
dependency. An evaluator MUST distinguish true, false, semantic unknown and
evaluation failure; it MUST NOT turn an exception or resource-limit failure
into a successful match or credited semantic review.

## 7. Results and Failure Semantics

Description processing results are distinct from policy decisions:

| Processing result | Meaning | Not a claim of |
| --- | --- | --- |
| `accepted_description` | Supported syntax and semantic obligations checked | Permission, completeness or successful execution |
| `accepted_partial` | Usable known effects plus explicit unresolved portions | Safety of unresolved portions |
| `unsupported_profile` | Required semantic capability unavailable | Correct policy rejection |
| `invalid_input` | Encoding/schema/structural requirement violated | Legitimate uncertainty |
| `untrusted_evidence` | Necessary evidence is not accepted by trust configuration | Proof that no effect occurred |
| `evaluation_failure` | Parser/mapper/checker/worker failed or exceeded bounds | Correct semantic review/block |

**CORE-017:** Implementations MUST keep processing result, policy decision and
execution outcome in separate fields/interfaces. Withholding execution after
an error MUST NOT be scored or presented as a correct semantic decision.

**CORE-018:** An enforcement integration requiring a profile MUST withhold the
affected execution if necessary semantics/evidence cannot be established. It
MUST explain the missing obligation rather than silently downgrade assurance.
An existing trusted applicable denial is not canceled by unrelated uncertainty.
Human approval cannot make an invalid proof valid or establish a missing fact.

## 8. Evolution, Caching and Trust Distribution

**CORE-019:** A published identifier MUST NOT be reassigned to a different
meaning. Records MUST have immutable revisions and content digests, and explicit
experimental/stable/deprecated/withdrawn states. A change affecting semantics,
conditions, evidence or profile interpretation MUST create a new revision.
Withdrawal for secrets, privacy, licensing or safety MUST NOT reassign an old
identifier or silently replace its bytes. A safe tombstone MUST distinguish
unavailability from a usable old revision without repeating sensitive content.
Immutability does not require indefinite public retention of harmful payloads.

**CORE-020:** A consumer MUST distinguish caching bytes from caching their prior
acceptance. Acceptance reuse MUST bind the complete description, relevant
record revisions, implementation, all effective profiles, checker revision,
trust-configuration identity/epoch, and profile-defined evidence/context
freshness and dependencies. A changed relevant dependency, expired evidence or
unknown currentness MUST trigger revalidation or invalidate acceptance reuse.
Occurrence-bound observations MUST remain bound to that occurrence. Consumers
MAY avoid invalidating unrelated records only when dependency coverage is
established; untracked dependency is not evidence of irrelevance. This does not
require a global epoch service or prevent retaining rejected bytes for audit.

**CORE-021:** A signed registry distribution profile MUST specify root trust,
rotation, compromise recovery, expiry, rollback protection and maximum offline
freshness. Expired necessary metadata MUST NOT be silently accepted as current.
An offline snapshot MUST NOT claim immediate knowledge of remote revocation.
TUF is a candidate distribution mechanism, not a semantic correctness checker.

**CORE-022:** Reusing an effect description MUST NOT bypass the authority
system's current grant, expiry, revocation, quota, occurrence or replay checks.
The core does not cache permission and does not replace OAuth or a PDP.

**CORE-023:** Consumers MUST advertise implemented spec/profile versions and
understand every listed critical extension before accepting its description.
Unknown critical extensions MUST yield `unsupported_profile`. Noncritical
extensions MUST NOT widen effects, coverage or authority, or change core
interpretation. Removing an unknown critical field and retrying is not a
conforming compatibility strategy.
Each extension ID MUST identify immutable versioned semantics. A payload-bearing
extension's ID MUST match its payload key in `extensions` by exact string
equality; marker-only extensions are exempt from that key requirement. Its
definition MUST state
whether it is marker-only or requires a payload and how that payload validates.
Unknown required versions MUST yield `unsupported_profile`; missing/malformed
required payloads or forbidden payloads MUST yield `invalid_input`. A marker-only
extension has no payload key. Semantic extensions MUST be marked critical.

## 9. Security, Privacy and Resource Bounds

**CORE-024:** A processing profile MUST publish finite limits for input bytes,
nesting, effects, relations, evidence entries, quantity digits and condition
evaluation. Limit failures MUST produce explicit failure results, not truncated
success. The initial illustrative local limits are 1 MiB UTF-8 input, 64 nesting
levels, 256 effects, 1024 relations, 256 evidence entries and 78 integer digits;
these are reviewable interoperability defaults, not measured capacity claims.

**CORE-025:** A consumer MUST treat locators, evidence links, schema references
and expressions as untrusted data. It MUST NOT execute example commands,
dereference arbitrary remote references, fetch internal URLs or disclose
credentials merely to process a description. Condition profiles MUST constrain
host functions and prohibit undeclared network/file side effects.

**CORE-026:** Telemetry MUST be disabled by default. Any opt-in reporting MUST
define consent/authority, minimization, retention, access and deletion policy.
Locators can identify internal systems; removing arguments or adding a
k-anonymity threshold MUST NOT be claimed to establish anonymization or legal
compliance. Public registry records MUST exclude live secrets and customer data.

**CORE-027:** Observed completion MUST be supported by a receiver/provider
observation bound to the actual occurrence and covered effect. A local admission,
HTTP timeout, queued task or actor self-report MUST NOT establish remote commit.
An execution profile MUST distinguish confirmed, partial, unknown and conflicting
outcomes and specify retry/idempotency responsibilities.

## 10. Conformance and Standards Status

**CORE-028:** A conformance claim MUST identify the exact specification revision,
profiles, suite version/hash, implementation identity and passed/failed/unsupported
cases. It MUST distinguish self-testing from independent evaluation and MUST NOT
claim regulatory certification, standards-body endorsement or general security.
A full conformance claim MUST require a frozen target profile and evidence for
all applicable mandatory obligations, with none failed or unsupported. A
limited test report MUST label its coverage rather than imply full conformance;
a draft report MUST NOT claim compliance with a future stable revision. Optional
profile support MUST be reported separately from required-profile obligations.

Core conformance does not require a particular effect taxonomy, CEL evaluator,
OSuite deployment, Matoi runtime, online registry, model, authorization API or
benchmark score. Optional profiles have separately identified obligations.
Every normative requirement maps to cases in `conformance/requirements.md`.
This draft supplies design vectors, not an implemented full conformance suite.

## 11. References and Compatibility Notes

Primary sources: RFC 2119, RFC 8174, RFC 8259, RFC 7493, RFC 8785; JSON Schema
2020-12; OpenID AuthZEN Authorization API 1.0; RFC 9396 and RFC 9700; RFC 9110;
MCP selected published schema; CEL language specification; TUF specification;
W3C PROV-DM. Exact inspected sources, status and retrieval identities are in
`../research/standards-crosswalk.md` and `../research/retrieval-manifest.json`.

This draft adds no IANA registration and makes no standards-essential patent
representation. Public contribution and patent policies require explicit
approval before adoption or public solicitation.
