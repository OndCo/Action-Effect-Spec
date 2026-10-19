"""RFC 3986 Appendix A generic URI syntax, without resolution or normalization."""

from ipaddress import AddressValueError, IPv6Address
import re
from string import ascii_letters, digits
from typing import Any, FrozenSet


_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*")
_HEX = frozenset("0123456789abcdefABCDEF")
_DIGITS = frozenset(digits)
_REG_NAME = frozenset(ascii_letters + digits + "-._~!$&'()*+,;=")
_USERINFO = _REG_NAME | frozenset(":")
_PATH = _USERINFO | frozenset("@/")
_QUERY_FRAGMENT = _PATH | frozenset("?")
_IPV6_CHARACTERS = _HEX | frozenset(":.")


def _component(value: str, characters: FrozenSet[str]) -> bool:
    index = 0
    while index < len(value):
        if value[index] in characters:
            index += 1
        elif (value[index] == "%" and index + 2 < len(value)
              and value[index + 1] in _HEX and value[index + 2] in _HEX):
            index += 3
        else:
            return False
    return True


def _ip_literal(value: str) -> bool:
    if value.startswith(("v", "V")):
        version, separator, address = value[1:].partition(".")
        return (bool(version) and bool(separator) and bool(address)
                and all(character in _HEX for character in version)
                and all(character in _USERINFO for character in address))
    # The longest IPv6 form includes a dotted IPv4 tail. Zone IDs are not in
    # Appendix A, even if a newer standard-library parser would accept them.
    if (not value or len(value) > 45
            or any(character not in _IPV6_CHARACTERS for character in value)):
        return False
    try:
        IPv6Address(value)
    except AddressValueError:
        return False
    return True


def _port(value: str) -> bool:
    return all(character in _DIGITS for character in value)


def _authority(value: str) -> bool:
    userinfo, separator, host_port = value.partition("@")
    if separator:
        if not _component(userinfo, _USERINFO):
            return False
    else:
        host_port = value

    if host_port.startswith("["):
        closing = host_port.find("]")
        if closing < 0 or not _ip_literal(host_port[1:closing]):
            return False
        suffix = host_port[closing + 1:]
        return not suffix or (suffix.startswith(":") and _port(suffix[1:]))

    host, separator, port = host_port.partition(":")
    # IPv4-looking text that does not match IPv4address can still be reg-name.
    return _component(host, _REG_NAME) and (not separator or _port(port))


def is_uri(value: Any) -> bool:
    """Check URI grammar plus the profile's nonempty post-scheme requirement."""
    if not isinstance(value, str):
        return False
    scheme, separator, remainder = value.partition(":")
    if not separator or not remainder or _SCHEME.fullmatch(scheme) is None:
        return False

    body, fragment_marker, fragment = remainder.partition("#")
    if fragment_marker and not _component(fragment, _QUERY_FRAGMENT):
        return False
    hierarchy, query_marker, query = body.partition("?")
    if query_marker and not _component(query, _QUERY_FRAGMENT):
        return False

    if hierarchy.startswith("//"):
        authority, slash, tail = hierarchy[2:].partition("/")
        path = slash + tail
        return _authority(authority) and _component(path, _PATH)
    return _component(hierarchy, _PATH)
