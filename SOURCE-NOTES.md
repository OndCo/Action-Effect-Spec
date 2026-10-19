# Primary Sources and Compatibility

Source inspection date: 18 October 2026, America/Toronto. This is original
editorial analysis of primary sources, not an endorsement by their publishers.
Version/status statements below refer to the inspected snapshots, not a promise
that a live `latest` URL will remain unchanged.

The [retrieval metadata](references/retrieval-manifest.json) preserves inspected
URLs, timestamps, success/failure status and available raw-byte SHA-256 values.
It omits local paths, command diagnostics and copyrighted source captures.
Those hashes are retrieval identities, not publisher signatures or a guarantee
that live URLs still serve the same bytes. No raw source archive is distributed.

## Meaning and Bytes

| Primary source | Design consequence |
| --- | --- |
| [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174), BCP 14 | Uppercase normative keywords, stable clause IDs and explicit scope; not an IETF submission. |
| [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259) and [RFC 7493](https://www.rfc-editor.org/rfc/rfc7493) | Reject decoded duplicate members and invalid Unicode before lossy parsing; represent exact quantities explicitly. |
| [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785), Informational | Canonical bytes and UTF-16 key ordering without Unicode normalization. The current consumer deliberately supports only safe-integer tokens, not full binary64/JCS. |
| [JSON Schema 2020-12](https://json-schema.org/draft/2020-12/json-schema-core) | Dialect and structural constraints are explicit; schema validity does not establish semantics, truth or authority. |
| [RFC 3986 Appendix A](https://www.rfc-editor.org/rfc/rfc3986#appendix-A) | Generic URI grammar, not HTTP-specific validation. Consumers do not fetch or normalize identifiers. This was additionally inspected during URI regression repair. |

## Authorization, Transport and Evidence

| Primary source and inspected status | Relationship, not a replacement claim |
| --- | --- |
| [OpenID AuthZEN Authorization API 1.0](https://openid.net/specs/authorization-api-1_0.html), Final | Reuse subject/action/resource/context decision exchange. An effect description is not a new grant, approved AuthZEN attribute or competing universal PDP API. |
| [RFC 9396](https://www.rfc-editor.org/rfc/rfc9396), OAuth RAR; [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700), OAuth security BCP | Requested scope, authenticated identity and current authorization are separate. Effect metadata cannot replace token/resource checks. |
| [RFC 9110 section 9.2.2](https://www.rfc-editor.org/rfc/rfc9110#section-9.2.2) | A timeout does not prove non-execution; retry/idempotency and provider evidence require their own contract. |
| [MCP selected 2025-11-25 schema](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/schema/2025-11-25/schema.ts) | Tool annotations are hints, not independently verified effects. This selected schema is not represented as the latest MCP version. |
| [A2A specification](https://a2a-protocol.org/latest/specification/), page identifying release 1.0.0 | A2A already includes authorization interactions and task lifecycle. Those mechanisms do not, by themselves, establish all transitive effects or provider completion. |
| [W3C PROV-DM](https://www.w3.org/TR/prov-dm/), Recommendation | Entity/activity/agent relations structure provenance; they do not authenticate facts. |
| [SCITT architecture record](https://datatracker.ietf.org/doc/draft-ietf-scitt-architecture/), inspected draft revision 22 | Possible future signed-claim transparency integration; not presented as a finalized RFC or authorization mechanism. |

## Optional Profiles

| Source | Boundary |
| --- | --- |
| [CEL language definition](https://github.com/google/cel-spec/blob/master/doc/langdef.md) | Conditions must pin language/error/unknown semantics and host limits. No CEL evaluator or interoperation claim is included in this release. |
| [TUF specification](https://theupdateframework.github.io/specification/latest/), inspected 1.0.37 | Candidate signed snapshot distribution, expiry and rollback defense; not semantic truth or instantaneous offline revocation. |
| [ECMA-427](https://ecma-international.org/publications-and-standards/standards/ecma-427/) and [purl](https://github.com/package-url/purl-spec) | Reuse package identity for implementation claims; package identity is not an execution occurrence or consequence bound. |
| [OpenTelemetry GenAI conventions](https://github.com/open-telemetry/semantic-conventions-genai), inspected Development status | Correlate observations without claiming enforcement or an already accepted effect attribute. |
| [OCSF](https://github.com/ocsf/ocsf-schema) | Possible event projection, not a pre-approved agent-effect class. |
| [OSV schema](https://ossf.github.io/osv-schema/), [Public Suffix List](https://publicsuffix.org/list/) and [CWE](https://cwe.mitre.org/about/index.html) | Learn explicit scope, lifecycle and local distribution; do not borrow vulnerability numbering authority or a DNS refresh interval for live authorization. |

## Access and Rights Limits

Some live MCP HTML endpoints timed out, so selected official Markdown/schema
sources were used. The old OpenTelemetry GenAI page supported its relocation
notice, not current normative semantics. A CVE rules landing page required
JavaScript; its retrieval did not establish inspection of substantive CNA rules.
Failed or limited retrievals are not silently counted as completed reviews.

No full ISO/IEEE standard certification, standards-essential patent search,
regulatory opinion or publisher approval was obtained. Referenced third-party
works retain their own rights; the repository's MIT license covers its selected
original contributions, not those external publications.
