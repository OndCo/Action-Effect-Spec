"""Exposed, language-local regression tests for the opt-in v1.1 contract."""

import copy
import inspect
from pathlib import Path
import subprocess
import sys
import tempfile

from support import (CLI, ConsumerCase, basis, bound_description, example, failure,
                     fixture_digest, public_bytes, request, unknown_amount, wire)


V1 = "offline-consumer-v1"
V11 = "offline-consumer-v1.1"
AMOUNT = "https://example.org/quantities/amount"
SECRET = "synthetic-private-marker-do-not-echo"
MISSING = object()
HELLO = dict(failure("capabilities", "offline_snapshot"), spec_version="0.1.0-draft.1",
             profile="https://example.org/profiles/refund/0.1.0-draft.1",
             numeric_domain="safe_integer_tokens_only", acceptance_cache=False)
HELLO_V11 = dict(HELLO, contract=V11)
ACCEPTED = dict(failure("accepted_partial", "declared_partial"),
                description_digest="a357beff955d1372cb7aede84dd1b1baaa4c375008672c821bdbae1e27f62377",
                effect_count=1, unresolved_count=1)
CANONICAL = dict(failure("canonicalized", "supported_subset"),
                 canonical_b64="eyJhIjpbdHJ1ZSxudWxsXSwieiI6MH0=",
                 sha256="4097289243fbf05814aa5d808b55f34ed4f900c17916bdb8f636eb04ea630ae8")


def frame(op="hello", raw=None, identifier="case"):
    return request(raw, op=op, identifier=identifier)


def residual(document, defect):
    effect = document["effects"][0]
    if defect in ("category", "operation"):
        effect[defect] = "urn:wrong"
    elif defect in ("resource", "destination", "data_class"):
        effect[defect]["value"] = "wrong-value"
    elif defect == "occurrence":
        effect["occurrence_ref"] = "not-observed"
    elif defect == "relations":
        document["relations"] = [{"from": "effect-1", "to": "effect-1",
                                   "kind": "urn:relation", "evidence_refs": ["decl-1"]}]
    elif defect == "coverage_evidence":
        document["coverage"]["evidence_refs"] = []
    elif defect == "effect_evidence":
        effect["evidence_refs"] = []
    elif defect == "descendants":
        document["unknowns"] = []
    else:
        raise AssertionError("unknown test defect")


