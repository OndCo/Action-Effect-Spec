# Profiles, Applicability and Existing-Protocol Seams

Design companion to `SPEC.md`; profile proposals are not implemented adapters.
Core requirements remain authoritative within this draft. No upstream project
has approved these proposed mappings.

## 1. Core Versus Profiles

The core standardizes meaning and interchange, not all tool semantics. An
implementation declares profiles individually; unsupported is a legitimate
reported result, not a claim of universal coverage.

| Proposed profile | Scope and required additional evidence | Excluded claim |
| --- | --- | --- |
| Core description | Coupled tuples, quantities, unknowns, evidence references, versioned semantics | Correct inference of any arbitrary tool |
| Registry consumer | Applicable revisions, implementation comparators, dependencies and freshness | Registry presence establishes trust |
| CEL condition | Pinned language definition, declarations, host-function allowlist, limits and test vectors | Every CEL library is automatically interchangeable |
| Bounded workflow | Finite interpreter semantics, complete dependency accounting, checked effect bound | Arbitrary program or opaque SaaS completeness |
| Occurrence evidence | Provider/receiver-bound observations and distinct outcome states | Remote exactly-once/atomic commit from local logs |
| Signed distribution | Selected TUF version/configuration, trusted roots, expiry and recovery | Immediate offline revocation or semantic correctness |

Implementers need not implement every profile. Compatibility claims state their
profile, version, accepted domains and unsupported cases. No profile requires
PCAA, CAVA, BAF, AREG, Matoi, ZeroGate or DRS as a product dependency.

An exchange selects an immutable composite profile manifest and its content
digest. That manifest fixes core, domain, identity, binding and optional
condition semantics, with revisions/digests for component profiles. It declares
reference resolution, digest target types, supported extensions and failure
behavior. This avoids private out-of-band conventions masquerading as shared
semantics. The finite example in `examples/binding-profile.md` is intentionally
not a production refund mapper or a general reference resolver.

## 2. Integration Matrix

| Existing interface | Reuse | Do not claim / draft decision |
| --- | --- | --- |
| OpenID AuthZEN 1.0 | Existing subject/action/resource/context authorization exchange | No new generic allow/deny API. An effect description may inform a PDP under a separately agreed context profile; this is not an AuthZEN-standard field. |
| OAuth RAR, RFC 9396 | Structured requested authorization details | Requesting a consequence is not receiving permission. Any new authorization detail type needs its own interoperable definition. |
| OAuth security BCP, RFC 9700 | Existing authenticated, audience-bound access arrangements | Registry category/issuer must not replace identity, resource-server or token validation. |
| MCP selected 2025-11-25 schema | Tool identity/input schema and existing transport authorization | Tool annotations remain hints. A signed vendor declaration is still a declaration. Experimental metadata must use an owned extension namespace, never a forged standard `effects` field. |
| A2A | Task transport, lifecycle and authorization interaction | Authorization requests/task states do not prove effects or remote completion. Mapping is proposed, not tested cross-vendor interoperability. |
| purl / ECMA-427 | Identify packages used by a tool implementation | A package URL is not an invocation locator, executing artifact measurement or consequence bound. No new `aep:` scheme is necessary in the core. |
| OpenTelemetry | Correlate observations with spans/events using explicitly experimental attributes | Observability is not enforcement. The old GenAI-spans page moved to `semantic-conventions-genai`; the retrieved new definition has Development status. No proposed effect attribute is an approved stable OTel field. |
| OCSF | Project checked observations into security-event records | Event-schema membership is not action admission. Never present a proposed agent effect class as already approved by OCSF. |
| W3C PROV-DM | Separate entity, activity, agent and derivation relations | Provenance structure does not authenticate an observer or prove factual truth. |
| SCITT | Consider transparency for signed claims after a separate integration review | The retrieved record is draft revision 22 with no RFC number; do not call it an adopted RFC or use transparency as authorization. |

The inspected source status is recorded in [SOURCE-NOTES.md](SOURCE-NOTES.md). These
interfaces are complementary; a compatibility projection can lose information.
Each projection needs round-trip or explicitly lossy tests before release.

## 3. Condition Profile Proposal

