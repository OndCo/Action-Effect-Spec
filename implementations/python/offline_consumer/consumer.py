"""Ordered processing under the v1 and opt-in v1.1 offline contracts."""

import base64
import hashlib
from typing import Any, Dict

from .configuration import AMOUNT_NAME, PROFILE_URI, ConfigurationError, Snapshot
from .errors import Rejection, outcome
from .json_subset import canonical_bytes, canonical_sha256, parse_json
from .projection import validate_projection
from .references import validate_references
from .structure import SPEC_VERSION, validate_structure


class Consumer:
    def __init__(self, snapshot: Snapshot, *, contract: str = "offline-consumer-v1") -> None:
        if contract not in ("offline-consumer-v1", "offline-consumer-v1.1"):
            raise ConfigurationError("unsupported consumer contract")
        self._snapshot = snapshot
        self._contract = contract

    def hello(self=None) -> Dict[str, Any]:
        # Keep the legacy class-level Consumer.hello() v1 query callable.
        result = outcome("capabilities", "offline_snapshot", spec_version=SPEC_VERSION,
                         profile=PROFILE_URI, numeric_domain="safe_integer_tokens_only",
                         acceptance_cache=False)
        if self is not None and self._contract == "offline-consumer-v1.1":
            result["contract"] = self._contract
        return result

    def check(self, raw: bytes) -> Dict[str, Any]:
        return self._evaluate(raw, diagnostic=False)

    def canonicalize(self, raw: bytes) -> Dict[str, Any]:
        return self._evaluate(raw, diagnostic=True)

    def _evaluate(self, raw: bytes, diagnostic: bool) -> Dict[str, Any]:
        try:
            document = parse_json(raw)
            if diagnostic:
                encoded = canonical_bytes(document)
                return outcome("canonicalized", "supported_subset",
                               canonical_b64=base64.b64encode(encoded).decode("ascii"),
                               sha256=hashlib.sha256(encoded).hexdigest())

            if not isinstance(document, dict) or not isinstance(document.get("spec_version"), str):
                raise Rejection("invalid_input", "structure")
            if document["spec_version"] != SPEC_VERSION:
                raise Rejection("unsupported_profile", "spec_version")
            validate_structure(document)
            validate_references(document, AMOUNT_NAME)
            if document["critical_extensions"]:
                raise Rejection("unsupported_profile", "critical_extension")
            if document["profile"] != PROFILE_URI:
                raise Rejection("unsupported_profile", "profile")
            if document["profile_digest"]["value"] != self._snapshot.profile_digest:
                raise Rejection("untrusted_evidence", "profile_binding")
            coverage = document["coverage"]
            if (coverage["scope"] != "direct" or coverage["completeness"] != "partial"
                    or any(effect["modality"] != "may" for effect in document["effects"])
                    or any(item["kind"] != "declaration" for item in document["evidence"])):
                raise Rejection("unsupported_profile", "evidence_scope")
            self._snapshot.validate_bindings(document)
            validate_projection(document, self._snapshot)
            return outcome("accepted_partial", "declared_partial",
                           description_digest=canonical_sha256(document),
                           effect_count=len(document["effects"]), unresolved_count=len(document["unknowns"]))
        except Rejection as rejected:
            return rejected.result()
        except Exception:
            return outcome("evaluation_failure", "internal_error")
