# Draft Change Record

## Ambit Context Note (26 October 2026)

The README now states that this specification is the effects layer of Ambit,
an open protocol convened by Ond, and that Ambit's other layers remain research.
No normative text, schema, example, profile, consumer or frozen file changed.

## 0.2.0-draft.1

Added an opt-in `offline-consumer-v1.1` contract with startup configuration
rejection, explicit contract identity and deterministic final projection error
precedence. Added paired-defect and legacy-compatibility tests in JavaScript and
Python. The seven frozen files, core wire version and default v1 behavior remain
unchanged, including the documented historical JS null-option fallback.

Added the GitHub issue-comment profile: exact native invocation and body binding,
partial direct scope, explicit provider-descendant unknowns, and a distinct
authorization integration in the companion benchmark. This is a narrowly
implemented profile, not a claim that legacy refund consumers understand GitHub.

## Public-Checkout Entry Point Repair

During clean-clone reproduction on 18 October 2026 (America/Toronto), an absolute
path through a filesystem symlink caused the JavaScript CLI to exit zero without
reading a request or producing a response. The entry-point guard compared a
lexical argument path with Node's resolved module path. This also affected the
companion benchmark's two command-line entry points.

The guard now compares resolved filesystem identities. A new regression requires
a symlinked CLI invocation to return an actual capability response; a separate
stdin-import control preserves import-safe behavior. The regression failed on
the previous implementation before the fix. Python and the semantic evaluator
were not changed.

The original seven source-frozen contract/example files remain byte-identical.
No test expectation, effect semantics, numeric domain, authority decision or
signature claim was changed. Benchmark reports before this fix remain historical
reports of their named source snapshot, not evidence that symlinked entry points
were covered. The companion benchmark pins the corrected commit for new runs.
