import io
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
from unittest.mock import patch

from support import (CLI, DOCUMENT_LIMIT, FRAME_LIMIT, PYTHON_ROOT, ConsumerCase,
                     basis, bound_description, example, failure, public_bytes,
                     request, wire)


class AdapterTests(ConsumerCase):
    def setUp(self):
        super().setUp()
        self.adapter = self.module("adapter")

    def serve(self, data, consumer=None):
        output = io.BytesIO()
        self.adapter.serve(io.BytesIO(data), output, self.consumer if consumer is None else consumer)
        return [json.loads(line) for line in output.getvalue().splitlines()]

    def test_hello_and_final_unterminated_frame(self):
        self.assertEqual(self.serve(request(op="hello") + b"\n" + request(op="hello", identifier="last")), [
            {"id": "case-1", "result": self.consumer.hello()},
            {"id": "last", "result": self.consumer.hello()},
        ])
        self.assertEqual(self.serve(b""), [])

    def test_exact_adapter_fields_and_types(self):
        valid = {"id": "id", "op": "hello"}
        invalid = [None, [], {}, {"id": "id"}, {"op": "hello"},
                   dict(valid, extra=True), dict(valid, document_b64=""),
                   dict(valid, op="unknown"), dict(valid, op=1),
                   {"id": "id", "op": "check"},
                   {"id": "id", "op": "check", "document_b64": False},
                   {"id": "id", "op": "check", "document_b64": "e30=", "basis": "x"}]
        for value in invalid:
            with self.subTest(value=value):
                self.assertEqual(self.serve(wire(value)), [{"id": None, "result": failure("invalid_input", "transport")}])

    def test_ids_count_unicode_scalars_not_utf16_units(self):
        for value in ("", "x" * 129, "\U0001f600" * 129, None, True, 1):
            self.assertEqual(self.serve(wire({"id": value, "op": "hello"})), [
                {"id": None, "result": failure("invalid_input", "transport")},
            ])
        for value in ("x", "x" * 128, "\U0001f600" * 128, "\u0000"):
            self.assertEqual(self.serve(request(op="hello", identifier=value)), [
                {"id": value, "result": self.consumer.hello()},
            ])

    def test_duplicate_keys_invalid_utf8_bom_and_surrogates_are_transport(self):
        cases = (br'{"id":"x","\u0069d":"y","op":"hello"}',
                 br'{"id":"\ud800","op":"hello"}', b"\xff",
                 b'\xef\xbb\xbf{"id":"x","op":"hello"}',
                 b'{"id":"x","op":"hello","n":NaN}', b"\n")
        for raw in cases:
            with self.subTest(raw=raw):
                self.assertEqual(self.serve(raw.rstrip(b"\n") + b"\n"), [
                    {"id": None, "result": failure("invalid_input", "transport")},
                ])

    def test_base64_requires_standard_alphabet_canonical_padding_and_bits(self):
        for value in ("e30", "e31=", "e30==", "e30= ", "e3\n0=", "_w==", "====", "AA=A", "\u00e9"):
            with self.subTest(value=value):
                frame = wire({"id": "id", "op": "check", "document_b64": value})
                self.assertEqual(self.serve(frame), [{"id": None, "result": failure("invalid_input", "transport")}])
        self.assertEqual(self.serve(wire({"id": "id", "op": "check", "document_b64": ""})), [
            {"id": "id", "result": failure("invalid_input", "syntax")},
        ])

    def test_invalid_document_echoes_id_without_document_contents(self):
        result = self.serve(request(b"private-document-not-json", identifier="valid-id"))
        self.assertEqual(result, [{"id": "valid-id", "result": failure("invalid_input", "syntax")}])

    def test_canonicalize_dispatch_and_document_limit(self):
        self.assertEqual(self.serve(request(b"-0", op="canonicalize")), [
            {"id": "case-1", "result": self.consumer.canonicalize(b"-0")},
        ])
        for raw in (b" " * (DOCUMENT_LIMIT + 1), b"[" * 65 + b"0" + b"]" * 65):
            self.assertEqual(self.serve(request(raw)), [
                {"id": "case-1", "result": failure("evaluation_failure", "limit_exceeded")},
            ])

    def test_frame_limit_inclusive_then_drain_and_recover(self):
        hello = request(op="hello")
        exact = b" " * (FRAME_LIMIT - len(hello)) + hello
        self.assertEqual(self.serve(exact + b"\n"), [{"id": "case-1", "result": self.consumer.hello()}])
        data = exact + b" " * (FRAME_LIMIT + 8) + b"\n" + hello + b"\n"
        self.assertEqual(self.serve(data), [
            {"id": None, "result": failure("evaluation_failure", "limit_exceeded")},
            {"id": "case-1", "result": self.consumer.hello()},
        ])
        self.assertEqual(self.serve(exact + b" "), [
            {"id": None, "result": failure("evaluation_failure", "limit_exceeded")},
        ])

    def test_blank_malformed_crlf_and_repeated_frame_recovery(self):
        data = b"\n\xff\n{}\n" + request(op="hello") + b"\r\n" + request(b"1.5") + b"\n" + request()
        results = self.serve(data)
        self.assertEqual(len(results), 6)
        for result in results[:3]:
            self.assertEqual(result, {"id": None, "result": failure("invalid_input", "transport")})
        self.assertEqual(results[3], {"id": "case-1", "result": self.consumer.hello()})
        self.assertEqual(results[4], {"id": "case-1", "result": failure("unsupported_profile", "numeric_domain")})
        self.assertEqual(results[5]["result"]["status"], "accepted_partial")

    def test_unexpected_code_failure_is_sanitized_and_next_frame_served(self):
        with patch.object(self.consumer, "check", side_effect=RuntimeError("secret stack detail")):
            results = self.serve(request() + b"\n" + request(op="hello"))
        self.assertEqual(results, [
            {"id": "case-1", "result": failure("evaluation_failure", "internal_error")},
            {"id": "case-1", "result": self.consumer.hello()},
        ])

    def test_frame_reader_never_requests_unbounded_input(self):
        class BoundedInput(io.BytesIO):
            def readline(self, size=-1):
                if size < 0 or size > FRAME_LIMIT + 2:
                    raise AssertionError("unbounded input read")
                return super().readline(size)

        output = io.BytesIO()
        self.adapter.serve(BoundedInput(b"x" * (FRAME_LIMIT * 2) + b"\n" + request(op="hello")),
                           output, self.consumer)
        results = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["result"], failure("evaluation_failure", "limit_exceeded"))
        self.assertEqual(results[1]["result"], self.consumer.hello())


