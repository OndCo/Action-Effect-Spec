# Contributing

This is a public working draft. You can inspect, implement and test it without
an OSuite account, purchase, membership payment or vendor permission.

## Useful First Contributions

- Implement the finite consumer profile in another language using only the
  contract and examples; disclose any exposure to existing implementations.
- Report a minimal synthetic input, actual output, expected output and the
  specification clause that makes the difference important.
- Propose one bounded domain profile with coupled fields, unknowns, evidence
  obligations, unsupported cases and deterministic test vectors.
- Review a normative clause or a compatibility projection against a pinned
  primary source. Do not infer upstream acceptance from a proposed mapping.

Questions and disagreements are welcome in GitHub issues. Do not post credentials,
customer traces, embargoed cases or a confidential vulnerability. Use
[SECURITY.md](SECURITY.md) for sensitive reports.

## Rights and Provenance

Before original code, specification text, diagrams or cases can be incorporated,
the contributor must explicitly confirm that they are authorized to provide the
material under this repository's MIT license. Use the pull request checklist.
Record original sources, applicable third-party notices, affiliation and relevant
conflicts. Do not copy standards text or a dataset merely because it is public.
Material with different or unclear rights needs separate review before adoption.
Silence, an unsolicited issue or later terms do not retroactively grant rights.

### Inbound Mechanism (DRAFT, not in effect)

No inbound mechanism has been selected or approved. The options below are
drafts for maintainer and legal review; this text does not choose one. Before
any outside material is merged, maintainers must select exactly one option,
give it a version string, and record the selection in this section.

- **Option A: Developer Certificate of Origin (DCO).** The contributor adds a
  `Signed-off-by:` trailer to each commit to certify the DCO text. The DCO
  contains no express patent grant; counsel should confirm its effect.
- **Option B: Contributor License Agreement (CLA).** The contributor signs an
  agreement with a version identifier before merge. Its terms, any grants
  (including patent terms) and its signing mechanism are not yet drafted.
- **Option C: Inbound grant under MIT.** Contributions are provided under the
  repository's MIT license, with authorization confirmed in the pull request.
  Whether this is sufficient for the project's needs is a legal question.

Selection record (maintainers to complete):

- Selected mechanism: pending
- Version string: pending
- Where confirmations are recorded: pending
- How they are checked before merge: pending
- Legal review: pending

This contribution process does not obtain a standards-essential patent promise
or guarantee freedom to operate. Known rights concerns can be raised privately
without publishing restricted details.

## Status Gates

These gates separate publishing editorial and documentation work from accepting
outside material. Drafting a mechanism does not approve or activate it.

- **Gate A (safe to publish):** disclaimers are accurate; no verification or
  certification claim is made without evidence; test evidence is attached with
  commands, exit codes and versions; a private vulnerability route is
  documented. Maintainers may merge documentation under Gate A.
- **Gate B (safe for external contributions):** an inbound mechanism is selected,
  versioned and reviewed by counsel; a marks policy is approved and its owner
  and policy URL are verified; the review process is reproducible. Until Gate B
  is passed, do not merge outside code, specification text or cases, and do not
  issue any badge.

## Review and Versioning

A proposed change describes the problem, affected CORE/profile clauses,
compatibility and security implications, tests and observed failures. Changes
to a frozen input or expected outcome require an explicit new version and
provenance note; do not edit an old experiment to make it pass.

Run the unit commands in [README.md](README.md). Reproduce the matching pinned
benchmark and retain failures. A new profile does not inherit evidence from the
finite refund profile. Unknowns and unsupported inputs must not become grants.

Maintainers review contributions; publication is not automatic acceptance.
Current review is convenor-led. A dispute about a maintainer's own implementation
must not be called independently adjudicated without a genuinely independent
reviewer. If independence is absent, label the outcome internal or defer it.
