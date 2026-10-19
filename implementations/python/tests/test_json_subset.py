import hashlib

from support import DOCUMENT_LIMIT, ModuleCase


class JsonSubsetTests(ModuleCase):
    def setUp(self):
        self.json = self.module("json_subset")

    def canonical(self, raw):
        return self.json.canonical_bytes(self.json.parse_json(raw))

    def rejects(self, raw, status="invalid_input", reason="syntax"):
        self.assert_rejection(lambda: self.json.parse_json(raw), status, reason)

    def test_supported_values_and_integer_boundaries(self):
        raw = b'{"z":-0,"a":[null,true,false,9007199254740991,-9007199254740991]}'
        expected = b'{"a":[null,true,false,9007199254740991,-9007199254740991],"z":0}'
        self.assertEqual(self.canonical(raw), expected)
        self.assertIs(type(self.json.parse_json(b"1")), int)

    def test_utf16_key_sorting_not_codepoint_sorting(self):
        raw = br'{"\ue000":0,"\ud83d\ude00":1,"\r":2,"1":3,"\u00f6":4,"\u20ac":5}'
        expected = '{"\\r":2,"1":3,"\u00f6":4,"\u20ac":5,"\U0001f600":1,"\ue000":0}'.encode("utf-8")
        self.assertEqual(self.canonical(raw), expected)
        self.assertEqual(hashlib.sha256(self.canonical(raw)).digest(),
                         hashlib.sha256(expected).digest())

    def test_required_escapes_and_unescaped_unicode(self):
        raw = br'["\u0000\b\t\n\f\r\u001f\"\\\/\u2028\u2029"]'
        expected = '["\\u0000\\b\\t\\n\\f\\r\\u001f\\\"\\\\/\u2028\u2029"]'.encode("utf-8")
        self.assertEqual(self.canonical(raw), expected)

    def test_strings_and_arrays_are_not_normalized_or_reordered(self):
        raw = br'["e\u0301","\u00e9","\ufeff",2,1]'
        expected = '["e\u0301","\u00e9","\ufeff",2,1]'.encode("utf-8")
        self.assertEqual(self.canonical(raw), expected)
        self.assertNotEqual(self.canonical(br'"e\u0301"'), self.canonical(br'"\u00e9"'))

    def test_valid_surrogate_pairs_become_scalars(self):
        self.assertEqual(self.canonical(br'{"\ud83d\ude00":"\ud800\udc00"}'),
                         '{"\U0001f600":"\U00010000"}'.encode("utf-8"))

    def test_duplicate_decoded_keys_at_any_depth(self):
        cases = [b'{"a":1,"a":2}', br'{"a":1,"\u0061":2}',
                 b'[{"nested":{"x":1,"x":2}}]',
                 '{"\U0001f600":1,"\\ud83d\\ude00":2}'.encode("utf-8")]
        for raw in cases:
            with self.subTest(raw=raw):
                self.rejects(raw)

    def test_lone_surrogates_in_strings_and_keys(self):
        for raw in (br'"\ud800"', br'"\udfff"', br'{"\ud800":1}',
                    br'["\ud800x"]', br'"\udc00\ud800"', br'"\ud800\ud801"'):
            with self.subTest(raw=raw):
                self.rejects(raw)

    def test_invalid_utf8_and_bom(self):
        for raw in (b'\xef\xbb\xbf{}', b'"\x80"', b'"\xc0\xaf"',
                    b'"\xed\xa0\x80"', b'"\xf4\x90\x80\x80"', b'"\xe2\x82"'):
            with self.subTest(raw=raw):
                self.rejects(raw)

    def test_malformed_and_nonfinite_json(self):
        cases = (b"", b" ", b"NaN", b"Infinity", b"-Infinity", b"[NaN]",
                 b"01", b"+1", b"[1,]", b'{"a":1,}', b"1 2", b"true false",
                 b'"\v"', b'"\x01"', b"{'a':1}", b"[", b"undefined",
                 b"[1.e1]", b"--1", b"0x10", b"[1e]", b'"unterminated')
        for raw in cases:
            with self.subTest(raw=raw):
                self.rejects(raw)

    def test_unsupported_numeric_tokens_are_not_syntax_errors(self):
        cases = (b"1.0", b"-0.0", b"0e0", b"1E+2", b"1e-999999", b"1e999999",
                 b"9007199254740992", b"-9007199254740992", b"1" * 20000)
        for index, raw in enumerate(cases):
            with self.subTest(index=index):
                self.rejects(raw, "unsupported_profile", "numeric_domain")

    def test_complete_syntax_precedes_numeric_domain(self):
        for raw in (b"[1.5,]", b'{"x":1e9,"x":2}', br'[1.1,"\ud800"]',
                    b'[9007199254740992,NaN]', b"1.0 false"):
            with self.subTest(raw=raw):
                self.rejects(raw)

    def test_byte_limit_inclusive(self):
        raw = b'"' + b"a" * (DOCUMENT_LIMIT - 2) + b'"'
        self.assertEqual(len(self.json.parse_json(raw)), DOCUMENT_LIMIT - 2)
        self.rejects(raw + b" ", "evaluation_failure", "limit_exceeded")

    def test_container_depth_inclusive_and_quotes_ignored(self):
        raw = b"[" * 64 + b'"{[\\\""' + b"]" * 64
        self.assertEqual(self.canonical(raw), raw)
        self.rejects(b"[" * 65 + b"0" + b"]" * 65,
                     "evaluation_failure", "limit_exceeded")
        raw = b'{"x":' * 64 + b"0" + b"}" * 64
        self.json.parse_json(raw)
        self.rejects(b'{"x":' + raw + b"}", "evaluation_failure", "limit_exceeded")

    def test_resource_limit_precedes_numeric_support(self):
        self.rejects(b"[" * 65 + b"1.2" + b"]" * 65,
                     "evaluation_failure", "limit_exceeded")

    def test_canonicalizer_does_not_silently_accept_python_floats(self):
        self.assert_rejection(lambda: self.json.canonical_bytes({"number": 1.0}),
                              "unsupported_profile", "numeric_domain")


if __name__ == "__main__":
    import unittest
    unittest.main()