class CommandLineTests(ConsumerCase):
    def run_cli(self, data, basis_path=None):
        command = [sys.executable, "-B", str(CLI)]
        if basis_path is not None:
            command.extend(["--basis", str(basis_path)])
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run(command, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              cwd="/", env=environment, timeout=15)

    def test_cli_runs_from_an_unrelated_cwd_with_clean_stdout(self):
        process = self.run_cli(request() + b"\n" + request(op="hello"))
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(process.stderr, b"")
        output = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(len(output), 2)
        self.assertEqual(output[0]["result"]["status"], "accepted_partial")
        self.assertEqual(output[1], {"id": "case-1", "result": self.consumer.hello()})

    def test_basis_path_selects_startup_fixture(self):
        with tempfile.TemporaryDirectory(dir=str(PYTHON_ROOT / "tests")) as directory:
            path = Path(directory) / "selected-basis.json"
            fixture = basis()
            fixture["input"]["amount_minor"] = "27"
            path.write_bytes(wire(fixture))
            document = bound_description(fixture)
            document["effects"][0]["quantities"][0]["value"] = "27"
            process = self.run_cli(request(wire(document)), path)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(json.loads(process.stdout)["result"]["status"], "accepted_partial")

    def test_invalid_unreadable_or_oversized_startup_config_is_not_a_review(self):
        with tempfile.TemporaryDirectory(dir=str(PYTHON_ROOT / "tests")) as directory:
            path = Path(directory) / "bad-basis.json"
            for raw in (None, b"private-bad-config", b"[]", b" " * (DOCUMENT_LIMIT + 1)):
                if raw is not None:
                    path.write_bytes(raw)
                process = self.run_cli(request(op="hello"), path)
                self.assertNotEqual(process.returncode, 0)
                self.assertEqual(process.stdout, b"")
                self.assertTrue(process.stderr)
                self.assertNotIn(b"private-bad-config", process.stderr)
                self.assertNotIn(b"Traceback", process.stderr)

    def test_basis_is_loaded_once_even_when_file_changes_between_frames(self):
        with tempfile.TemporaryDirectory(dir=str(PYTHON_ROOT / "tests")) as directory:
            path = Path(directory) / "basis.json"
            path.write_bytes(public_bytes("synthetic-basis.json"))
            command = [sys.executable, "-B", str(CLI), "--basis", str(path)]
            process = subprocess.Popen(command, cwd="/", stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                process.stdin.write(request(op="hello") + b"\n")
                process.stdin.flush()
                ready, _, _ = select.select([process.stdout], [], [], 10)
                self.assertTrue(ready, "CLI did not flush a response")
                self.assertEqual(json.loads(process.stdout.readline())["result"], self.consumer.hello())
                path.write_bytes(b"not a usable fixture anymore")
                output, errors = process.communicate(request(), timeout=10)
                self.assertEqual(process.returncode, 0, errors)
                self.assertEqual(json.loads(output)["result"]["status"], "accepted_partial")
            finally:
                if process.poll() is None:
                    process.kill()
                process.communicate()


if __name__ == "__main__":
    import unittest
    unittest.main()
