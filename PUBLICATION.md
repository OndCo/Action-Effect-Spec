# Public Draft Scope

Editorial date: 18 October 2026, America/Toronto. Machine run timestamps use UTC.

## Included Material

This repository contains the proposed specification, profile/governance design,
JSON Schema, synthetic examples, 40 design-only vectors, the finite
`offline-consumer-v1` contract, separately written JavaScript/Python consumers
and their unit tests. CI, source notes and contribution/security instructions
are publication support, not additional semantic capabilities.

The exact file list is the Git tree of the selected commit. The benchmark pins
that commit and records individual source hashes. Do not cite a mutable branch
as the identity of an experiment.

The original internal development logs, research coordination notes, prior
local run archives, raw third-party source captures, commercial application,
customer data, credentials and protected evaluation cases are not part of this
release. The original local research archive has not been overwritten.

## Frozen Documents and Publication Layout

The seven shared contract/example files used to author the original 80 cases
remain byte-identical. Their SHA-256 values are checked by the benchmark before
regenerating or verifying its corpus. Publication does not silently rewrite
normative text or expected outcomes.

Section 11 of the frozen `SPEC.md` mentions pre-publication sibling paths
`../research/standards-crosswalk.md` and `../research/retrieval-manifest.json`.
Those are historical layout references, not required files or network lookups.
The public replacement is [SOURCE-NOTES.md](SOURCE-NOTES.md) and its
[source metadata](references/retrieval-manifest.json). Raw captured standards
are not redistributed. The consumer and reproducer do not read those paths.

The frozen consumer profile also excludes another research collaboration's
holdouts. This is an exclusion, not a collaborator endorsement, assignment of
work or inclusion of their unpublished results. Named institutional partners
are not implied by this release.

## Construction and Evidence

The JavaScript and Python implementations were initially written separately
from the same public contract and examples, without translating, importing or
reading the other candidate. A separate same-project case-authoring session
used the seven frozen documents before inspecting candidate output. Internal
review subsequently supplied counterexamples and corrections.

This was AI-assisted development within one project. Multiple implementation
languages or authoring sessions do not make it an independent laboratory study.
Shared design assumptions and correlated mistakes remain possible. Public
expected-result checks and implementation agreement are reported separately.

The companion benchmark's release reports measure the selected public sources
afresh. Earlier local reports are retained in the internal archive, not claimed
to describe a different public source snapshot. No missing raw transcript is
manufactured or replaced by an assertion of external verification.

## Open Boundaries

- Full core conformance, live authorization and real provider effects remain
  unimplemented by this profile.
- Missing/non-object trusted startup fixture members are rejected during startup
  by both consumers; the next profile revision should spell out this boundary
  more explicitly than the current invalid-configuration/applicability split.
- Simultaneous final-stage projection defects need a fully specified precedence
  before a stable profile. Current finite cases do not establish every ordering.
- A stable general profile needs new domains, implementations and independent
  review. Public development cases cannot be relabeled as untouched holdouts.

## Rights and Stewardship

The user-created repository's MIT license is retained for the selected original
work. No additional patent grant or standards-essential non-assertion promise is
created by this note. Patent policy, formal independent governance and a stable
namespace remain future decisions, not completed legal clearance.

Ond is the initial convenor. There is no external standards-body approval,
independent governing board, public registry service or certification badge.
The proposed broader governance process remains in
[registry-and-governance.md](registry-and-governance.md).
