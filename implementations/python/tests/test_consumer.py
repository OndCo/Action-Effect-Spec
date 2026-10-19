import base64
import copy
from dataclasses import FrozenInstanceError
import hashlib
import json
import tempfile
from pathlib import Path

from support import (AMOUNT, ConsumerCase, DOCUMENT_LIMIT, PROFILE_HASH, PROFILE_URI,
                     PYTHON_ROOT, basis, bound_description, example, failure,
                     fixture_digest, public_bytes, unknown_amount, wire)


class ConsumerTests(ConsumerCase):
    def test_public_example_exact_result(self):
        self.assert_accepted(example())

    def test_exact_capabilities_do_not_grant_authority(self):
        self.assertEqual(self.consumer.hello(), {
            "status": "capabilities", "reason": "offline_snapshot",
            "authority": "not_evaluated", "spec_version": "0.1.0-draft.1",
            "profile": PROFILE_URI, "numeric_domain": "safe_integer_tokens_only",
            "acceptance_cache": False,
        })

    def test_canonicalize_is_not_description_acceptance(self):
        canonical = b'{"a":[true,null],"z":0}'
        self.assertEqual(self.consumer.canonicalize(b'{"z":-0, "a":[true,null]}'), {
            "status": "canonicalized", "reason": "supported_subset",
            "authority": "not_evaluated",
            "canonical_b64": base64.b64encode(canonical).decode("ascii"),
            "sha256": hashlib.sha256(canonical).hexdigest(),
        })
        self.assertEqual(self.consumer.check(b'"not an object"'), failure("invalid_input", "structure"))

    def test_version_gate_before_other_shape_constraints(self):
        for value in ({}, {"spec_version": 1}, {"spec_version": None}, []):
            self.assert_failure(value, "invalid_input", "structure")
        self.assert_failure({"spec_version": "future"}, "unsupported_profile", "spec_version")
        self.assert_failure({"spec_version": ""}, "unsupported_profile", "spec_version")

    def test_raw_syntax_and_numeric_precedence(self):
        self.assertEqual(self.consumer.check(b'{"spec_version":"future","n":1.5}'),
                         failure("unsupported_profile", "numeric_domain"))
        self.assertEqual(self.consumer.check(b'{"spec_version":"future","n":1.5,}'),
                         failure("invalid_input", "syntax"))
        self.assertEqual(self.consumer.check(b" " * (DOCUMENT_LIMIT + 1)),
                         failure("evaluation_failure", "limit_exceeded"))

    def test_critical_profile_and_scope_precedence(self):
        document = example()
        document["critical_extensions"] = ["urn:critical:v1"]
        document["profile"] = "urn:other-profile"
        document["profile_digest"]["value"] = "0" * 64
        self.assert_failure(document, "unsupported_profile", "critical_extension")
        document["critical_extensions"] = []
        self.assert_failure(document, "unsupported_profile", "profile")
        document["profile"] = PROFILE_URI
        document["coverage"]["completeness"] = "bounded_claim"
        self.assert_failure(document, "untrusted_evidence", "profile_binding")
        document["profile_digest"]["value"] = PROFILE_HASH
        document["invocation"]["digest"]["value"] = "0" * 64
        self.assert_failure(document, "unsupported_profile", "evidence_scope")

    def test_structure_precedes_unsupported_extension(self):
        document = example()
        document["critical_extensions"] = ["urn:critical:v1"]
        document["coverage"]["extra"] = True
        self.assert_failure(document, "invalid_input", "structure")

    def test_scope_observation_and_nondeclaration_evidence_are_unsupported(self):
        for field, value in (("scope", "transitive"), ("completeness", "bounded_claim")):
            document = example()
            document["coverage"][field] = value
            self.assert_failure(document, "unsupported_profile", "evidence_scope")
        for kind in ("observation", "analysis", "review"):
            document = example()
            document["evidence"][0]["kind"] = kind
            self.assert_failure(document, "unsupported_profile", "evidence_scope")
        document = example()
        document["effects"][0]["modality"] = "observed"
        self.assert_failure(document, "invalid_input", "structure")
        document["effects"][0]["occurrence_ref"] = "opaque-occurrence"
        self.assert_failure(document, "unsupported_profile", "evidence_scope")
        document["effects"] = []
        document["coverage"]["completeness"] = "bounded_claim"
        self.assert_failure(document, "unsupported_profile", "evidence_scope")

    def test_all_binding_references_are_finite_exact_lookup_keys(self):
        for field in ("invocation", "implementation", "context"):
            for value in ("https://example.org/other#input", "./synthetic-basis.json#input",
                          "file:///not-a-file", "synthetic-basis.json#INPUT"):
                document = example()
                document[field]["reference"] = value
                self.assert_failure(document, "untrusted_evidence", "artifact_binding")
        for field, value in (("id", "https://EXAMPLE.org/mappings/refund"), ("revision", "01")):
            document = example()
            document["mapping"][field] = value
            self.assert_failure(document, "untrusted_evidence", "artifact_binding")
        document = example()
        document["evidence"][0]["artifact_ref"] += "%20"
        self.assert_failure(document, "untrusted_evidence", "artifact_binding")

    def test_selected_member_digests_not_enclosing_file_or_references(self):
        for field in ("invocation", "implementation", "context", "mapping"):
            for wrong in (fixture_digest(basis()), "0" * 64):
                document = example()
                document[field]["digest"]["value"] = wrong
                self.assert_failure(document, "untrusted_evidence", "artifact_binding")
        document = example()
        document["evidence"][0]["artifact_digest"]["value"] = fixture_digest(basis())
        self.assert_failure(document, "untrusted_evidence", "artifact_binding")

    def test_complete_members_including_uninterpreted_metadata_are_bound(self):
        for member in ("input", "implementation", "context", "mapping", "declaration"):
            fixture = basis()
            fixture[member]["opaque_metadata"] = {"claim": "not executed or proven", "flag": True}
            consumer = self.new_consumer(fixture)
            self.assert_failure(example(), "untrusted_evidence", "artifact_binding", consumer)
            self.assert_accepted(bound_description(fixture), consumer)
        fixture = basis()
        fixture["unselected_wrapper"] = {"note": "not a selected member"}
        self.assert_accepted(example(), self.new_consumer(fixture))

    def test_every_evidence_item_must_match_the_declaration_source(self):
        document = example()
        document["evidence"][0]["source"] = "https://example.org/other-issuer"
        self.assert_failure(document, "untrusted_evidence", "artifact_binding")
        document = example()
        other = copy.deepcopy(document["evidence"][0])
        other["evidence_id"] = "unused-declaration"
        other["source"] = "https://example.org/untrusted"
        document["evidence"].append(other)
        self.assert_failure(document, "untrusted_evidence", "artifact_binding")
        other["source"] = document["evidence"][0]["source"]
        other["scope"] = "arbitrary text is not proof"
        self.assert_accepted(document)

    def test_configured_order_amount_context_and_issuer_can_change(self):
        fixture = basis()
        fixture["input"]["order"] = "\u00e9-order"
        fixture["input"]["amount_minor"] = "123"
        fixture["context"]["account"] = "another-synthetic-account"
        fixture["declaration"]["issuer"] = "urn:synthetic:issuer-two"
        document = bound_description(fixture)
        document["effects"][0]["resource"]["value"] = "\u00e9-order"
        document["effects"][0]["quantities"][0]["value"] = "123"
        self.assert_accepted(document, self.new_consumer(fixture))

    def test_applicability_checks_all_required_fixture_values(self):
        changes = (("input", "operation", "charge"), ("input", "order", ""),
                   ("input", "order", None), ("input", "currency", "EUR"),
                   ("implementation", "name", "other-tool"),
                   ("implementation", "version", "1.0.1"),
                   ("implementation", "visibility", "measured"),
                   ("context", "account", ""), ("context", "account", False),
                   ("context", "destination", "another-payment"),
                   ("context", "environment", "production"),
                   ("mapping", "id", "urn:other-mapping"), ("mapping", "revision", "2"))
        for member, key, value in changes:
            with self.subTest(member=member, key=key, value=value):
                fixture = basis()
                fixture[member][key] = value
                self.assert_failure(bound_description(fixture), "untrusted_evidence", "applicability",
                                    self.new_consumer(fixture))
        for member, key in (("input", "order"), ("context", "account"),
                            ("implementation", "version"), ("mapping", "revision")):
            fixture = basis()
            del fixture[member][key]
            self.assert_failure(bound_description(fixture), "untrusted_evidence", "applicability",
                                self.new_consumer(fixture))

    def test_amount_applicability_range_and_string_type(self):
        for amount in ("0", "999999999999"):
            fixture = basis()
            fixture["input"]["amount_minor"] = amount
            document = bound_description(fixture)
            document["effects"][0]["quantities"][0]["value"] = amount
            self.assert_accepted(document, self.new_consumer(fixture))
        for amount in (None, 0, True, "-0", "-1", "00", "1e2", "1.0", " 1", "1\n",
                       "1000000000000", "9" * 78, "\u0661"):
            with self.subTest(amount=amount):
                fixture = basis()
                fixture["input"]["amount_minor"] = amount
                self.assert_failure(bound_description(fixture), "untrusted_evidence", "applicability",
                                    self.new_consumer(fixture))

    def test_artifact_binding_precedes_applicability_then_projection(self):
        fixture = basis()
        fixture["input"]["currency"] = "EUR"
        consumer = self.new_consumer(fixture)
        document = example()
        document["effects"][0]["category"] = "urn:wrong-category"
        self.assert_failure(document, "untrusted_evidence", "artifact_binding", consumer)
        document = bound_description(fixture, document)
        self.assert_failure(document, "untrusted_evidence", "applicability", consumer)

    def test_projection_tuple_is_coupled_and_exact(self):
        for field, value in (("category", "urn:other-category"), ("operation", "urn:other-operation"),
                             ("occurrence_ref", "not-an-observation")):
            document = example()
            document["effects"][0][field] = value
            self.assert_failure(document, "untrusted_evidence", "effect_projection")
        for slot in ("resource", "destination", "data_class"):
            for key, value in (("namespace", "urn:other-namespace"), ("value", "wrong-value")):
                document = example()
                document["effects"][0][slot][key] = value
                self.assert_failure(document, "untrusted_evidence", "effect_projection")
            document = example()
            document["effects"][0][slot] = {"state": "unknown", "reason": "not known"}
            self.assert_failure(document, "untrusted_evidence", "effect_projection")

    def test_exactly_one_effect_no_relations_and_explicit_support(self):
        document = example()
        document["effects"] = []
        self.assert_failure(document, "untrusted_evidence", "effect_projection")
        document = example()
        other = copy.deepcopy(document["effects"][0])
        other["effect_id"] = "another-effect"
        document["effects"].append(other)
        self.assert_failure(document, "untrusted_evidence", "effect_projection")
        document = example()
        document["relations"] = [{"from": "effect-1", "to": "effect-1", "kind": "urn:may-trigger",
                                   "evidence_refs": ["decl-1"]}]
        self.assert_failure(document, "untrusted_evidence", "effect_projection")
        for target in ("coverage", "effect"):
            document = example()
            owner = document["coverage"] if target == "coverage" else document["effects"][0]
            owner["evidence_refs"] = []
            self.assert_failure(document, "untrusted_evidence", "effect_projection")

    def test_unknown_descendants_are_required_and_other_unknowns_are_retained(self):
        document = example()
        document["unknowns"] = []
        self.assert_failure(document, "untrusted_evidence", "effect_projection")
        document = example()
        for code in ("unmapped", "missing_context", "unresolved_identity", "conflicting_evidence",
                     "unsupported_implementation"):
            document["unknowns"].append({"code": code, "scope": "still unresolved"})
        self.assert_accepted(document)

    def test_wrong_represented_amount_unit_or_scale(self):
        for key, value in (("value", "7301"), ("value", "-1"), ("unit", "EUR"), ("scale", "3")):
            document = example()
            document["effects"][0]["quantities"][0][key] = value
            self.assert_failure(document, "untrusted_evidence", "effect_projection")
        document = example()
        other = copy.deepcopy(document["effects"][0]["quantities"][0])
        other["name"] = "urn:extra-quantity"
        document["effects"][0]["quantities"].append(other)
        self.assert_failure(document, "untrusted_evidence", "effect_projection")

    def test_missing_amount_representation_is_final_domain_structure_error(self):
        document = example()
        document["effects"][0]["quantities"] = []
        self.assert_failure(document, "invalid_input", "structure")
        document["invocation"]["digest"]["value"] = "0" * 64
        self.assert_failure(document, "untrusted_evidence", "artifact_binding")
        document = example()
        document["effects"][0]["quantities"][0]["name"] = "urn:other-quantity"
        self.assert_failure(document, "invalid_input", "structure")

    def test_absent_fixture_amount_requires_exact_unknown_representation(self):
        fixture = basis()
        del fixture["input"]["amount_minor"]
        consumer = self.new_consumer(fixture)
        document = unknown_amount(bound_description(fixture))
        document["effects"][0]["effect_id"] = "locally-chosen-id"
        document["unknowns"][-1]["target"]["effect_id"] = "locally-chosen-id"
        self.assert_accepted(document, consumer)
        document["unknowns"].pop()
        self.assert_failure(document, "invalid_input", "structure", consumer)
        document = bound_description(fixture)
        self.assert_failure(document, "untrusted_evidence", "effect_projection", consumer)

    def test_unknown_does_not_replace_available_known_amount(self):
        self.assert_failure(unknown_amount(example()), "untrusted_evidence", "effect_projection")

    def test_noncritical_metadata_is_hashed_without_widening_semantics(self):
        document = example()
        document["extensions"] = {"urn:metadata:v1": {
            "authority": "granted", "effects": [], "coverage": "complete", "note": "\u00e9",
        }}
        self.assert_accepted(document)
        self.assertNotEqual(fixture_digest(document), fixture_digest(example()))
        raw = wire(document).replace(b'"note":"\xc3\xa9"', b'"note":1.5')
        self.assertEqual(self.consumer.check(raw), failure("unsupported_profile", "numeric_domain"))

    def test_results_are_fresh_not_an_acceptance_cache(self):
        previous = self.consumer.check(public_bytes("partial-refund.json"))
        previous["authority"] = "granted"
        self.assert_accepted(example())
        self.assertEqual(self.consumer.hello()["acceptance_cache"], False)


