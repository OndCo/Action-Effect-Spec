# Registry, Trust, Governance and Release Proposal

This is a governance proposal, not a legal opinion or a claim that independent
governance is operating. The current public draft uses the repository's
[MIT license](LICENSE); contribution intake follows [CONTRIBUTING.md](CONTRIBUTING.md).
This document creates no additional patent covenant, public namespace or
certification scheme.

## 1. Records and Evidence

A mapping record needs: persistent identity; immutable revision/content digest;
tool locator; implementation applicability with ecosystem comparator; condition
profile and expression; required context; complete effect-tuple templates;
evidence references; scope/exclusions; stability/status; and change rationale.

Record identifiers are descriptive references, not authorization tokens. A
tool's owner can author a declaration; publisher acceptance does not make it
independent verification. Evidence kinds are separate dimensions:

- declaration: who asserts behavior, for which implementation and conditions;
- observation: exact witness, input/context, observer and visibility limits;
- analysis: assumptions, analyzed semantics, bound and checker;
- review: reviewers, conflicts, independence and the proposition reviewed.

One observed Git witness does not support all Git versions `>=2.0`. A vendor
signature is not a trusted measurement of the executable. Review disagreement
does not disappear by majority vote without recording rationale and uncertainty.

## 2. Namespace and Change Management

Start with a provisional, versioned namespace and a public proposal process.
Do not claim CWE/CVE-like numbering authority or register an unnecessary URI
scheme. All `example.org` identifiers in this draft are reserved illustrative
addresses, not active registry allocations.

Separate concept definitions, mapping records, evidence artifacts and release
snapshots. Keep supersession/deprecation/withdrawal history and pinned old
revisions for reproducibility. Emergency withdrawal needs a documented consumer
response and incident notice; it cannot silently rewrite old evidence.

Revision identity is distinct from indefinite public availability of its payload.
If personal/confidential material, secrets or unauthorized content is discovered,
an identified incident owner can restrict affected hosted records/snapshots while
triaging rights and safety. Publish only a safe withdrawal/tombstone and corrective
revision; do not automatically expose identifying hashes or the sensitive reason.
Keep necessary evidence under justified restricted retention, with review/appeal
and a documented effect on reproducibility/results. Stopping distribution cannot
guarantee recall of third-party copies or revoke otherwise valid existing licenses.

Changes that increase apparent risk deserve scrutiny too: poisoning can create
denial of service and approval fatigue. The process therefore reviews both
understatement and overstatement, with impact evidence, affected profiles and
reproducible counterexamples. There is no globally sound scalar "safer change"
ordering across different policies and contexts.

Suggested change record: problem; existing behavior; proposed semantic change;
normative clauses affected; security/privacy implications; compatibility;
conformance vectors; external review; licensing/provenance; disposition.

## 3. Distribution and Local Use

Publish immutable, content-addressed snapshots with an explicit schema/profile
manifest. A TUF-based distribution profile can authenticate timely metadata
under configured root keys and thresholds. It still needs rotation/recovery
tests, client clock/freshness assumptions and bounded rollback behavior.

Normal lookups should use an installed local snapshot, not expose each customer
action to a central service. Registry freshness and live authorization freshness
are distinct. Offline operation declares its stale-data envelope and stops the
affected strict path when required freshness cannot be established.

Dependencies should identify relevant record revisions, concept definitions,
condition semantics and implementation/context facts. Selective invalidation is
allowed only with demonstrated dependency completeness. Neither rebuilding
everything nor caching everything is a required algorithm.

## 4. Contribution and Institutional Independence

Proposed roles: spec editors, registry reviewers, profile maintainers, security
contacts, benchmark custodians and implementers. Role overlap/conflicts must be
visible. The benchmark's protected input/label access cannot be inherited merely
because someone maintains the spec.

Initially Ond can convene the project, but a neutral specification cannot promise
Ond permanent veto, perpetual exclusive maintenance or exclusive commercial use.
Any later foundation transfer needs an actual agreed process; no named foundation,
university or standards body is treated as a committed sponsor.

A proposed acceptance rule is documented technical review plus reproducible
evidence by people with relevant expertise. Counting two signatures is not proof
of independence. Contributors identify affiliation and conflicts; high-impact
changes need review outside the submitting vendor where feasible.

Before soliciting, accepting, merging, redistributing or substantively incorporating
outside material, require an approved versioned inbound mechanism to be effective
and record contributor authority and applicable assent/permissions, or a separately
documented sufficient existing grant. This covers normative suggestions, diagrams,
mapping/profile contributions, cases/labels and manuscript material as well as code.
Unsolicited material may be triaged but not adopted or publicly redistributed before
this gate; later terms are not presumed retroactive. DCO sign-off, CLA, copyright
license and patent license are not interchangeable. Do not silently borrow a
standards body's agreement or present an unsigned agreement as effective.

