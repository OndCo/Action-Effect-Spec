"""Local semantic integrity, with distinct effect and evidence namespaces."""

from typing import Any, Dict

from .errors import Rejection


def _require(condition: bool) -> None:
    if not condition:
        raise Rejection("invalid_input", "references")


def validate_references(document: Dict[str, Any], amount_name: str) -> None:
    """Requires schema-valid input; this establishes no evidence support."""
    effects = {effect["effect_id"]: effect for effect in document["effects"]}
    evidence_ids = {item["evidence_id"] for item in document["evidence"]}
    _require(len(effects) == len(document["effects"]))
    _require(len(evidence_ids) == len(document["evidence"]))

    owners = [document["coverage"]] + document["effects"] + document["relations"]
    for owner in owners:
        _require(all(reference in evidence_ids for reference in owner["evidence_refs"]))
    for relation in document["relations"]:
        _require(relation["from"] in effects and relation["to"] in effects)

    known = {}
    for effect_id, effect in effects.items():
        names = {quantity["name"] for quantity in effect["quantities"]}
        _require(len(names) == len(effect["quantities"]))
        known[effect_id] = names

    targets = set()
    for unknown in document["unknowns"]:
        if unknown["code"] != "unknown_quantity":
            continue
        target = unknown["target"]
        pair = (target["effect_id"], target["quantity_name"])
        _require(pair[0] in effects and pair[1] == amount_name)
        _require(pair not in targets and pair[1] not in known[pair[0]])
        targets.add(pair)
