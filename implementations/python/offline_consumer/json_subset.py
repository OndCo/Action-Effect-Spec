"""Strict UTF-8 JSON and the safe-integer-token-only RFC 8785 subset."""

import hashlib
import json
from typing import Any

from .errors import Rejection


MAX_DOCUMENT_BYTES = 1024 * 1024
MAX_DEPTH = 64
MAX_SAFE_INTEGER = 9007199254740991
_UNSUPPORTED_NUMBER = object()


def _syntax() -> None:
    raise Rejection("invalid_input", "syntax")


def _depth_limit(raw: bytes, maximum: int) -> None:
    depth = 0
    quoted = False
    escaped = False
    for character in raw:
        if quoted:
            if escaped:
                escaped = False
            elif character == 92:
                escaped = True
            elif character == 34:
                quoted = False
        elif character == 34:
            quoted = True
        elif character in (91, 123):
            depth += 1
            if depth > maximum:
                raise Rejection("evaluation_failure", "limit_exceeded")
        elif character in (93, 125):
            depth = max(0, depth - 1)


def _integer(token: str) -> Any:
    digits = token[1:] if token.startswith("-") else token
    if len(digits) > 16 or (len(digits) == 16 and digits > "9007199254740991"):
        return _UNSUPPORTED_NUMBER
    return int(token)


def _fraction_or_exponent(token: str) -> Any:
    return _UNSUPPORTED_NUMBER


def _nonfinite(token: str) -> None:
    _syntax()


def _unique_object(pairs: Any) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            _syntax()
        result[key] = value
    return result


def _scalar_string(value: str) -> None:
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        _syntax()


def _check_scalars(value: Any) -> bool:
    unsupported = value is _UNSUPPORTED_NUMBER
    if isinstance(value, str):
        _scalar_string(value)
    elif isinstance(value, list):
        for child in value:
            unsupported = _check_scalars(child) or unsupported
    elif isinstance(value, dict):
        for key, child in value.items():
            _scalar_string(key)
            unsupported = _check_scalars(child) or unsupported
    return unsupported


def parse_json(raw: bytes, *, max_bytes: int = MAX_DOCUMENT_BYTES,
               max_depth: int = MAX_DEPTH) -> Any:
    """Parse all syntax/scalars before rejecting unsupported numeric tokens."""
    if not isinstance(raw, bytes):
        raise TypeError("JSON input must be raw bytes")
    if len(raw) > max_bytes:
        raise Rejection("evaluation_failure", "limit_exceeded")
    _depth_limit(raw, max_depth)
    if raw.startswith(b"\xef\xbb\xbf"):
        _syntax()
    try:
        value = json.loads(raw.decode("utf-8", errors="strict"),
                           object_pairs_hook=_unique_object, parse_int=_integer,
                           parse_float=_fraction_or_exponent, parse_constant=_nonfinite)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise Rejection("invalid_input", "syntax") from None
    if _check_scalars(value):
        raise Rejection("unsupported_profile", "numeric_domain")
    return value


def _encode(value: Any, depth: int) -> str:
    if value is None:
        return "null"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is int:
        if abs(value) > MAX_SAFE_INTEGER:
            raise Rejection("unsupported_profile", "numeric_domain")
        return str(value)
    if isinstance(value, float):
        raise Rejection("unsupported_profile", "numeric_domain")
    if isinstance(value, str):
        _scalar_string(value)
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (dict, list)):
        depth += 1
        if depth > MAX_DEPTH:
            raise Rejection("evaluation_failure", "limit_exceeded")
        if isinstance(value, list):
            return "[" + ",".join(_encode(child, depth) for child in value) + "]"
        for key in value:
            if not isinstance(key, str):
                _syntax()
            _scalar_string(key)
        # Scalar-valid UTF-16BE byte order is UTF-16 code-unit order.
        keys = sorted(value, key=lambda key: key.encode("utf-16-be"))
        return "{" + ",".join(_encode(key, depth) + ":" + _encode(value[key], depth)
                              for key in keys) + "}"
    raise TypeError("Value is outside the supported JSON data model")


def canonical_bytes(value: Any) -> bytes:
    """Canonicalize a parsed subset value, without normalizing any strings."""
    return _encode(value, 0).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()