class ConsumerV11Tests(ConsumerCase):
    def selected(self, fixture=MISSING, contract=V11):
        self.assertIn("contract", inspect.signature(self.consumer_module.Consumer).parameters,
                      "Consumer needs an explicit contract API option")
        snapshot = self.configuration.Snapshot.from_bytes(
            public_bytes("synthetic-basis.json") if fixture is MISSING else wire(fixture),
            public_bytes("refund-profile.json"))
        return self.consumer_module.Consumer(snapshot, contract=contract)

    def evaluate(self, document, fixture=MISSING):
        return self.selected(fixture).check(wire(document))

    def test_v11_hello_identifies_contract_not_a_new_wire_schema(self):
        consumer = self.selected()
        self.assertEqual(consumer.hello(), HELLO_V11)
        self.assertEqual(consumer.check(wire(example())), ACCEPTED)
        self.assertEqual(consumer.canonicalize(b'{"z":-0,"a":[true,null]}'), CANONICAL)

    def test_default_and_explicit_v1_api_outputs_and_class_hello_are_unchanged(self):
        self.assertEqual(self.consumer.hello(), HELLO)
        self.assertEqual(self.consumer_module.Consumer.hello(), HELLO)
        self.assertEqual(self.consumer.check(wire(example())), ACCEPTED)
        self.assertEqual(self.selected(contract=V1).hello(), HELLO)
        self.assertEqual(self.selected(contract=V1).check(wire(example())), ACCEPTED)

    def test_bad_api_contract_is_a_sanitized_configuration_exception(self):
        for contract in (SECRET, "", None, True, 1, [], {"secret": SECRET}):
            with self.subTest(contract=contract):
                with self.assertRaises(self.configuration.ConfigurationError) as caught:
                    self.selected(contract=contract)
                self.assertNotIn(SECRET, str(caught.exception))

    def test_nonobject_roots_and_missing_or_nonobject_members_are_startup_errors(self):
        self.selected()
        invalid = [None, [], False, 0, SECRET]
        for member in ("input", "implementation", "context", "mapping", "declaration"):
            for value in (MISSING, None, [], False, 0, SECRET):
                fixture = basis()
                if value is MISSING:
                    del fixture[member]
                else:
                    fixture[member] = value
                invalid.append(fixture)
        for fixture in invalid:
            with self.assertRaises(self.configuration.ConfigurationError) as caught:
                self.selected(fixture)
            self.assertNotIn(SECRET, str(caught.exception))

    def test_unsupported_fixture_scalars_and_absent_nested_fields_are_applicability(self):
        changes = [("input", "operation", "charge"), ("input", "order", None), ("input", "order", ""),
                   ("input", "currency", "EUR"), ("implementation", "name", "other-tool"),
                   ("implementation", "version", "2"), ("implementation", "visibility", "measured"),
                   ("context", "account", False), ("context", "destination", "other"),
                   ("context", "environment", "production"), ("mapping", "id", "urn:other"),
                   ("mapping", "revision", "2")]
        changes.extend(("input", "amount_minor", value) for value in (
            None, True, 7300, "-0", "-1", "00", "1e2", "1.0", "1\n", "1000000000000"))
        changes.extend((member, key, MISSING) for member, key in (
            ("input", "order"), ("implementation", "version"), ("context", "account"), ("mapping", "revision")))
        for member, key, value in changes:
            with self.subTest(member=member, key=key, value=value):
                fixture = basis()
                if value is MISSING:
                    del fixture[member][key]
                else:
                    fixture[member][key] = value
                self.assertEqual(self.evaluate(bound_description(fixture), fixture),
                                 failure("untrusted_evidence", "applicability"))

    def test_empty_objects_load_and_issuer_applicability_does_not_bypass_binding(self):
        for member in ("input", "implementation", "context", "mapping", "declaration"):
            fixture, document = basis(), example()
            fixture[member] = {}
            document["evidence"] = []
            document["coverage"]["evidence_refs"] = []
            document["effects"][0]["evidence_refs"] = []
            self.assertEqual(self.evaluate(bound_description(fixture, document), fixture),
                             failure("untrusted_evidence", "applicability"))
        fixture = basis()
        fixture["declaration"]["issuer"] = SECRET
        document = bound_description(fixture)
        self.assertEqual(self.evaluate(document, fixture), failure("invalid_input", "structure"))
        document["evidence"][0]["source"] = "urn:other-issuer"
        self.assertEqual(self.evaluate(document, fixture), failure("untrusted_evidence", "artifact_binding"))
        document["evidence"] = []
        document["coverage"]["evidence_refs"] = []
        document["effects"][0]["evidence_refs"] = []
        self.assertEqual(self.evaluate(document, fixture), failure("untrusted_evidence", "applicability"))

    def test_paired_applicability_precedes_each_later_projection_class(self):
        for defect, status, reason in (("cardinality", "untrusted_evidence", "effect_projection"),
                                       ("missing", "invalid_input", "structure"),
                                       ("resource", "untrusted_evidence", "effect_projection")):
            with self.subTest(defect=defect):
                fixture = basis()
                fixture["input"]["currency"] = "EUR"
                document = bound_description(fixture)
                if defect == "cardinality":
                    document["effects"] = []
                elif defect == "missing":
                    document["effects"][0]["quantities"] = []
                else:
                    residual(document, defect)
                self.assertEqual(self.evaluate(document, fixture), failure("untrusted_evidence", "applicability"))
                fixture["input"]["currency"] = "USD"
                self.assertEqual(self.evaluate(bound_description(fixture, document), fixture), failure(status, reason))

    def test_paired_cardinality_precedes_missing_amount_in_both_tuple_orders(self):
        for reverse in (False, True):
            document = example()
            document["effects"][0]["quantities"] = []
            other = copy.deepcopy(example()["effects"][0])
            other["effect_id"] = "other-effect"
            document["effects"].append(other)
            if reverse:
                document["effects"].reverse()
            self.assertEqual(self.evaluate(document), failure("untrusted_evidence", "effect_projection"))
            document["effects"] = [effect for effect in document["effects"] if effect["effect_id"] == "effect-1"]
            self.assertEqual(self.evaluate(document), failure("invalid_input", "structure"))
            document["effects"][0]["quantities"] = example()["effects"][0]["quantities"]
            self.assertEqual(self.evaluate(document), ACCEPTED)

    def test_paired_cardinality_never_selects_a_good_tuple_over_a_coupled_mismatch(self):
        document = example()
        document["effects"][0]["destination"]["value"] = "wrong-payment"
        document["effects"].append(dict(copy.deepcopy(example()["effects"][0]), effect_id="other-effect"))
        self.assertEqual(self.evaluate(document), failure("untrusted_evidence", "effect_projection"))
        document["effects"].pop()
        self.assertEqual(self.evaluate(document), failure("untrusted_evidence", "effect_projection"))
        document["effects"][0]["destination"]["value"] = "original-payment"
        self.assertEqual(self.evaluate(document), ACCEPTED)

    def test_paired_missing_representation_precedes_all_remaining_projection_constraints(self):
        for defect in ("category", "operation", "resource", "destination", "data_class", "occurrence",
                       "relations", "coverage_evidence", "effect_evidence", "descendants"):
            for amount_present in (True, False):
                for unrelated_quantity in (False, True):
                    with self.subTest(defect=defect, amount_present=amount_present, unrelated=unrelated_quantity):
                        fixture = basis()
                        if not amount_present:
                            del fixture["input"]["amount_minor"]
                        document = bound_description(fixture)
                        document["effects"][0]["quantities"] = ([{
                            "name": "urn:other-quantity", "value": "1", "unit": "USD", "scale": "2",
                        }] if unrelated_quantity else [])
                        residual(document, defect)
                        self.assertEqual(self.evaluate(document, fixture), failure("invalid_input", "structure"))
                        if amount_present:
                            document["effects"][0]["quantities"] = example()["effects"][0]["quantities"]
                        else:
                            unknown_amount(document)
                        self.assertEqual(self.evaluate(document, fixture), failure("untrusted_evidence", "effect_projection"))

    def test_represented_wrong_amounts_and_other_coupled_defects_remain_projection_mismatches(self):
        for key, value in (("value", "7301"), ("unit", "EUR"), ("scale", "3")):
            document = example()
            document["effects"][0]["quantities"][0][key] = value
            document["effects"][0]["resource"]["value"] = "wrong"
            self.assertEqual(self.evaluate(document), failure("untrusted_evidence", "effect_projection"))
            document["effects"][0]["resource"]["value"] = "order-42"
            self.assertEqual(self.evaluate(document), failure("untrusted_evidence", "effect_projection"))
        self.assertEqual(self.evaluate(unknown_amount(example())), failure("untrusted_evidence", "effect_projection"))
        fixture = basis()
        del fixture["input"]["amount_minor"]
        self.assertEqual(self.evaluate(bound_description(fixture), fixture), failure("untrusted_evidence", "effect_projection"))
        document = unknown_amount(bound_description(fixture))
        self.assertEqual(self.evaluate(document, fixture), dict(
            ACCEPTED, description_digest=fixture_digest(document), unresolved_count=2))

    def test_earlier_document_gates_precede_final_applicability_and_missing_amounts(self):
        fixture = basis()
        fixture["input"]["currency"] = "EUR"
        cases = (("structure", "invalid_input"), ("references", "invalid_input"),
                 ("critical_extension", "unsupported_profile"), ("profile", "unsupported_profile"),
                 ("profile_binding", "untrusted_evidence"), ("evidence_scope", "unsupported_profile"),
                 ("artifact_binding", "untrusted_evidence"))
        for reason, status in cases:
            document = bound_description(fixture)
            document["effects"][0]["quantities"] = []
            if reason == "structure":
                document["contract"] = V11
            elif reason == "references":
                document["unknowns"].append({"code": "unknown_quantity", "scope": "bad target",
                                             "target": {"effect_id": "absent", "quantity_name": AMOUNT}})
            elif reason == "critical_extension":
                document["critical_extensions"] = ["urn:critical:unknown"]
            elif reason == "profile":
                document["profile"] = "urn:unknown-profile"
            elif reason == "profile_binding":
                document["profile_digest"]["value"] = "0" * 64
            elif reason == "evidence_scope":
                document["coverage"]["scope"] = "transitive"
            else:
                document["invocation"]["digest"]["value"] = "0" * 64
            self.assertEqual(self.evaluate(document, fixture), failure(status, reason))


