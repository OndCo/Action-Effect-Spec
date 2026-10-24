# Action Effect Spec

**Describe what an action may do, what supports that description, and what is
still unknown. Keep that separate from permission to execute.**

Release `0.2.0-draft.1`; core wire version `0.1.0-draft.1` is unchanged.
Public working draft, convened by Ond. Not an adopted
standard, certification program or production authorization service.

A tool name does not determine its consequences. Implementation, input,
destination and runtime context matter. This project proposes vendor-neutral
effect tuples with explicit evidence, applicability and coverage, so different
consumers can interpret the same description without sharing a control plane.

```text
Invocation + implementation + context
                  |
        Conditional effect description
        (coupled tuples + evidence + unknowns)
                  |
             Consumer checks
                  |
       Separate current authorization
       Separate execution and observation
```

## Start Here

- [Specification](SPEC.md): 28 identified core requirements.
- [Implemented profile](conformance/consumer-profile-v1.md): exact offline
  interface, byte rules, processing order and supported finite domain.
- [Opt-in v1.1 contract](conformance/consumer-profile-v1.1.md): explicit startup
  configuration handling and compound-error precedence; v1 remains the default.
- [GitHub issue-comment profile](profiles/github-issue-comment/README.md): an
  additive direct/partial domain profile, with runnable MCP/SDK, consumer and
  OPA examples in the companion benchmark. It does not require OSuite.
- [Partial profile accountability](conformance/profile-readiness.md): all 28
  CORE obligations, exact source/test anchors and explicit role-specific gaps.
- [Frozen GitHub candidate](profiles/github-issue-comment/candidate/README.md):
  additive offline component pins, not stable conformance or security certification.
- [Synthetic example](examples/partial-refund.json) and
  [binding semantics](examples/binding-profile.md).
- [JavaScript](implementations/javascript/cli.mjs) and
  [Python](implementations/python/cli.py) consumers, written separately.
- [Action Effect Bench](https://github.com/OndCo/Action-Effect-Bench): frozen
  development cases, separate expected-result/agreement checks and raw reports.
- [Existing-protocol relationships](profiles-and-integrations.md),
  [governance proposal](registry-and-governance.md) and
  [publication scope](PUBLICATION.md).

## Run Locally

Use Node.js 22+ and Python 3.9+; supported current language releases are
recommended. No package installation, account, telemetry, cloud resource or
OSuite dependency is required. From this repository's root:

```sh
node --test implementations/javascript/*.test.mjs
python3 -B -W error -m unittest discover -s implementations/python/tests
printf '%s\n' '{"id":"example","op":"hello"}' | node implementations/javascript/cli.mjs
printf '%s\n' '{"id":"example","op":"hello"}' | python3 -B implementations/python/cli.py
```

The current reproducibility targets are Linux and macOS; Windows has not been
qualified. Entry-point packaging corrections are recorded in [CHANGELOG.md](CHANGELOG.md).

Both CLIs use JSON-Lines. A `check` request carries `id`, `op: "check"` and
`document_b64`, the standard-base64 encoding of the raw description bytes.
The default fixture is synthetic. `--basis PATH` selects a caller-controlled
startup fixture; an incoming request cannot change that trust configuration.
Add `--contract offline-consumer-v1.1` to either CLI to select the clarified
contract explicitly. Contract identity and core wire identity are separate.

For a reproducible cross-consumer run, follow the benchmark's
[pinned-checkout instructions](https://github.com/OndCo/Action-Effect-Bench#reproduce-the-original-corpus).
The repository names on GitHub are capitalized, but those instructions explicitly
clone into lowercase sibling directories required by this draft runner.

## What Is Implemented

The consumers check one finite **partial USD-refund declaration** profile:
strict raw JSON, supported canonical bytes, structure, typed references,
fixture bindings and coupled effect projection. Malformed, unsupported,
untrusted and processing-failure outcomes remain distinct.

Every response carries `authority: not_evaluated`. `accepted_partial` does not
approve a refund, establish a complete effect bound or prove a real provider
observation. There is no signature verification, live grant/revocation check,
CEL evaluator, remote registry or runtime enforcement in these consumers.
The numeric profile is safe-integer JSON tokens, not full RFC 8785 binary64.

The benchmark contains 80 source-frozen public-development cases and 22
post-review regressions. Both are internal development evidence, not a protected
holdout or external institutional validation. The original
[40 design vectors](conformance/requirements.md) are not 40 executed tests;
the limited profile does not establish full CORE-001..028 conformance.

## Collaborate

Useful contributions include a third independently written consumer, a minimal
counterexample, or a narrowly specified new profile with explicit unknowns and
testable evidence. See [CONTRIBUTING.md](CONTRIBUTING.md) before sending material.
Report confidential vulnerabilities through [SECURITY.md](SECURITY.md), not a
public issue. No product purchase or paid membership is required.

## License and Status

The selected original code, documentation and synthetic fixtures are released
under the repository's [MIT license](LICENSE). This does not license unrelated
OSuite commercial code, third-party standards or protected research data.
No separate standards patent covenant, trademark right, institutional
endorsement or claim of universal legal compliance is made.
