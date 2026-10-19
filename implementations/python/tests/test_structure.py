import copy

from support import AMOUNT, ModuleCase, at, example, unknown_amount


OBJECT_PATHS = (
    (), ("profile_digest",), ("invocation",), ("invocation", "digest"),
    ("implementation",), ("implementation", "digest"), ("context",),
    ("context", "digest"), ("mapping",), ("mapping", "digest"), ("coverage",),
    ("effects", 0), ("effects", 0, "resource"), ("effects", 0, "destination"),
    ("effects", 0, "data_class"), ("effects", 0, "quantities", 0),
    ("evidence", 0), ("evidence", 0, "artifact_digest"), ("unknowns", 0),
)

URI_PATHS = (
    ("profile",), ("record_id",), ("mapping", "id"),
    ("effects", 0, "category"), ("effects", 0, "operation"),
    ("effects", 0, "resource", "namespace"),
    ("effects", 0, "destination", "namespace"),
    ("effects", 0, "data_class", "namespace"),
    ("effects", 0, "quantities", 0, "name"),
    ("evidence", 0, "source"), ("evidence", 0, "artifact_ref"),
)


class StructureTests(ModuleCase):
    def setUp(self):
        self.structure = self.module("structure")

    def valid(self, document):
        self.structure.validate_structure(document)

    def invalid(self, document):
        self.assert_rejection(lambda: self.valid(document), "invalid_input", "structure")

    def test_public_example_is_structurally_valid(self):
        self.valid(example())

    def test_every_required_member_and_extra_member(self):
        for path in OBJECT_PATHS:
            for key in at(example(), path):
                with self.subTest(path=path, missing=key):
                    document = example()
                    del at(document, path)[key]
                    self.invalid(document)
            with self.subTest(path=path, extra=True):
                document = example()
                at(document, path)["extra"] = None
                self.invalid(document)

    def test_object_types_are_not_coerced(self):
        for path in OBJECT_PATHS:
            for value in (None, True, 1, "object", []):
                with self.subTest(path=path, value=value):
                    document = example()
                    if path:
                        at(document, path[:-1])[path[-1]] = value
                        self.invalid(document)
                    else:
                        self.invalid(value)

    def test_all_string_fields_have_types(self):
        def string_paths(value, path=()):
            if isinstance(value, str):
                yield path
            elif isinstance(value, dict):
                for key, child in value.items():
                    yield from string_paths(child, path + (key,))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    yield from string_paths(child, path + (index,))

        for path in string_paths(example()):
            for value in (None, False, 1, [], {}):
                with self.subTest(path=path, value=value):
                    document = example()
                    at(document, path[:-1])[path[-1]] = value
                    self.invalid(document)

    def test_nonempty_string_constraints(self):
        paths = URI_PATHS + (
            ("invocation", "reference"), ("implementation", "reference"),
            ("context", "reference"), ("mapping", "revision"),
            ("effects", 0, "effect_id"), ("effects", 0, "resource", "value"),
            ("effects", 0, "destination", "value"),
            ("effects", 0, "data_class", "value"),
            ("effects", 0, "quantities", 0, "unit"),
            ("effects", 0, "evidence_refs", 0), ("coverage", "assumptions", 0),
            ("coverage", "evidence_refs", 0), ("evidence", 0, "evidence_id"),
            ("evidence", 0, "scope"), ("unknowns", 0, "scope"),
        )
        for path in paths:
            with self.subTest(path=path):
                document = example()
                at(document, path[:-1])[path[-1]] = ""
                self.invalid(document)

    def test_uri_validation_at_every_uri_field(self):
        invalid_uris = ("relative/path", ":missing", "1bad:x", "https:",
                        "https://example.org/a b", "urn:\u00e9", "urn:x%",
                        "urn:x%0", "urn:x%GG", "urn:x\\y", "urn:x\n",
                        "urn:x\x7f", "urn:x<y>", "urn:x|y", "urn:x{y}")
        for path in URI_PATHS:
            for value in invalid_uris:
                with self.subTest(path=path, value=value):
                    document = example()
                    at(document, path[:-1])[path[-1]] = value
                    self.invalid(document)
        for value in ("urn:x", "mailto:a@example.org", "x+v1:a%20b?c#d"):
            document = example()
            document["record_id"] = value
            self.valid(document)
        document = example()
        document["invocation"]["reference"] = "opaque local key, not a URI"
        self.valid(document)

    def test_digest_format_and_algorithm(self):
        for path in (("profile_digest",), ("invocation", "digest"),
                     ("implementation", "digest"), ("context", "digest"),
                     ("mapping", "digest"), ("evidence", 0, "artifact_digest")):
            for key, value in (("algorithm", "sha256"), ("algorithm", 256),
                               ("value", "A" * 64), ("value", "a" * 63),
                               ("value", "a" * 65), ("value", "g" * 64),
                               ("value", "a" * 64 + "\n")):
                with self.subTest(path=path, key=key, value=value):
                    document = example()
                    at(document, path)[key] = value
                    self.invalid(document)

    def test_quantity_integer_string_and_scale_grammar(self):
        for value in ("0", "1", "-1", "9" * 78, "-" + "9" * 78):
            document = example()
            document["effects"][0]["quantities"][0]["value"] = value
            self.valid(document)
        for value in ("", "-0", "+1", "00", "01", "-01", "1.0", "1e2",
                      " 1", "1 ", "0\n", "\u0661", "9" * 79, "-" + "9" * 79):
            with self.subTest(value=value):
                document = example()
                document["effects"][0]["quantities"][0]["value"] = value
                self.invalid(document)
        for scale in map(str, range(19)):
            document = example()
            document["effects"][0]["quantities"][0]["scale"] = scale
            self.valid(document)
        for scale in ("19", "-1", "01", "1.0", "2\n", "", 2):
            document = example()
            document["effects"][0]["quantities"][0]["scale"] = scale
            self.invalid(document)

    def test_slot_variants_are_exclusive(self):
        for name in ("resource", "destination", "data_class"):
            for slot in ({"state": "none"}, {"state": "unknown", "reason": "unresolved"}):
                document = example()
                document["effects"][0][name] = slot
                self.valid(document)
            for slot in ({"state": "known"}, {"state": "none", "value": "x"},
                         {"state": "unknown"}, {"state": "unknown", "reason": ""},
                         {"state": "other"}, {"state": "unknown", "reason": "x", "value": "y"}):
                with self.subTest(name=name, slot=slot):
                    document = example()
                    document["effects"][0][name] = slot
                    self.invalid(document)

    def test_enums_and_observed_occurrence_requirement(self):
        for path in (("coverage", "scope"), ("coverage", "completeness"),
                     ("effects", 0, "modality"), ("evidence", 0, "kind"),
                     ("unknowns", 0, "code")):
            document = example()
            at(document, path[:-1])[path[-1]] = "not-in-the-enum"
            self.invalid(document)
        document = example()
        document["effects"][0]["modality"] = "observed"
        self.invalid(document)
        document["effects"][0]["occurrence_ref"] = "occurrence-1"
        self.valid(document)
        document["effects"][0]["occurrence_ref"] = ""
        self.invalid(document)

    def test_array_types_bounds_and_unique_string_arrays(self):
        paths = ((("effects",), 256), (("evidence",), 256), (("unknowns",), 256),
                 (("effects", 0, "quantities"), 64), (("coverage", "assumptions"), 64),
                 (("coverage", "evidence_refs"), 256),
                 (("effects", 0, "evidence_refs"), 256))
        for path, maximum in paths:
            for value in (None, "array", {}, False):
                document = example()
                at(document, path[:-1])[path[-1]] = value
                self.invalid(document)
            document = example()
            item = at(document, path)[0]
            at(document, path[:-1])[path[-1]] = [copy.deepcopy(item) for _ in range(maximum + 1)]
            self.invalid(document)
        for path in (("coverage", "assumptions"), ("coverage", "evidence_refs"),
                     ("effects", 0, "evidence_refs")):
            document = example()
            at(document, path).append(at(document, path)[0])
            self.invalid(document)
        document = example()
        document["coverage"]["assumptions"] = ["\u00e9", "e\u0301"]
        self.valid(document)

    def test_unknown_target_conditional_shape(self):
        document = unknown_amount(example())
        self.valid(document)
        del document["unknowns"][-1]["target"]
        self.invalid(document)
        for key, value in (("effect_id", ""), ("quantity_name", "not-a-uri"),
                           ("extra", "not-allowed")):
            document = unknown_amount(example())
            document["unknowns"][-1]["target"][key] = value
            self.invalid(document)
        for key in ("effect_id", "quantity_name"):
            document = unknown_amount(example())
            del document["unknowns"][-1]["target"][key]
            self.invalid(document)
        document = example()
        document["unknowns"][0]["target"] = {"effect_id": "effect-1", "quantity_name": AMOUNT}
        self.invalid(document)

    def test_relation_shape_limits_and_reference_arrays(self):
        relation = {"from": "effect-1", "to": "effect-1", "kind": "urn:relation:triggers",
                    "evidence_refs": ["decl-1"]}
        document = example()
        document["relations"] = [relation]
        self.valid(document)
        for key in relation:
            candidate = copy.deepcopy(document)
            del candidate["relations"][0][key]
            self.invalid(candidate)
        for key, value in (("extra", 1), ("from", ""), ("to", False),
                           ("kind", "relative"), ("evidence_refs", ["decl-1", "decl-1"]),
                           ("evidence_refs", [str(i) for i in range(257)])):
            candidate = copy.deepcopy(document)
            candidate["relations"][0][key] = value
            self.invalid(candidate)
        document["relations"] = [relation] * 1024
        self.valid(document)
        document["relations"].append(relation)
        self.invalid(document)

    def test_extension_shape_and_limits_without_payload_execution(self):
        document = example()
        document["extensions"] = {"urn:metadata:v1": [None, True, {"arbitrary": "value"}]}
        self.valid(document)
        for value in ([], None, True, {"relative": {}}):
            document["extensions"] = value
            self.invalid(document)
        document["extensions"] = {"urn:x:" + str(i): None for i in range(64)}
        self.valid(document)
        document["extensions"]["urn:x:extra"] = None
        self.invalid(document)
        document = example()
        for value in (None, {}, ["relative"], ["urn:x", "urn:x"],
                      ["urn:x:" + str(i) for i in range(65)]):
            document["critical_extensions"] = value
            self.invalid(document)


if __name__ == "__main__":
    import unittest
    unittest.main()
