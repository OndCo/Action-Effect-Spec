"""Caller-selected local startup configuration; never request-selected I/O."""

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
import re
from typing import Any, Dict, Optional, Tuple

from .errors import Rejection
from .json_subset import MAX_DOCUMENT_BYTES, canonical_bytes, canonical_sha256, parse_json
from .structure import is_uri


PROFILE_URI = "https://example.org/profiles/refund/0.1.0-draft.1"
PROFILE_HASH = "dddac40519b57620ca8b6fec558746ed8fb1f6ddf77263fd93cf5b2b582f2e00"
AMOUNT_NAME = "https://example.org/quantities/amount"
_EXAMPLES = Path(__file__).resolve().parents[3] / "examples"
DEFAULT_BASIS = _EXAMPLES / "synthetic-basis.json"
_MANIFEST = _EXAMPLES / "refund-profile.json"
_AMOUNT = re.compile(r"(?:0|[1-9][0-9]{0,11})")


class ConfigurationError(Exception):
    """An unusable startup configuration, not a per-document review."""


@dataclass(frozen=True)
class BoundMember:
    field: str
    reference: str
    preimage: bytes
    revision: Optional[str] = None

    def matches_digest(self, digest: Dict[str, Any]) -> bool:
        return (digest["algorithm"] == "sha-256"
                and digest["value"] == hashlib.sha256(self.preimage).hexdigest())


@dataclass(frozen=True)
class RefundInputs:
    applicable: bool
    order: Optional[str]
    amount: Optional[str]


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and len(value) > 0


def _refund_inputs(basis: Dict[str, Any], manifest: Dict[str, Any]) -> RefundInputs:
    invocation = basis["input"]
    implementation = basis["implementation"]
    context = basis["context"]
    mapping = basis["mapping"]
    implementation_rule = manifest["implementation_constraints"]
    mapping_rule = next(row for row in manifest["reference_resolution"] if row["field"] == "mapping.id")
    quantity_rule = manifest["quantity_definitions"][0]
    order = invocation.get("order")
    amount = invocation.get("amount_minor")
    applicable = (
        invocation.get("operation") == "refund" and _nonempty(order)
        and invocation.get("currency") == "USD" and _nonempty(context.get("account"))
        and context.get("destination") == "original-payment"
        and context.get("environment") == "synthetic"
        and implementation.get("name") == implementation_rule["name"]
        and implementation.get("version") == implementation_rule["version"]
        and implementation.get("visibility") == "declared"
        and mapping.get("id") == mapping_rule["reference"]
        and mapping.get("revision") == mapping_rule["revision"]
        and is_uri(basis["declaration"].get("issuer"))
    )
    if "amount_minor" in invocation:
        applicable = applicable and (
            isinstance(amount, str) and _AMOUNT.fullmatch(amount) is not None
            and int(quantity_rule["value_min"]) <= int(amount) <= int(quantity_rule["value_max"])
        )
    return RefundInputs(bool(applicable), order if isinstance(order, str) else None,
                        amount if isinstance(amount, str) else None)


@dataclass(frozen=True)
class Snapshot:
    """Only immutable preimage bytes and scalar projection data survive loading."""

    members: Tuple[BoundMember, ...]
    issuer: Optional[str]
    refund: RefundInputs
    profile_digest: str = field(default=PROFILE_HASH, init=False)

    @classmethod
    def from_bytes(cls, basis_bytes: bytes, manifest_bytes: bytes) -> "Snapshot":
        try:
            manifest = parse_json(manifest_bytes)
            if canonical_sha256(manifest) != PROFILE_HASH:
                raise ConfigurationError("profile manifest does not match the pinned hash")
            basis = parse_json(basis_bytes)
            rows = manifest["reference_resolution"]
            if (type(basis) is not dict
                    or any(type(basis.get(row["member"])) is not dict for row in rows)):
                raise ConfigurationError("required selected fixture objects are missing or malformed")
            members = tuple(BoundMember(row["field"], row["reference"],
                                        canonical_bytes(basis[row["member"]]), row.get("revision"))
                            for row in rows)
            issuer = basis["declaration"].get("issuer")
            return cls(members, issuer if isinstance(issuer, str) else None,
                       _refund_inputs(basis, manifest))
        except Rejection:
            raise ConfigurationError("startup JSON is invalid, over limit, or outside the supported subset") from None

    def validate_bindings(self, document: Dict[str, Any]) -> None:
        for member in self.members:
            if member.field == "evidence.artifact_ref":
                for evidence in document["evidence"]:
                    if not (evidence["artifact_ref"] == member.reference
                            and evidence["source"] == self.issuer
                            and evidence["kind"] == "declaration"
                            and member.matches_digest(evidence["artifact_digest"])):
                        raise Rejection("untrusted_evidence", "artifact_binding")
            else:
                owner, selector = member.field.split(".")
                binding = document[owner]
                if not (binding[selector] == member.reference
                        and (member.revision is None or binding["revision"] == member.revision)
                        and member.matches_digest(binding["digest"])):
                    raise Rejection("untrusted_evidence", "artifact_binding")


def _read_bounded(path: Path) -> bytes:
    try:
        with path.open("rb") as stream:
            return stream.read(MAX_DOCUMENT_BYTES + 1)
    except OSError:
        raise ConfigurationError("startup file is unreadable") from None


def load_snapshot(basis_path: Optional[Path] = None) -> Snapshot:
    path = DEFAULT_BASIS if basis_path is None else Path(basis_path)
    return Snapshot.from_bytes(_read_bounded(path), _read_bounded(_MANIFEST))
