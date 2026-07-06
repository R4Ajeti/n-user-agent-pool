from __future__ import annotations

import hashlib

from core.constant.chrome_user_agent_pool_constant import KEY_VAL_KEY_HASH_ALGORITHM_STR


def hashKeyValKey(
    keyStr: str,
    algorithmStr: str = KEY_VAL_KEY_HASH_ALGORITHM_STR,
) -> str:
    if not isinstance(keyStr, str) or not keyStr.strip():
        raise ValueError("Keyval key must be a non-empty string.")

    try:
        hashObject = hashlib.new(algorithmStr)
    except ValueError as exc:
        raise ValueError(f"Unsupported hash algorithm: {algorithmStr}") from exc

    hashObject.update(keyStr.strip().encode("utf-8"))
    return hashObject.hexdigest()
