from __future__ import annotations

import base64
import binascii
import json
from typing import Any


def decodeBase64JsonObject(encodedValueStr: str) -> dict[str, Any]:
    if not isinstance(encodedValueStr, str) or not encodedValueStr.strip():
        raise ValueError("Base64 JSON value must be a non-empty string.")

    try:
        decodedByte = base64.b64decode(encodedValueStr.strip(), validate=True)
        decodedTextStr = decodedByte.decode("utf-8")
        valueObject = json.loads(decodedTextStr)
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Base64 JSON value is invalid.") from exc

    if not isinstance(valueObject, dict):
        raise ValueError("Base64 JSON value must decode to a JSON object.")

    return valueObject
