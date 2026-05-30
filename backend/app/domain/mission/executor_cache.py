"""Opt-in in-process cache for EASY cognition outputs (token-spend dedup).

Keyed by the deterministic prompt hash (``provider:model:input_hash``). When an
operator sets ``MISSION_EXECUTOR_CACHE_TTL_SECONDS`` > 0, an identical prompt
served within the TTL reuses the upstream's textual result instead of issuing
another paid completion. The HDR minted on a cache hit therefore carries the
same input/output hashes as the original call — a transparent, verifiable
signal that the cognition was deduplicated rather than freshly computed.

Forensic posture: DISABLED by default. With TTL 0 nothing is ever stored or
read, so each HDR reflects a real upstream invocation. The cache is process-
local (not shared across workers), bounded in size, and stores only the
provider's returned text — never API keys or request bodies.

Thread/async-safety: a single ``threading.Lock`` guards the store. Operations
are O(1) dict access plus occasional bounded eviction; the lock is never held
across I/O.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict

# Hard ceiling on retained entries — bounds memory regardless of TTL. FIFO/LRU
# eviction (OrderedDict, move-to-end on read) keeps the hottest prompts.
_MAX_ENTRIES = 512

_lock = threading.Lock()
# key -> (expires_at_epoch, cached_text)
_store: "OrderedDict[str, tuple[float, str]]" = OrderedDict()


def make_key(*, provider: str, model: str, input_hash: str) -> str:
    """Compose the namespaced cache key (provider+model isolate cognitions)."""
    return f"{provider}:{model}:{input_hash}"


def get(key: str) -> str | None:
    """Return cached text for ``key`` if present and unexpired, else None."""
    now = time.time()
    with _lock:
        entry = _store.get(key)
        if entry is None:
            return None
        expires_at, text = entry
        if expires_at <= now:
            # Expired — drop it lazily.
            _store.pop(key, None)
            return None
        # Mark as most-recently-used.
        _store.move_to_end(key)
        return text


def put(key: str, text: str, *, ttl_seconds: int) -> None:
    """Store ``text`` under ``key`` for ``ttl_seconds``. No-op when ttl <= 0."""
    if ttl_seconds <= 0:
        return
    expires_at = time.time() + ttl_seconds
    with _lock:
        _store[key] = (expires_at, text)
        _store.move_to_end(key)
        # Evict oldest until within the size ceiling.
        while len(_store) > _MAX_ENTRIES:
            _store.popitem(last=False)


def clear() -> None:
    """Drop all entries (test hook / operational reset)."""
    with _lock:
        _store.clear()
