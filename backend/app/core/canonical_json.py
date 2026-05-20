"""Canonical JSON serialization aligned with RFC 8785 JCS principals.

RFC 8785 specifies lexicographically sorted object keys, minimal separators,
no insignificant whitespace, and deterministic Unicode serialization. Python's
:class:`json.JSONEncoder` is used with UTF-8 logical content; callers should
normalize composite structures to JSON-native types (:class:`dict`, :class:`list`,
:class:`str`, :class:`int`, :class:`float`, :class:`bool`, or ``None``) before
serializing numerics requiring ES6-compatible canonical forms for strict
court-grade audits.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Mapping


def _sort_mapping(obj: Any) -> Any:
    """Return a recursively key-sorted structure suitable for canonical JSON.

    Args:
        obj: Arbitrary nested structure consisting of dictionaries, sequences,
            and JSON scalars.

    Returns:
        A new structure with dictionaries replaced by OrderedDict sorted by
        lexical order of Unicode string keys.

    Raises:
        TypeError: If a dictionary key is not of type ``str``.
    """
    if isinstance(obj, Mapping):
        for key in obj:
            if not isinstance(key, str):
                msg = "Canonical JSON requires string object keys."
                raise TypeError(msg)
        sorted_keys = sorted(obj.keys())
        return OrderedDict((k, _sort_mapping(obj[k])) for k in sorted_keys)
    if isinstance(obj, (list, tuple)):
        return [_sort_mapping(item) for item in obj]
    return obj


def canonical_json_dumps(obj: Mapping[str, Any]) -> str:
    """Serialize a mapping to canonical compact JSON suitable for hashing.

    Object keys at every depth are emitted in unicode code-point lexical order.

    Args:
        obj: JSON-like root object (typically a dictionary).

    Returns:
        Canonical JSON string without extraneous whitespace, using ``:``
        and ``,`` separators without following spaces.

    Raises:
        TypeError: If ``obj`` includes values that cannot be encoded as JSON.

    Examples:
        >>> canonical_json_dumps({"b": 1, "a": {"c": True, "b": False}})
        '{"a":{"b":false,"c":true},"b":1}'
    """
    import json

    normalized = _sort_mapping(dict(obj))
    # RFC 8785 / JCS: UTF-8, no insignificant whitespace.
    # ensure_ascii=False preserves Unicode outside Basic Multilingual Plane.
    return json.dumps(normalized, separators=(",", ":"), ensure_ascii=False, sort_keys=False)
