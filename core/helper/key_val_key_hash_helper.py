from __future__ import annotations

import hashlib

from core.constant.chrome_user_agent_pool_constant import KEY_VAL_KEY_HASH_ALGORITHM_STR


def hashKeyValKey(
    keyStr: str,
    algorithmStr: str = KEY_VAL_KEY_HASH_ALGORITHM_STR,
    namespaceStr: str | None = None,
) -> str:
    if not isinstance(keyStr, str) or not keyStr.strip():
        raise ValueError("Keyval key must be a non-empty string.")

    hashInputStr = keyStr.strip()
    if namespaceStr is not None and namespaceStr.strip():
        hashInputStr = f"{namespaceStr.strip()}:{hashInputStr}"

    try:
        hashObject = hashlib.new(algorithmStr)
    except ValueError as exc:
        raise ValueError(f"Unsupported hash algorithm: {algorithmStr}") from exc

    hashObject.update(hashInputStr.encode("utf-8"))
    return hashObject.hexdigest()
