"""Post-review URI regressions derived from RFC 3986 Appendix A, not shared cases."""

from support import ConsumerCase, ModuleCase, at, example, unknown_amount
from test_structure import URI_PATHS


class GenericUriTests(ModuleCase):
    def setUp(self):
        self.is_uri = self.module("structure").is_uri

    def test_opaque_schemes_and_percent_encoding_remain_valid(self):
        values = (
            "urn:example:opaque:identifier", "URN:example:Case-Sensitive",
            "mailto:person+tag@example.org?subject=RFC%203986",
            "tel:+1-202-555-0100", "data:text/plain;charset=UTF-8,hello%20world",
            "custom+v1:a:b@c/d;e?next=a/b?c#fragment/with?query",
            "urn:example:%5B%5D%23%3F%2F%3A%40%25", "urn:example:%ff",
        )
        for value in values:
            with self.subTest(value=value):
                self.assertTrue(self.is_uri(value))

    def test_generic_hierarchical_paths_and_empty_components(self):
        values = (
            "custom:/", "custom:/absolute//path", "custom:rootless/path",
            "custom://", "custom:///absolute/path", "custom:////double/path",
            "custom://@host/path", "custom://user:password@host:123/path",
            "custom://host:/", "custom://host:00080/", "custom://host:999999999999999999999/",
            "custom://host/path?", "custom://host/path#", "custom://host/path?#",
            "custom://example%2Eorg/path", "custom://not-a-dns-name!$&'()*+,;=/",
            "custom://256.256.256.256/path",
        )
        for value in values:
            with self.subTest(value=value):
                self.assertTrue(self.is_uri(value))
        self.assertFalse(self.is_uri("custom:"))

    def test_ipv6_compression_and_embedded_ipv4(self):
        addresses = (
            "1:2:3:4:5:6:7:8", "::1:2:3:4:5:6:7", "1::2:3:4:5:6:7",
            "1:2::3:4:5:6:7", "1:2:3::4:5:6:7", "1:2:3:4::5:6:7",
            "1:2:3:4:5::6:7", "1:2:3:4:5:6::7", "1:2:3:4:5:6:7::", "::",
            "2001:db8::1", "2001:DB8::ABCD", "::ffff:192.0.2.128",
            "1:2:3:4:5:6:192.0.2.1", "::192.0.2.1",
        )
        for address in addresses:
            with self.subTest(address=address):
                self.assertTrue(self.is_uri("custom://[" + address + "]:443/path?x#y"))

    def test_ipvfuture_is_supported_without_resolution(self):
        addresses = (
            "v1.future", "V1.future", "vF.future:address", "v0123456789abcdef.a",
            "vA.-._~!$&'()*+,;=:address", "v1.a.b.c", "v1." + "a" * 80,
        )
        for address in addresses:
            with self.subTest(address=address):
                self.assertTrue(self.is_uri("custom://user@[" + address + "]:7/path"))

    def test_malformed_ip_literals_are_rejected(self):
        values = (
            "https://[", "https://[::1", "https://[::1]]", "https://[[::1]]",
            "https://[]", "https://[example.org]", "https://[127.0.0.1]",
            "https://[1:2:3:4:5:6:7]", "https://[1:2:3:4:5:6:7:8:9]",
            "https://[1:2:3:4:5:6:7:8::]", "https://[1::2::3]", "https://[:::1]",
            "https://[12345::]", "https://[gggg::]", "https://[:1:2:3:4:5:6:7]",
            "https://[::ffff:192.0.2.256]", "https://[::ffff:192.0.2.01]",
            "https://[::ffff:192.0.2]", "https://[192.0.2.1::]",
            "https://[fe80::1%eth0]", "https://[fe80::1%25eth0]",
            "https://[::1]suffix", "https://[::1]:80:90", "https://2001:db8::1/",
        )
        for value in values:
            with self.subTest(value=value):
                self.assertFalse(self.is_uri(value))

    def test_malformed_ipvfuture_is_rejected(self):
        for address in ("v.future", "vG.future", "v1", "v1.", "v1.%61", "v1.a@b",
                        "v1.a/b", "v1.a?b", "v1.a#b", "v1.a[b]", "v1.\u00e9"):
            with self.subTest(address=address):
                self.assertFalse(self.is_uri("custom://[" + address + "]/"))

    def test_authority_delimiters_and_nonnumeric_ports(self):
        values = (
            "https://first@second@example.org/", "https://user[name]@example.org/",
            "https://example[.]org/", "https://example.org]/", "https://host:80:90/",
            "https://host:http/", "https://host:-1/", "https://host:+1/",
            "https://host:%38%30/", "https://host:8a/", "https://host:\u0668/",
            "https://[::1]:https/", "https://[v1.future]:service/",
        )
        for value in values:
            with self.subTest(value=value):
                self.assertFalse(self.is_uri(value))

    def test_reserved_delimiters_are_component_specific(self):
        values = (
            "https://example.org/#first#second", "urn:example:x##",
            "https://example.org/path[part]", "urn:example:part]",
            "https://example.org/?q=[part]", "https://example.org/#fragment[part]",
        )
        for value in values:
            with self.subTest(value=value):
                self.assertFalse(self.is_uri(value))
        for value in ("https://example.org/a:b@c?q=a:b@c/?x#f:a@b/c?d",
                      "https://example.org/%5Bpart%5D?q=%23#first%23second"):
            with self.subTest(value=value):
                self.assertTrue(self.is_uri(value))

    def test_percent_escapes_are_checked_in_each_component(self):
        templates = ("custom://{}@host/", "custom://{}/", "custom:/{}/",
                     "custom:root/{}", "custom:path?{}", "custom:path#{}")
        for template in templates:
            for component in ("bad%", "bad%1", "bad%GH", "bad%0g"):
                with self.subTest(template=template, component=component):
                    self.assertFalse(self.is_uri(template.format(component)))
            self.assertTrue(self.is_uri(template.format("ok%2f%2F%23%5B%5D")))