class ConfigurationTests(ConsumerCase):
    def test_manifest_is_pinned_over_complete_canonical_content(self):
        manifest = json.loads(public_bytes("refund-profile.json"))
        self.assertEqual(fixture_digest(manifest), PROFILE_HASH)
        snapshot = self.configuration.Snapshot.from_bytes(
            public_bytes("synthetic-basis.json"), wire(manifest))
        with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
            snapshot.profile_digest = "0" * 64
        manifest["uninterpreted_new_field"] = "changes full hash"
        with self.assertRaises(self.configuration.ConfigurationError):
            self.configuration.Snapshot.from_bytes(public_bytes("synthetic-basis.json"), wire(manifest))

    def test_invalid_startup_syntax_or_selected_member_shape(self):
        cases = [b"not-json", b'{"input":{},"input":{}}', b"[]", b'{"number":1.5}']
        for member in ("input", "implementation", "context", "mapping", "declaration"):
            fixture = basis()
            del fixture[member]
            cases.append(wire(fixture))
            fixture = basis()
            fixture[member] = []
            cases.append(wire(fixture))
        for raw in cases:
            with self.subTest(raw=raw[:80]):
                with self.assertRaises(self.configuration.ConfigurationError):
                    self.configuration.Snapshot.from_bytes(raw, public_bytes("refund-profile.json"))

    def test_load_snapshot_keeps_configured_bytes_after_file_changes(self):
        with tempfile.TemporaryDirectory(dir=str(PYTHON_ROOT / "tests")) as directory:
            path = Path(directory) / "basis.json"
            path.write_bytes(public_bytes("synthetic-basis.json"))
            snapshot = self.configuration.load_snapshot(path)
            path.write_bytes(b"now invalid")
            consumer = self.consumer_module.Consumer(snapshot)
            self.assert_accepted(example(), consumer)

    def test_unreadable_config_is_a_startup_error(self):
        with tempfile.TemporaryDirectory(dir=str(PYTHON_ROOT / "tests")) as directory:
            with self.assertRaises(self.configuration.ConfigurationError):
                self.configuration.load_snapshot(Path(directory) / "missing.json")


if __name__ == "__main__":
    import unittest
    unittest.main()
