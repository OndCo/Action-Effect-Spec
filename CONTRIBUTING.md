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

No separate CLA fee is required. This contribution process does not obtain a
standards-essential patent promise or guarantee freedom to operate. Known
rights concerns can be raised privately without publishing restricted details.

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