class UriConsumerTests(ConsumerCase):
    def test_review_record_id_counterexamples_are_structure_errors(self):
        for value in ("https://[", "https://example.org/#first#second"):
            with self.subTest(value=value):
                document = example()
                document["record_id"] = value
                self.assert_failure(document, "invalid_input", "structure")

    def test_new_syntax_rules_apply_to_all_schema_uri_fields(self):
        for path in URI_PATHS:
            with self.subTest(path=path):
                document = example()
                at(document, path[:-1])[path[-1]] = "https://["
                self.assert_failure(document, "invalid_input", "structure")
        document = unknown_amount(example())
        document["unknowns"][-1]["target"]["quantity_name"] = "https://["
        self.assert_failure(document, "invalid_input", "structure")
        document = example()
        document["relations"] = [{"from": "effect-1", "to": "effect-1", "kind": "https://[",
                                   "evidence_refs": ["decl-1"]}]
        self.assert_failure(document, "invalid_input", "structure")
        document = example()
        document["critical_extensions"] = ["https://["]
        self.assert_failure(document, "invalid_input", "structure")
        document = example()
        document["extensions"] = {"https://[": None}
        self.assert_failure(document, "invalid_input", "structure")

    def test_valid_generic_record_ids_keep_their_original_spelling(self):
        for value in ("URN:example:opaque%2fId", "mailto:person@example.org",
                      "custom://user@[2001:DB8::1]:00080/path?x#y",
                      "custom://[vF.future:address]/path", "custom://host:999999/"):
            with self.subTest(value=value):
                document = example()
                document["record_id"] = value
                self.assert_accepted(document)
                self.assertEqual(document["record_id"], value)

    def test_uri_structure_errors_keep_existing_stage_precedence(self):
        document = unknown_amount(example())
        document["record_id"] = "https://example.org/#first#second"
        document["critical_extensions"] = ["urn:critical:v1"]
        document["coverage"]["evidence_refs"] = ["missing"]
        self.assert_failure(document, "invalid_input", "structure")
        document["spec_version"] = "future"
        self.assert_failure(document, "unsupported_profile", "spec_version")


if __name__ == "__main__":
    import unittest
    unittest.main()