class CommandLineV11Tests(ConsumerCase):
    def execute(self, data, args=()):
        return subprocess.run([sys.executable, "-B", str(CLI), *args], input=data,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd="/", timeout=10)

    def successful(self, process, rows):
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(process.stderr, b"")
        self.assertEqual(process.stdout, b"".join(wire(row) + b"\n" for row in rows))

    def fatal(self, process):
        self.assertEqual(process.returncode, 2)
        self.assertEqual(process.stdout, b"")
        self.assertTrue(process.stderr)
        self.assertNotIn(SECRET.encode(), process.stderr)
        self.assertNotIn(b"Traceback", process.stderr)

    def test_default_stdout_is_byte_compatible_and_only_opt_in_hello_adds_contract(self):
        data = b"\n".join((frame(), frame("check"), frame("canonicalize", b'{"z":-0,"a":[true,null]}'),
                            b"not-json", frame("check", b'{"spec_version":"future"}'), frame("check", SECRET.encode())))
        rows = [{"id": "case", "result": HELLO}, {"id": "case", "result": ACCEPTED}, {"id": "case", "result": CANONICAL},
                {"id": None, "result": failure("invalid_input", "transport")},
                {"id": "case", "result": failure("unsupported_profile", "spec_version")},
                {"id": "case", "result": failure("invalid_input", "syntax")}]
        self.successful(self.execute(data), rows)
        self.successful(self.execute(data, ("--contract", V1)), rows)
        self.successful(self.execute(data, ("--contract", V11)), [{"id": "case", "result": HELLO_V11}] + rows[1:])

    def test_unknown_malformed_frames_and_documents_are_rejected_then_service_continues(self):
        bad_frames = [wire({"id": "case", "op": SECRET}), b'{"id":"a","id":"b","op":"hello"}',
                      wire({"id": "case", "op": "check", "document_b64": "e31="}),
                      wire({"id": "case", "op": "hello", "contract": V1})]
        documents = [(b'{"a":1,"a":2}', "invalid_input", "syntax"), (b"\xff", "invalid_input", "syntax"),
                     (b'{"spec_version":"future","n":1.5,}', "invalid_input", "syntax"),
                     (b"1.5", "unsupported_profile", "numeric_domain"), (b"null", "invalid_input", "structure"),
                     (wire({"spec_version": V11}), "unsupported_profile", "spec_version")]
        data = b"\n".join(bad_frames + [frame("check", raw) for raw, _, _ in documents] + [frame()])
        rows = ([{"id": None, "result": failure("invalid_input", "transport")} for _ in bad_frames]
                + [{"id": "case", "result": failure(status, reason)} for _, status, reason in documents]
                + [{"id": "case", "result": HELLO_V11}])
        self.successful(self.execute(data, ("--contract", V11)), rows)

    def test_document_and_frame_limits_and_recovery_are_unchanged(self):
        data = b"\n".join((b" " * (2 * 1024 * 1024 + 1), frame("check", b" " * (1024 * 1024 + 1)), frame()))
        self.successful(self.execute(data, ("--contract", V11)), [
            {"id": None, "result": failure("evaluation_failure", "limit_exceeded")},
            {"id": "case", "result": failure("evaluation_failure", "limit_exceeded")},
            {"id": "case", "result": HELLO_V11},
        ])

    def test_basis_and_contract_options_compose_in_either_order_and_scalars_are_not_startup_failures(self):
        with tempfile.TemporaryDirectory(prefix="effect-v11-") as directory:
            path = Path(directory) / (SECRET + ".json")
            fixture = basis()
            fixture["input"]["currency"] = "EUR"
            path.write_bytes(wire(fixture))
            data = b"\n".join((frame(), frame("check", wire(bound_description(fixture))),
                                frame("canonicalize", b'{"z":-0,"a":[true,null]}')))
            for args in (("--contract", V11, "--basis", str(path)), ("--basis", str(path), "--contract", V11)):
                self.successful(self.execute(data, args), [
                    {"id": "case", "result": HELLO_V11},
                    {"id": "case", "result": failure("untrusted_evidence", "applicability")},
                    {"id": "case", "result": CANONICAL},
                ])

    def test_startup_failures_are_nonzero_stderr_only_without_fixture_path_or_request_content(self):
        self.successful(self.execute(frame(), ("--contract", V11)), [{"id": "case", "result": HELLO_V11}])
        with tempfile.TemporaryDirectory(prefix="effect-v11-") as directory:
            path = Path(directory) / (SECRET + ".json")
            self.fatal(self.execute(frame(), ("--contract", V11, "--basis", str(path))))
            invalid = [SECRET.encode(), b'{"input":{},"input":{}}', b"\xff", b'{"n":1.5}',
                       b" " * (1024 * 1024 + 1)] + [wire(value) for value in (None, [], False, 0, SECRET)]
            for member in ("input", "implementation", "context", "mapping", "declaration"):
                for value in (MISSING, None, [], False, 0, SECRET):
                    fixture = basis()
                    fixture["declaration"]["claim"] = SECRET
                    if value is MISSING:
                        del fixture[member]
                    else:
                        fixture[member] = value
                    invalid.append(wire(fixture))
            for raw in invalid:
                path.write_bytes(raw)
                self.fatal(self.execute(frame(identifier=SECRET), ("--contract", V11, "--basis", str(path))))

    def test_bad_contract_and_ambiguous_opt_in_arguments_do_not_echo_supplied_values(self):
        for args in (("--contract", SECRET), ("--contract", ""), ("--contract",),
                     ("--contract", V11, "--contract", V1), ("--contract", V11, "--basis"),
                     ("--contract", V11, "--" + SECRET), ("--contract", V11, SECRET)):
            with self.subTest(args=args):
                self.fatal(self.execute(frame(), args))


if __name__ == "__main__":
    import unittest
    unittest.main()
