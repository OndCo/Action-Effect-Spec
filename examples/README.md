# Synthetic Example Scope

`synthetic-basis.json` contains only newly authored fictional inputs, context,
implementation declaration and mapping. `partial-refund.json` describes a
possible direct effect with explicitly unknown descendants. It establishes no
real refund, real tool correctness, actual authority or completeness.

Digests refer to canonicalized components of the synthetic basis (ASCII-keyed,
string-only JSON objects in this example). They are recomputed by the local
editorial check. That check is not a complete RFC 8785 implementation, an evidence
verifier or a signature system. No network evidence reference is dereferenced.

All example.org addresses are illustrative. They do not allocate a live namespace
or invite a consumer to trust a server. The finite offline consumer profile now
checks these synthetic declarations; it does not measure real refund behavior,
complete domain conformance or provider safety.

`refund-profile.json` fixes the version-specific effective profile.
`binding-profile.md` defines exact local reference targets, digest preimages,
tuple projection and quantity semantics. The top-level profile digest is checked
in addition to the five basis digests. No generic fragment-resolution rule is
implied by strings such as `synthetic-basis.json#input`.
