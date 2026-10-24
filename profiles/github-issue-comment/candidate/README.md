# GitHub Issue Comment 1 Candidate

Candidate ID: `github-issue-comment-1-candidate.1`. **Partial, not stable, not
security certified. `externallyIndependentEvaluations=0`.** This additive
[manifest](manifest.json) freezes the existing experimental
[`github-issue-comment/1`](../README.md) profile at Spec commit
`a9b86f4b529a5e330c2a9bf1b8c4c259a7b36e40`; it does not promote that profile or
replace any original identifiers or normative text.

## Scope and Compatibility

One declared `create_issue_comment` effect via the existing SDK/MCP envelopes:
`may`, direct/partial, exact case-sensitive identity, exact UTF-8 body bytes and
body SHA-256. The body limit remains 8192 bytes; issue numbers remain 1..2147483647.
Provider notifications, webhooks and internal descendants stay explicit unknowns.
This does not imply notifications do not happen.

No authority grant, signature/CEL/current-revocation check, remote registry,
enforcement, observation proof, transitive bound, arbitrary GitHub operation,
SaaS attestation, DLP or cross-organization atomicity is added. Processing keeps
the original distinction between invalid input, unsupported operation/extension,
untrusted bindings and operational failure. Acceptance remains
`accepted_partial/declared_partial`, `authority: not_evaluated`. Neither a hash
match nor an operational failure is a correct authorization decision.

`offline-consumer-v1` remains the refund default and v1.1 remains opt-in; neither
becomes a GitHub consumer. The pinned external GitHub consumer is described in
the [accountability matrix](../../../conformance/profile-readiness.md), not
implemented or verified here. The sidecar changes no processing precedence.

## Noncircular Pins

The manifest lists **four** normative components: the unchanged `SPEC.md`, core
JSON schema, original domain `profile.json` and original domain `README.md`.
Each component hash is SHA-256 of the complete raw file bytes, including JSON
whitespace and Markdown line endings. There is no component selector or network
resolution. Implementation code, tests, reports, this README, the candidate
manifest itself and its verifier are not normative hash components.

The candidate manifest's own complete raw-byte SHA-256 is pinned separately in
the verifier, outside that component set:

```text
2c9afb7c2710d1d3303b9ac282a1fc302f69bf17a36108dd36e7e875b02c9289
```

The original wire `profile_digest` is still SHA-256 of the complete original
profile JSON using the supported safe-integer RFC 8785 subset:
`c4c062d8181d3e0d2cd04a0667ec6711d159bd61db5eeeae95217918e80350b3`.
Do not substitute the candidate manifest, its raw-byte pin or the README for
that preimage. This is an out-of-band snapshot, not a repair or redefinition of
the historical CORE-011 effective-profile binding.

## Verify and Trust

From the Spec repository root:

```sh
node scripts/verify-candidate.mjs
node --test scripts/tests/candidate.test.mjs
```

The verifier supports only this candidate and manifest version 1, with no
network or test execution. It rejects missing/changed/nonregular files,
symlinks, path escapes, duplicate JSON keys, unknown keys, unsupported versions,
identity/claim changes and any manifest-byte change. It reads at most 64 KiB of
manifest data, depth 64, and four files of at most 1 MiB each. Over-limit input
fails rather than truncating success. `--root PATH` selects an offline copy;
success exits 0, failure exits 2 on stderr without input/path content.

Trust the reviewed verifier/manifest pin and a quiescent checkout obtained by
your own trusted process. This tool does not authenticate its own source,
signatures, origin, remote currentness or concurrent hostile filesystem changes.
The caller-selected root is resolved locally (system aliases above it may
resolve); a symlink root itself or any symlink component below it is rejected.
Changing a component and its advertised hash still fails the separate manifest
pin. Changed semantics or bytes require a new candidate revision, not silent
replacement. No publication or test execution can certify future stable text.

The repository's [MIT license](../../../LICENSE) remains unchanged. No added
patent covenant, warranty, endorsement or legal-compliance promise is made.
