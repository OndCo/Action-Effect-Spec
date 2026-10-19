"""Bounded JSON-lines transport, with recovery at the next LF boundary."""

import base64
import binascii
import json
from typing import Any, BinaryIO, Dict, Iterator, Optional, Tuple

from .consumer import Consumer
from .errors import Rejection, outcome
from .json_subset import parse_json


MAX_FRAME_BYTES = 2 * 1024 * 1024
_DRAIN_CHUNK = 64 * 1024


def _frames(stream: BinaryIO) -> Iterator[Optional[bytes]]:
    while True:
        chunk = stream.readline(MAX_FRAME_BYTES + 2)
        if not chunk:
            return
        ended = chunk.endswith(b"\n")
        raw = chunk[:-1] if ended else chunk
        if len(raw) > MAX_FRAME_BYTES:
            while not ended:
                chunk = stream.readline(_DRAIN_CHUNK)
                if not chunk:
                    break
                ended = chunk.endswith(b"\n")
            yield None
        else:
            yield raw


def _transport() -> None:
    raise Rejection("invalid_input", "transport")


def _request(raw: bytes) -> Tuple[str, str, Optional[bytes]]:
    try:
        request = parse_json(raw, max_bytes=MAX_FRAME_BYTES)
    except Rejection:
        _transport()
    if not isinstance(request, dict):
        _transport()
    identifier = request.get("id")
    operation = request.get("op")
    if not isinstance(identifier, str) or not 1 <= len(identifier) <= 128:
        _transport()
    if operation not in ("check", "canonicalize", "hello"):
        _transport()
    fields = {"id", "op"} if operation == "hello" else {"id", "op", "document_b64"}
    if request.keys() != fields:
        _transport()
    if operation == "hello":
        return identifier, operation, None
    encoded = request["document_b64"]
    if not isinstance(encoded, str):
        _transport()
    try:
        ascii_bytes = encoded.encode("ascii")
        document = base64.b64decode(ascii_bytes, validate=True)
    except (UnicodeEncodeError, binascii.Error, ValueError):
        _transport()
    if base64.b64encode(document) != ascii_bytes:
        _transport()
    return identifier, operation, document


def _response(raw: Optional[bytes], consumer: Consumer) -> Dict[str, Any]:
    identifier = None
    try:
        if raw is None:
            raise Rejection("evaluation_failure", "limit_exceeded")
        identifier, operation, document = _request(raw)
        if operation == "hello":
            result = consumer.hello()
        elif operation == "canonicalize":
            result = consumer.canonicalize(document)
        else:
            result = consumer.check(document)
    except Rejection as rejected:
        result = rejected.result()
    except Exception:
        result = outcome("evaluation_failure", "internal_error")
    return {"id": identifier, "result": result}


def serve(source: BinaryIO, destination: BinaryIO, consumer: Consumer) -> None:
    """Write and flush one response per frame; no request can select a file."""
    for frame in _frames(source):
        response = _response(frame, consumer)
        try:
            encoded = json.dumps(response, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
        except Exception:
            response = {"id": response["id"], "result": outcome("evaluation_failure", "internal_error")}
            encoded = json.dumps(response, separators=(",", ":"))
        destination.write(encoded.encode("ascii") + b"\n")
        destination.flush()
