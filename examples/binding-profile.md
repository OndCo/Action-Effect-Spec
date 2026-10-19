# Synthetic Profile and Binding Rules

This companion fixes the meaning of `refund-profile.json`. Its version-specific
URI is not a live endpoint. The description's `profile_digest` is SHA-256 of the
full RFC 8785 UTF-8 JSON manifest, not this prose or a fetched web page. The local
consumer configuration must map that URI to the approved manifest and this
revision's rules. A digest match provides integrity, not a reason to trust it.

The manifest selects no external component profiles. It pins the core revision,
synthetic domain, opaque identity, no-condition language and fixed local binding
rules. A changed rule requires a different profile revision, manifest and digest;
changing a prose rule while retaining this identity is not compatible.

## Binding Targets

The five rows of `reference_resolution` are a finite lookup table. They are not
instructions to interpret arbitrary URI fragments, fetch URLs, or open paths.
For each row, hash the complete top-level member named by `member` in the supplied
`synthetic-basis.json` fixture. For mapping resolution, both ID and revision must
match. The fixture's enclosing object, the locator string and the member object
have different hashes. Unlisted references cannot establish applicability.

Each selected member is an object. No field is removed before canonicalization;
duplicate JSON keys and invalid Unicode are rejected before selection. The
SHA-256 algorithm name and lowercase hexadecimal representation are explicit.
Binding non-JSON artifacts is not supported by this synthetic profile.

An accepted association covers the **entire** description, including its
`spec_version`, profile URI/digest, mapping ID/revision/digest, invocation,
implementation, context, effects, evidence, unknowns and extensions. A consumer
may retain the object plus this acceptance context or its complete canonical
digest in an existing envelope. This example produces no signature, permission
or accepted-bound receipt. Five matching hashes alone establish no combined
semantic claim.

## Meaning and Missing Information

The single effect is a declared possibility, not an observation. The order is
selected from `input.order`; the destination from `context.destination`; amount
and currency from `input.amount_minor` and `input.currency`. The implementation
name/version must exactly match the profile, and all named context members must
be available. Comparing these supplied declarations does not authenticate their
source or identify a real deployed binary.

The amount's integer coefficient `7300`, unit `USD` and scale `2` mean USD 73.00.
Only nonnegative coefficients up to `999999999999` and the unit/scale in the
manifest are supported here. Those bounds are a fictional profile constraint,
not a bank limit or a granted spending allowance. Another currency requires a
different supported profile, not a silent conversion. Other domain profiles
may define other units and signed values.

There is one named amount per refund effect. If required input is unavailable,
an `unknown_quantity` item targets its exact local effect ID and quantity URI;
that name cannot also appear as known, and duplicate unknown targets are invalid.
An empty amount list without that explicit target is invalid, not zero or
unlimited. A processing error is not a legitimate unknown quantity. This profile
requires the amount; other profiles explicitly distinguish inapplicable names.

All descendants remain unresolved. A declaration supports only what was declared;
the example supplies no checked upper bound, external execution, current grant,
provider attestation, identity resolution, CEL execution or critical extension.
Both fixture consistency and profile checking still require an implementation;
the editorial helper does not perform general evidence validation.