Use CEL rather than a new expression language, but pin a specific language
revision and conformance suite before claiming interoperability. The installed
environment declares attribute names and types; expressions do not fetch data.
The base profile excludes user-defined I/O functions and implicit conversions
between strings, integers, floats and quantities. Regex, collection and macro
limits need explicit tests and implementation-specific cost accounting.

The final CEL result is interpreted according to CEL, not a made-up boolean
engine. For example, the inspected definition permits `error && false` to yield
false and `error || true` to yield true. An error in an irrelevant subexpression
is not automatically a host failure. A host timeout, crashed worker or invalid
expression configuration remains a processing failure, never a credited review.

Before a stable condition profile: freeze the source revision, supported
functions/macros, numerical limits, unknown-attribute behavior and expected
truth/error table; run two independent libraries against the same vectors. No
CEL evaluation or interoperability result is supplied by this draft package.

## 4. Domain Applicability Matrix

| Customer workflow | Reusable description | Evidence still needed at runtime | Unsafe assumption to avoid |
| --- | --- | --- | --- |
| Refund/payment | Exact operation, amount/unit, original payment target | Authenticated account, current grant, totals/limits, provider result | Any `transfer` label covers any recipient/amount |
| Documents/email | Read/write/send tuples with data class and recipient | Actual document/attachment classification, resolved recipient | Read-sensitive + send-public allows sending sensitive content |
| Git/release | Local/remote effects, ref/repository identity | Git config, hooks, filters, protected-ref behavior, actual result | `--force` proves history changed; a path keyword is execution intent |
| Cloud/IAM | Resource and authority changes, affected principal | Effective identity, inheritance, provider version/state, rollback behavior | Terraform's top-level name covers all provider side effects |
| MCP/SDK | Tool schemas and versioned invocation mapping | Server implementation identity, parameter and context bindings | Tool hint is third-party verified fact |
| Shell/process | Supported parser and declared subcommands | Expansions, aliases, working directory, environment, child processes | Arbitrary shell can be perfectly normalized by a keyword registry |
| Browser | Targeted DOM/API action and destination | Frame/origin, redirects, downloads, observed provider action | URL or button label proves final effect |
| Async/workflow | Explicit trigger and descendant relations | Current topology, queue consumers, claim/commit/reconciliation | Entry approval covers unknown downstream workers |
| Binary-only tool | Artifact identity plus declared/observed bounds | Sandbox observations or supported analysis, interception of unknown paths | Source unavailability implies safety or universal analyzability |
| Proprietary SaaS | Documented API semantics and scoped observations | Contracted provider behavior and reliable readback | A successful local POST proves all downstream effects |
| On-chain action | Chain, contract, method, value and recipient | Current chain state, delegate calls, finality/reorg assumptions | A simulated or submitted transaction is finalized |
| Industrial/physical action | Requested physical operation and units | Device state, certified safety controls, latency and hazard analysis | Digital effect conformance certifies physical safety |

These are coverage requirements, not claims that the profiles are implemented.
Generality means extensible representation and explicit limits, not that one
mapper solves all domains. Domain release claims require actual domain evidence.

## 5. OSuite Adaptation Without Lock-In

CAVA may consume checked effect tuples without changing existing action IDs.
AREG may distinguish predicted, observed and unknown effects. Matoi may reuse
evidence only while the relevant mapping/implementation/context dependencies
remain valid, including effective profiles, checker/trust changes, occurrence
scope and freshness. Cached bytes are not cached accepted evidence. BAF binds
the resulting scope to an explicit lease; PCAA retains
the deployer's authority and proof obligations. ZeroGate does not skip live
authorization because a registry record is cached. DRS tests declared control
coverage and cannot invent unobserved edges.

This is a design relationship, not evidence that the whole composition is
deployed. A non-OSuite authorizer or runtime can consume the same descriptions.
An OSuite implementation can be wrong while a competing implementation conforms.

Related collaborations on requested-authority tuples, runtime narrowing and
independent evaluation remain separate. They are not assigned ownership of this
registry, required to adopt its identifiers, or presumed to endorse this proposal.
Their reserved cases are excluded from this project's development data.
