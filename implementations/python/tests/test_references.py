import copy

from support import AMOUNT, ConsumerCase, example, unknown_amount


class ReferenceTests(ConsumerCase):
    def invalid(self, document):
        self.assert_failure(document, "invalid_input", "references")

    def test_duplicate_effect_ids(self):
        document = example()
        document["effects"].append(copy.deepcopy(document["effects"][0]))
        self.invalid(document)

    def test_duplicate_evidence_ids(self):
        document = example()
        document["evidence"].append(copy.deepcopy(document["evidence"][0]))
        self.invalid(document)

    def test_effect_and_evidence_namespaces_are_separate(self):
        document = example()
        document["effects"][0]["effect_id"] = "decl-1"
        self.assert_accepted(document)
        document = example()
        document["coverage"]["evidence_refs"] = ["effect-1"]
        self.invalid(document)
        document = example()
        document["relations"] = [{"from": "decl-1", "to": "effect-1",
                                   "kind": "urn:may-trigger", "evidence_refs": ["decl-1"]}]
        self.invalid(document)

    def test_every_evidence_reference_must_resolve(self):
        for owner in ("coverage", "effect", "relation"):
            with self.subTest(owner=owner):
                document = example()
                if owner == "coverage":
                    document["coverage"]["evidence_refs"] = ["missing"]
                elif owner == "effect":
                    document["effects"][0]["evidence_refs"] = ["missing"]
                else:
                    document["relations"] = [{"from": "effect-1", "to": "effect-1",
                                               "kind": "urn:may-trigger", "evidence_refs": ["missing"]}]
                self.invalid(document)

    def test_every_relation_endpoint_must_resolve(self):
        for endpoint in ("from", "to"):
            document = example()
            relation = {"from": "effect-1", "to": "effect-1", "kind": "urn:may-trigger",
                        "evidence_refs": []}
            relation[endpoint] = "missing"
            document["relations"] = [relation]
            self.invalid(document)

    def test_duplicate_quantity_names_are_local_to_each_effect(self):
        document = example()
        document["effects"][0]["quantities"].append(
            copy.deepcopy(document["effects"][0]["quantities"][0]))
        self.invalid(document)
        document = example()
        other = copy.deepcopy(document["effects"][0])
        other["effect_id"] = "second-effect"
        document["effects"].append(other)
        self.module("references").validate_references(document, AMOUNT)

    def test_unknown_quantity_targets_have_the_right_type_and_name(self):
        for key, value in (("effect_id", "missing"), ("effect_id", "decl-1"),
                           ("quantity_name", "urn:other-quantity")):
            document = unknown_amount(example())
            document["unknowns"][-1]["target"][key] = value
            self.invalid(document)

    def test_known_unknown_collision_and_duplicate_unknown_targets(self):
        document = unknown_amount(example())
        document["effects"][0]["quantities"] = example()["effects"][0]["quantities"]
        self.invalid(document)
        document = unknown_amount(example())
        document["unknowns"].append(copy.deepcopy(document["unknowns"][-1]))
        self.invalid(document)

    def test_target_shape_precedes_reference_integrity(self):
        document = unknown_amount(example())
        del document["unknowns"][-1]["target"]
        self.assert_failure(document, "invalid_input", "structure")

    def test_identifiers_compare_exactly_without_casefold_or_normalization(self):
        for wrong in ("DECL-1", "decl-1 ", "Decl-1"):
            document = example()
            document["coverage"]["evidence_refs"] = [wrong]
            self.invalid(document)
        document = example()
        document["effects"][0]["effect_id"] = "\u00e9"
        other = copy.deepcopy(document["effects"][0])
        other["effect_id"] = "e\u0301"
        document["effects"].append(other)
        self.module("references").validate_references(document, AMOUNT)
        document = unknown_amount(example())
        document["effects"][0]["effect_id"] = "\u00e9"
        document["unknowns"][-1]["target"]["effect_id"] = "e\u0301"
        self.invalid(document)

    def test_references_precede_unsupported_critical_or_profile(self):
        document = example()
        document["critical_extensions"] = ["urn:critical:v1"]
        document["profile"] = "urn:profile:unknown"
        document["coverage"]["evidence_refs"] = ["missing"]
        self.invalid(document)


if __name__ == "__main__":
    import unittest
    unittest.main()
