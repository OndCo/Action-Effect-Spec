"""Independent test data/helpers restricted to the published example files."""

import base64
import copy
import hashlib
import importlib
import json
from pathlib import Path
import sys
import unittest


PYTHON_ROOT = Path(__file__).resolve().parents[1]
SPEC_ROOT = PYTHON_ROOT.parents[1]
EXAMPLES = SPEC_ROOT / "examples"
CLI = PYTHON_ROOT / "cli.py"
PROFILE_URI = "https://example.org/profiles/refund/0.1.0-draft.1"
PROFILE_HASH = "dddac40519b57620ca8b6fec558746ed8fb1f6ddf77263fd93cf5b2b582f2e00"
AMOUNT = "https://example.org/quantities/amount"
DOCUMENT_LIMIT = 1024 * 1024
FRAME_LIMIT = 2 * DOCUMENT_LIMIT

sys.path.insert(0, str(PYTHON_ROOT))


def public_bytes(name):
    return (EXAMPLES / name).read_bytes()


def example():
    return json.loads(public_bytes("partial-refund.json"))


def basis():
    return json.loads(public_bytes("synthetic-basis.json"))


def wire(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def fixture_digest(value):
    # Only ASCII-keyed fixture/description objects use this independent oracle.
    encoded = json.dumps(value, ensure_ascii=False, allow_nan=False,
                         sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def bound_description(fixture, document=None):
    document = copy.deepcopy(example() if document is None else document)
    for field, member in (("invocation", "input"),
                          ("implementation", "implementation"),
                          ("context", "context"), ("mapping", "mapping")):
        document[field]["digest"]["value"] = fixture_digest(fixture[member])
    for item in document["evidence"]:
        item["artifact_digest"]["value"] = fixture_digest(fixture["declaration"])
        item["source"] = fixture["declaration"]["issuer"]
    return document


def unknown_amount(document):
    document["effects"][0]["quantities"] = []
    document["unknowns"].append({
        "code": "unknown_quantity", "scope": "amount was not supplied",
        "target": {"effect_id": document["effects"][0]["effect_id"],
                   "quantity_name": AMOUNT},
    })
    return document


def at(document, path):
    for key in path:
        document = document[key]
    return document


def request(document=None, op="check", identifier="case-1"):
    value = {"id": identifier, "op": op}
    if op != "hello":
        value["document_b64"] = base64.b64encode(
            public_bytes("partial-refund.json") if document is None else document
        ).decode("ascii")
    return wire(value)


def failure(status, reason):
    return {"status": status, "reason": reason, "authority": "not_evaluated"}


class ModuleCase(unittest.TestCase):
    def module(self, name):
        qualified = "offline_consumer." + name
        try:
            return importlib.import_module(qualified)
        except ModuleNotFoundError as error:
            if error.name in ("offline_consumer", qualified):
                self.fail("Implementation module is not present: " + qualified)
            raise

    def assert_rejection(self, function, status, reason):
        errors = self.module("errors")
        with self.assertRaises(errors.Rejection) as caught:
            function()
        self.assertEqual(caught.exception.result(), failure(status, reason))


class ConsumerCase(ModuleCase):
    def setUp(self):
        self.consumer_module = self.module("consumer")
        self.configuration = self.module("configuration")
        self.consumer = self.new_consumer()

    def new_consumer(self, fixture=None):
        snapshot = self.configuration.Snapshot.from_bytes(
            public_bytes("synthetic-basis.json") if fixture is None else wire(fixture),
            public_bytes("refund-profile.json"),
        )
        return self.consumer_module.Consumer(snapshot)

    def check(self, document, consumer=None):
        return (self.consumer if consumer is None else consumer).check(wire(document))

    def assert_failure(self, document, status, reason, consumer=None):
        self.assertEqual(self.check(document, consumer), failure(status, reason))

    def assert_accepted(self, document, consumer=None):
        self.assertEqual(self.check(document, consumer), {
            "status": "accepted_partial", "reason": "declared_partial",
            "authority": "not_evaluated", "description_digest": fixture_digest(document),
            "effect_count": len(document["effects"]),
            "unresolved_count": len(document["unknowns"]),
        })
