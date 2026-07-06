from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from core.constant.chrome_user_agent_pool_constant import (
    DEFAULT_TIMEOUT_SECOND_INT,
    KEY_VAL_AUTH_TOKEN_ENV_STR,
    KEY_VAL_AUTHORIZATION_HEADER_STR,
    KEY_VAL_BASE_URL_ENV_STR,
    KEY_VAL_HTTP_GET_METHOD_STR,
    KEY_VAL_HTTP_PUT_METHOD_STR,
    KEY_VAL_JSON_CONTENT_TYPE_STR,
    KEY_VAL_TEXT_CONTENT_TYPE_STR,
)
from core.helper.key_val_key_hash_helper import hashKeyValKey


class KeyValStoreProxyError(Exception):
    pass


class KeyValStoreProxy:
    def __init__(
        self,
        baseUrlStr: str | None = None,
        authTokenStr: str | None = None,
        timeoutSecondInt: int = DEFAULT_TIMEOUT_SECOND_INT,
    ) -> None:
        self.baseUrlStr = (
            os.getenv(KEY_VAL_BASE_URL_ENV_STR) if baseUrlStr is None else baseUrlStr
        )
        self.authTokenStr = (
            os.getenv(KEY_VAL_AUTH_TOKEN_ENV_STR) if authTokenStr is None else authTokenStr
        )
        self.timeoutSecondInt = timeoutSecondInt

    def getValue(self, keyStr: str) -> str | None:
        if not self.baseUrlStr:
            return None

        requestObject = Request(
            self.buildKeyUrl(keyStr),
            method=KEY_VAL_HTTP_GET_METHOD_STR,
            headers=self.buildHeaderDict(),
        )

        try:
            with urlopen(requestObject, timeout=self.timeoutSecondInt) as responseObject:
                return responseObject.read().decode("utf-8")
        except HTTPError as exc:
            if exc.code == 404:
                return None
            raise KeyValStoreProxyError("Unable to read Keyval value.") from exc
        except (URLError, TimeoutError, OSError, UnicodeDecodeError) as exc:
            raise KeyValStoreProxyError("Unable to read Keyval value.") from exc

    def setValue(self, keyStr: str, valueStr: str) -> bool:
        if not self.baseUrlStr:
            return False

        requestObject = Request(
            self.buildKeyUrl(keyStr),
            data=valueStr.encode("utf-8"),
            method=KEY_VAL_HTTP_PUT_METHOD_STR,
            headers=self.buildHeaderDict(KEY_VAL_TEXT_CONTENT_TYPE_STR),
        )

        try:
            with urlopen(requestObject, timeout=self.timeoutSecondInt):
                return True
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise KeyValStoreProxyError("Unable to write Keyval value.") from exc

    def getJson(self, keyStr: str) -> Any:
        valueStr = self.getValue(keyStr)
        if valueStr is None or valueStr == "":
            return None

        try:
            return json.loads(valueStr)
        except json.JSONDecodeError as exc:
            raise KeyValStoreProxyError("Stored Keyval value is not valid JSON.") from exc

    def setJson(self, keyStr: str, valueObject: Any) -> bool:
        valueStr = json.dumps(valueObject, sort_keys=True, separators=(",", ":"))
        if not self.baseUrlStr:
            return False

        requestObject = Request(
            self.buildKeyUrl(keyStr),
            data=valueStr.encode("utf-8"),
            method=KEY_VAL_HTTP_PUT_METHOD_STR,
            headers=self.buildHeaderDict(KEY_VAL_JSON_CONTENT_TYPE_STR),
        )

        try:
            with urlopen(requestObject, timeout=self.timeoutSecondInt):
                return True
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise KeyValStoreProxyError("Unable to write Keyval JSON value.") from exc

    def buildHeaderDict(self, contentTypeStr: str | None = None) -> dict[str, str]:
        headerDict: dict[str, str] = {}

        if contentTypeStr is not None:
            headerDict["Content-Type"] = contentTypeStr

        if self.authTokenStr:
            headerDict[KEY_VAL_AUTHORIZATION_HEADER_STR] = f"Bearer {self.authTokenStr}"

        return headerDict

    def buildKeyUrl(self, keyStr: str) -> str:
        if not self.baseUrlStr:
            raise KeyValStoreProxyError("KEY_VAL_BASE_URL is not configured.")

        hashedKeyStr = hashKeyValKey(keyStr)
        return f"{self.baseUrlStr.rstrip('/')}/{quote(hashedKeyStr)}"
