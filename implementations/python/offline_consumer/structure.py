"""Explicit checks for the published schema, after strict byte parsing."""

import re
from typing import Any, Callable, Iterable

from .errors import Rejection
from .uri import is_uri


SPEC_VERSION = "0.1.0-draft.1"
_DIGEST = re.compile(r"[0-9a-f]{64}")
_INTEGER_STRING = re.compile(r"(?:0|-?[1-9][0-9]{0,77})")
_SCALE = re.compile(r"(?:0|[1-9]|1[0-8])")
_ROOT_FIELDS = (
    "spec_version", "profile", "profile_digest", "record_id", "invocation",
    "implementation", "mapping", "context", "coverage", "effects", "evidence",
    "unknowns", "relations", "critical_extensions", "extensions",
)
_UNKNOWN_CODES = (
    "unmapped", "missing_context", "unresolved_identity", "unobserved_descendants",
    "conflicting_evidence", "unsupported_implementation", "unknown_quantity",
)


def _require(condition: bool) -> None:
    if not condition:
        raise Rejection("invalid_input", "structure")


def _object(value: Any, required: Iterable[str], optional: Iterable[str] = ()) -> None:
    _require(type(value) is dict)
    required = set(required)
    _require(required <= value.keys() <= required | set(optional))


def _string(value: Any) -> None:
    _require(isinstance(value, str) and len(value) > 0)


def _uri(value: Any) -> None:
    _require(is_uri(value))


def _enum(value: Any, choices: Iterable[str]) -> None:
    _require(isinstance(value, str) and value in choices)


def _array(value: Any, maximum: int, item: Callable[[Any], None],
           unique: bool = False) -> None:
    _require(type(value) is list and len(value) <= maximum)
    for child in value:
        item(child)
    if unique:
        _require(len(set(value)) == len(value))


def _digest(value: Any) -> None:
    _object(value, ("algorithm", "value"))
    _require(value["algorithm"] == "sha-256")
    _string(value["value"])
    _require(_DIGEST.fullmatch(value["value"]) is not None)


def _binding(value: Any) -> None:
    _object(value, ("reference", "digest"))
    _string(value["reference"])
    _digest(value["digest"])


def _evidence_refs(value: Any) -> None:
    _array(value, 256, _string, unique=True)


def _slot(value: Any) -> None:
    _require(type(value) is dict)
    state = value.get("state")
    if state == "known":
        _object(value, ("state", "namespace", "value"))
        _uri(value["namespace"])
        _string(value["value"])
    elif state == "none":
        _object(value, ("state",))
    elif state == "unknown":
        _object(value, ("state", "reason"))
        _string(value["reason"])
    else:
        _require(False)


def _quantity(value: Any) -> None:
    _object(value, ("name", "value", "unit", "scale"))
    _uri(value["name"])
    _string(value["value"])
    _require(len(value["value"]) <= 79 and _INTEGER_STRING.fullmatch(value["value"]) is not None)
    _string(value["unit"])
    _string(value["scale"])
    _require(_SCALE.fullmatch(value["scale"]) is not None)


def _effect(value: Any) -> None:
    _object(value, ("effect_id", "category", "operation", "resource", "destination",
                    "data_class", "quantities", "modality", "evidence_refs"), ("occurrence_ref",))
    _string(value["effect_id"])
    _uri(value["category"])
    _uri(value["operation"])
    for field in ("resource", "destination", "data_class"):
        _slot(value[field])
    _array(value["quantities"], 64, _quantity)
    _enum(value["modality"], ("may", "observed"))
    if "occurrence_ref" in value:
        _string(value["occurrence_ref"])
    if value["modality"] == "observed":
        _require("occurrence_ref" in value)
    _evidence_refs(value["evidence_refs"])


def _evidence(value: Any) -> None:
    _object(value, ("evidence_id", "kind", "source", "artifact_ref", "artifact_digest", "scope"))
    _string(value["evidence_id"])
    _enum(value["kind"], ("declaration", "observation", "analysis", "review"))
    _uri(value["source"])
    _uri(value["artifact_ref"])
    _digest(value["artifact_digest"])
    _string(value["scope"])


def _unknown(value: Any) -> None:
    _object(value, ("code", "scope"), ("target",))
    _enum(value["code"], _UNKNOWN_CODES)
    _string(value["scope"])
    if value["code"] == "unknown_quantity":
        _require("target" in value)
        _object(value["target"], ("effect_id", "quantity_name"))
        _string(value["target"]["effect_id"])
        _uri(value["target"]["quantity_name"])
    else:
        _require("target" not in value)


def _relation(value: Any) -> None:
    _object(value, ("from", "to", "kind", "evidence_refs"))
    _string(value["from"])
    _string(value["to"])
    _uri(value["kind"])
    _evidence_refs(value["evidence_refs"])


def validate_structure(document: Any) -> None:
    _object(document, _ROOT_FIELDS)
    _require(document["spec_version"] == SPEC_VERSION)
    _uri(document["profile"])
    _digest(document["profile_digest"])
    _uri(document["record_id"])
    for field in ("invocation", "implementation", "context"):
        _binding(document[field])

    mapping = document["mapping"]
    _object(mapping, ("id", "revision", "digest"))
    _uri(mapping["id"])
    _string(mapping["revision"])
    _digest(mapping["digest"])

    coverage = document["coverage"]
    _object(coverage, ("scope", "completeness", "assumptions", "evidence_refs"))
    _enum(coverage["scope"], ("direct", "transitive"))
    _enum(coverage["completeness"], ("partial", "bounded_claim"))
    _array(coverage["assumptions"], 64, _string, unique=True)
    _evidence_refs(coverage["evidence_refs"])

    _array(document["effects"], 256, _effect)
    _array(document["evidence"], 256, _evidence)
    _array(document["unknowns"], 256, _unknown)
    _array(document["relations"], 1024, _relation)
    _array(document["critical_extensions"], 64, _uri, unique=True)
    _require(type(document["extensions"]) is dict and len(document["extensions"]) <= 64)
    for key in document["extensions"]:
        _uri(key)
