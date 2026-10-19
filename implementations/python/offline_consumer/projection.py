"""The finite synthetic refund declaration, not effect inference or authority."""

from typing import Any, Dict

from .configuration import AMOUNT_NAME, Snapshot
from .errors import Rejection


def _require(condition: bool) -> None:
    if not condition:
        raise Rejection("untrusted_evidence", "effect_projection")


def _known(namespace: str, value: str) -> Dict[str, str]:
    return {"state": "known", "namespace": namespace, "value": value}


def validate_projection(document: Dict[str, Any], snapshot: Snapshot) -> None:
    """Requires shape, references, scope and artifact bindings already checked."""
    if not snapshot.refund.applicable:
        raise Rejection("untrusted_evidence", "applicability")
    _require(len(document["effects"]) == 1)
    effect = document["effects"][0]
    quantities = effect["quantities"]
    unknown_amounts = [unknown for unknown in document["unknowns"] if unknown["code"] == "unknown_quantity"]
    if not any(quantity["name"] == AMOUNT_NAME for quantity in quantities) and not unknown_amounts:
        raise Rejection("invalid_input", "structure")

    _require(effect["category"] == "https://example.org/effects/funds-transfer/1")
    _require(effect["operation"] == "https://example.org/operations/refund/1")
    _require(effect["resource"] == _known("https://example.org/resource-types/order", snapshot.refund.order))
    _require(effect["destination"] == _known("https://example.org/destination-types/payment", "original-payment"))
    _require(effect["data_class"] == _known("https://example.org/classification", "synthetic-transaction"))
    _require(effect["modality"] == "may" and "occurrence_ref" not in effect)
    _require(not document["relations"])
    _require(bool(document["coverage"]["evidence_refs"]) and bool(effect["evidence_refs"]))
    _require(any(unknown["code"] == "unobserved_descendants" for unknown in document["unknowns"]))

    if snapshot.refund.amount is None:
        _require(not quantities and len(unknown_amounts) == 1)
    else:
        expected = {"name": AMOUNT_NAME, "value": snapshot.refund.amount, "unit": "USD", "scale": "2"}
        _require(quantities == [expected] and not unknown_amounts)