Before claiming independent governance, identify actual decision-makers,
appointment/removal powers, funding, common corporate control, conflicts and
appeals. The submitting vendor has no deciding vote on its disputed record or
score. Recusals apply before computing an independent quorum; when that quorum
is absent, defer or explicitly label a convenor-controlled decision. Neither
sponsorship nor a technical-maintainer role buys exceptions or vetoes. These are
proposed requirements; the present editorial work is convenor-led, not neutral
governance already in operation.

## 5. Current License and Future Policy Decisions

The first public draft retains the MIT license selected when the owner created
this repository. It covers the selected original reference code, prose and
synthetic fixtures, not unrelated product code or third-party source material.
No extra standards-essential patent commitment is enacted. The following matrix
records alternatives considered for future versions, not competing current terms.

| Asset | Candidate approach, subject to approval | Important boundary |
| --- | --- | --- |
| New minimal reference code | Consider Apache-2.0 or another approved permissive license | Apache's contributor patent provisions have real consequences; do not infer rights to commercial OSuite code |
| Specification prose and diagrams | Consider CC BY 4.0 for text plus a separately reviewed standards patent policy | Copyright permission does not itself grant patent/trademark rights |
| New synthetic registry/test data | Consider CDLA-Permissive-2.0 or CC BY 4.0 after provenance review | Neither choice launders third-party restrictions or customer privacy |
| Third-party source and datasets | Original licenses and notices, source-by-source permission | Retrieved standards pages are local research copies, not automatic redistribution |
| Commercial runtime/product | Remains outside the new public project unless explicitly licensed | Public interchange does not require exposing tenant data, keys or service internals |
| Manuscript | Decide preprint/journal rights separately | Permissions for other work do not authorize new joint work |

Record a patent-policy decision separately at editorial, external-intake and
stable-profile stages: disclosure-only, a scoped non-assertion mechanism, or a
defined royalty-free commitment. Specify authorized entities, claims, covered
versions, exclusions, reciprocity/defensive terms, withdrawal and transfer effects.
Disclosure-only can be a deliberate choice but supplies no implementer patent
promise. An authorized editorial draft need not pretend to have completed an RF
regime or patent clearance. Any eventual commitment uses approved legal instruments,
not this explanatory table or another body's borrowed boilerplate.

The alternatives above are not enacted by their inclusion here. Before changing
the current terms or making a stable-profile patent commitment, obtain the
appropriate ownership, contributor-rights, patent, trademark and privacy review.
This public draft makes no representation of completed patent clearance or
jurisdiction-wide legal review. No patent search can guarantee freedom to operate.

## 6. Conformance, Branding and Acquisition

Publish precise test statements, not a broad "secure agent" badge. A claim names
the spec/profile/suite versions, implementation and evaluator. Self-testing,
independent testing and a formally governed certification program are distinct.
Any marks program requires separate ownership, usage and enforcement rules.

Acquisition readiness benefits from clean provenance, auditable rights, sustained
maintenance, adoption and reliable technology. It does not justify hiding
dependencies, presenting private code as a neutral standard, or retaining secret
exceptions for OSuite. A future buyer of Ond would not automatically own exclusive
control of an open specification or its independent community.

## 7. Privacy and Regulatory Alignment

Disable telemetry by default. An internal tool name, resource URI, repository,
tenant or destination can be personal/confidential information without arguments.
Any optional telemetry needs defined authority, minimization, retention/deletion,
security and a jurisdiction-appropriate legal basis. A k-anonymity threshold is
not a guarantee of anonymity.

Technical conformance can support evidence collection under risk-management or
security programs. It does not certify GDPR/PIPEDA/EU AI Act/ISO/SOC compliance,
establish a lawful purpose, transfer accountability or validate physical safety.
Sector/jurisdiction reviews depend on the actual deployment and contracts.

## 8. Release Stages

The editorial publication scope is recorded in [PUBLICATION.md](PUBLICATION.md),
with clear limitations, a security contact and an owner-approved public release.
It does not require claiming completed implementations. A stable profile release
additionally requires a stable namespace, maintainer commitment and independently
interoperating implementations, frozen profile semantics and a validated suite
with coverage of all applicable mandatory obligations. A limited draft-vector
report is not full core/profile conformance. Failure or non-support of a mandatory
obligation prevents that scope's conformance claim; genuinely optional unimplemented
profiles do not invalidate supported core scope. Public GitHub creation, standards
proposals and external messages are separate user decisions.
