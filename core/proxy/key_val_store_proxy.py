from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from core.constant.chrome_user_agent_pool_constant import (
    CORE_LOGGER_NAME_STR,
    DEFAULT_TIMEOUT_SECOND_INT,
    KEY_VAL_AUTH_TOKEN_ENV_STR,
    KEY_VAL_AUTHORIZATION_HEADER_STR,
    KEY_VAL_BASE_URL_ENV_STR,
    KEY_VAL_DEFAULT_BASE_URL_STR,
    KEY_VAL_GET_PATH_STR,
    KEY_VAL_HTTP_GET_METHOD_STR,
    KEY_VAL_HTTP_POST_METHOD_STR,
    KEY_VAL_HTTP_PUT_METHOD_STR,
    KEY_VAL_JSON_CONTENT_TYPE_STR,
    KEY_VAL_NAMESPACE_ENV_STR,
    KEY_VAL_PUBLIC_CHUNK_MARKER_PREFIX_STR,
    KEY_VAL_PUBLIC_BASE_URL_STR,
    KEY_VAL_PUBLIC_VALUE_CHUNK_SIZE_INT,
    KEY_VAL_PUBLIC_VALUE_MAX_LENGTH_INT,
    KEY_VAL_SET_PATH_STR,
    KEY_VAL_TEXT_CONTENT_TYPE_STR,
    LOGGER_FORMAT_STR,
    LOGGER_LEVEL_ENV_STR,
    PACKAGE_USER_AGENT_STR,
)
from core.helper.key_val_key_hash_helper import hashKeyValKey
from core.helper.logger_config_helper import configureLoggerFromEnv


logger = logging.getLogger(CORE_LOGGER_NAME_STR)


class KeyValStoreProxyError(Exception):
    pass


class KeyValStoreProxy:
    def __init__(
        self,
        baseUrlStr: str | None = None,
        authTokenStr: str | None = None,
        namespaceStr: str | None = None,
        timeoutSecondInt: int = DEFAULT_TIMEOUT_SECOND_INT,
    ) -> None:
        configureLoggerFromEnv(
            CORE_LOGGER_NAME_STR,
            LOGGER_LEVEL_ENV_STR,
            LOGGER_FORMAT_STR,
        )
        self.baseUrlStr = (
            os.getenv(KEY_VAL_BASE_URL_ENV_STR, KEY_VAL_DEFAULT_BASE_URL_STR)
            if baseUrlStr is None
            else baseUrlStr
        )
        self.authTokenStr = (
            os.getenv(KEY_VAL_AUTH_TOKEN_ENV_STR) if authTokenStr is None else authTokenStr
        )
        self.namespaceStr = (
            os.getenv(KEY_VAL_NAMESPACE_ENV_STR, "")
            if namespaceStr is None
            else namespaceStr
        )
        self.timeoutSecondInt = timeoutSecondInt
        logger.debug(
            "Keyval proxy initialized baseUrlConfigured=%s safeBaseUrl=%s publicUrlMode=%s namespaceConfigured=%s tokenConfigured=%s timeoutSecond=%s",
            bool(self.baseUrlStr),
            self.getSafeBaseUrlForLog(),
            self.isPublicKeyValUrlMode(),
            self.hasNamespace(),
            bool(self.authTokenStr),
            self.timeoutSecondInt,
        )

    def getValue(self, keyStr: str) -> str | None:
        if not self.baseUrlStr:
            logger.debug(
                "Keyval read skipped key=%s reason=KEY_VAL_BASE_URL_not_configured",
                keyStr,
            )
            return None

        if self.isPublicKeyValUrlMode() and not self.hasNamespace():
            logger.debug(
                "Keyval read skipped key=%s reason=USER_AGENT_POOL_NAMESPACE_not_configured",
                keyStr,
            )
            return None

        logger.debug(
            "Keyval read start key=%s hashedKey=%s getUrl=%s",
            keyStr,
            self.hashKey(keyStr),
            self.buildSafeGetUrlForLog(keyStr),
        )
        requestObject = Request(
            self.buildGetUrl(keyStr),
            method=KEY_VAL_HTTP_GET_METHOD_STR,
            headers=self.buildHeaderDict(),
        )

        try:
            with urlopen(requestObject, timeout=self.timeoutSecondInt) as responseObject:
                valueStr = responseObject.read().decode("utf-8")
        except HTTPError as exc:
            if exc.code == 404:
                logger.debug("Keyval read miss key=%s statusCode=404", keyStr)
                return None
            logger.debug("Keyval read failed key=%s statusCode=%s", keyStr, exc.code)
            raise KeyValStoreProxyError("Unable to read Keyval value.") from exc
        except (URLError, TimeoutError, OSError, UnicodeDecodeError) as exc:
            logger.debug(
                "Keyval read failed key=%s errorType=%s",
                keyStr,
                type(exc).__name__,
            )
            raise KeyValStoreProxyError("Unable to read Keyval value.") from exc

        if self.isPublicKeyValUrlMode():
            try:
                valueObject = json.loads(valueStr)
            except json.JSONDecodeError as exc:
                raise KeyValStoreProxyError("KeyVal public response is invalid JSON.") from exc

            if valueObject.get("status") != "SUCCESS":
                logger.debug(
                    "Keyval read miss key=%s status=%s getUrl=%s",
                    keyStr,
                    valueObject.get("status"),
                    self.buildSafeGetUrlForLog(keyStr),
                )
                return None
            valueStr = str(valueObject.get("val", ""))

        logger.debug(
            "Keyval read success key=%s byteCount=%s",
            keyStr,
            len(valueStr.encode("utf-8")),
        )
        return valueStr

    def setValue(self, keyStr: str, valueStr: str) -> bool:
        if not self.baseUrlStr:
            logger.debug(
                "Keyval write skipped key=%s reason=KEY_VAL_BASE_URL_not_configured",
                keyStr,
            )
            return False

        if self.isPublicKeyValUrlMode() and not self.hasNamespace():
            logger.debug(
                "Keyval write skipped key=%s reason=USER_AGENT_POOL_NAMESPACE_not_configured",
                keyStr,
            )
            return False

        if self.isPublicKeyValUrlMode() and len(valueStr) > KEY_VAL_PUBLIC_VALUE_MAX_LENGTH_INT:
            logger.debug(
                "Keyval public write skipped key=%s getUrl=%s reason=value_too_large charCount=%s maxCharCount=%s",
                keyStr,
                self.buildSafeGetUrlForLog(keyStr),
                len(valueStr),
                KEY_VAL_PUBLIC_VALUE_MAX_LENGTH_INT,
            )
            return False

        logger.debug(
            "Keyval write start key=%s hashedKey=%s getUrl=%s setUrl=%s byteCount=%s",
            keyStr,
            self.hashKey(keyStr),
            self.buildSafeGetUrlForLog(keyStr),
            self.buildSafeSetUrlForLog(keyStr),
            len(valueStr.encode("utf-8")),
        )

        if self.isPublicKeyValUrlMode():
            requestObject = Request(
                self.buildPublicSetApiUrl(),
                data=json.dumps(
                    {"key": self.hashKey(keyStr), "val": valueStr},
                    separators=(",", ":"),
                ).encode("utf-8"),
                method=KEY_VAL_HTTP_POST_METHOD_STR,
                headers=self.buildHeaderDict(KEY_VAL_JSON_CONTENT_TYPE_STR),
            )
        else:
            requestObject = Request(
                self.buildSetUrl(keyStr, valueStr),
                data=valueStr.encode("utf-8"),
                method=KEY_VAL_HTTP_PUT_METHOD_STR,
                headers=self.buildHeaderDict(KEY_VAL_TEXT_CONTENT_TYPE_STR),
            )

        try:
            with urlopen(requestObject, timeout=self.timeoutSecondInt) as responseObject:
                if self.isPublicKeyValUrlMode():
                    valueObject = json.loads(responseObject.read().decode("utf-8"))
                    if valueObject.get("status") != "SUCCESS":
                        logger.debug(
                            "Keyval write rejected key=%s status=%s getUrl=%s",
                            keyStr,
                            valueObject.get("status"),
                            self.buildSafeGetUrlForLog(keyStr),
                        )
                        return False
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            logger.debug(
                "Keyval write failed key=%s errorType=%s",
                keyStr,
                type(exc).__name__,
            )
            raise KeyValStoreProxyError("Unable to write Keyval value.") from exc

        logger.debug(
            "Keyval write success key=%s getUrl=%s",
            keyStr,
            self.buildSafeGetUrlForLog(keyStr),
        )
        return True

    def getLargeValue(self, keyStr: str) -> str | None:
        valueStr = self.getValue(keyStr)
        if not self.isPublicKeyValUrlMode() or valueStr is None:
            return valueStr

        if not valueStr.startswith(KEY_VAL_PUBLIC_CHUNK_MARKER_PREFIX_STR):
            return valueStr

        countStr = valueStr[len(KEY_VAL_PUBLIC_CHUNK_MARKER_PREFIX_STR):]
        if not countStr.isdigit():
            logger.debug("Keyval chunk marker invalid key=%s marker=%s", keyStr, valueStr)
            return None

        chunkCountInt = int(countStr)
        chunkList: list[str] = []
        for chunkIndexInt in range(chunkCountInt):
            chunkValueStr = self.getValue(self.buildChunkKey(keyStr, chunkIndexInt))
            if chunkValueStr is None:
                logger.debug(
                    "Keyval chunk missing key=%s chunkIndex=%s",
                    keyStr,
                    chunkIndexInt,
                )
                return None
            chunkList.append(chunkValueStr)

        logger.debug(
            "Keyval large value reconstructed key=%s baseGetUrl=%s chunkGetUrlList=%s chunkCount=%s charCount=%s",
            keyStr,
            self.buildSafeGetUrlForLog(keyStr),
            self.buildSafeChunkGetUrlListForLog(keyStr, chunkCountInt),
            chunkCountInt,
            sum(len(chunkStr) for chunkStr in chunkList),
        )
        return "".join(chunkList)

    def setLargeValue(self, keyStr: str, valueStr: str) -> bool:
        if not self.isPublicKeyValUrlMode() or len(valueStr) <= KEY_VAL_PUBLIC_VALUE_MAX_LENGTH_INT:
            return self.setValue(keyStr, valueStr)

        chunkList = [
            valueStr[indexInt:indexInt + KEY_VAL_PUBLIC_VALUE_CHUNK_SIZE_INT]
            for indexInt in range(0, len(valueStr), KEY_VAL_PUBLIC_VALUE_CHUNK_SIZE_INT)
        ]
        chunkSavedBool = True
        for chunkIndexInt, chunkValueStr in enumerate(chunkList):
            chunkSavedBool = (
                self.setValue(self.buildChunkKey(keyStr, chunkIndexInt), chunkValueStr)
                and chunkSavedBool
            )

        markerSavedBool = self.setValue(
            keyStr,
            f"{KEY_VAL_PUBLIC_CHUNK_MARKER_PREFIX_STR}{len(chunkList)}",
        )
        logger.debug(
            "Keyval large value write attempted key=%s baseGetUrl=%s chunkGetUrlList=%s chunkCount=%s saved=%s",
            keyStr,
            self.buildSafeGetUrlForLog(keyStr),
            self.buildSafeChunkGetUrlListForLog(keyStr, len(chunkList)),
            len(chunkList),
            chunkSavedBool and markerSavedBool,
        )
        return chunkSavedBool and markerSavedBool

    def getJson(self, keyStr: str) -> Any:
        valueStr = self.getLargeValue(keyStr)
        if valueStr is None or valueStr == "":
            logger.debug("Keyval JSON read empty key=%s", keyStr)
            return None

        try:
            valueObject = json.loads(valueStr)
        except json.JSONDecodeError as exc:
            logger.debug("Keyval JSON read invalid key=%s", keyStr)
            raise KeyValStoreProxyError("Stored Keyval value is not valid JSON.") from exc

        logger.debug(
            "Keyval JSON read parsed key=%s valueType=%s",
            keyStr,
            type(valueObject).__name__,
        )
        return valueObject

    def setJson(self, keyStr: str, valueObject: Any) -> bool:
        valueStr = json.dumps(valueObject, sort_keys=True, separators=(",", ":"))
        return self.setLargeValue(keyStr, valueStr)

    def buildHeaderDict(self, contentTypeStr: str | None = None) -> dict[str, str]:
        headerDict: dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": PACKAGE_USER_AGENT_STR,
        }

        if contentTypeStr is not None:
            headerDict["Content-Type"] = contentTypeStr

        if self.authTokenStr:
            headerDict[KEY_VAL_AUTHORIZATION_HEADER_STR] = f"Bearer {self.authTokenStr}"

        return headerDict

    def buildKeyUrl(self, keyStr: str) -> str:
        return self.buildGetUrl(keyStr)

    def buildGetUrl(self, keyStr: str) -> str:
        if not self.baseUrlStr:
            raise KeyValStoreProxyError("KEY_VAL_BASE_URL is not configured.")

        hashedKeyStr = self.hashKey(keyStr)
        if self.isPublicKeyValUrlMode():
            return (
                f"{self.baseUrlStr.rstrip('/')}/"
                f"{KEY_VAL_GET_PATH_STR}/{quote(hashedKeyStr)}"
            )

        return f"{self.baseUrlStr.rstrip('/')}/{quote(hashedKeyStr)}"

    def buildSetUrl(self, keyStr: str, valueStr: str) -> str:
        if not self.baseUrlStr:
            raise KeyValStoreProxyError("KEY_VAL_BASE_URL is not configured.")

        hashedKeyStr = self.hashKey(keyStr)
        if self.isPublicKeyValUrlMode():
            return self.buildPublicSetApiUrl()

        return f"{self.baseUrlStr.rstrip('/')}/{quote(hashedKeyStr)}"

    def buildPublicSetApiUrl(self) -> str:
        if not self.baseUrlStr:
            raise KeyValStoreProxyError("KEY_VAL_BASE_URL is not configured.")

        return f"{self.baseUrlStr.rstrip('/')}/{KEY_VAL_SET_PATH_STR}"

    def buildChunkKey(self, keyStr: str, chunkIndexInt: int) -> str:
        return f"{keyStr}_chunk_{chunkIndexInt}"

    def isPublicKeyValUrlMode(self) -> bool:
        if not self.baseUrlStr:
            return False

        return urlsplit(self.baseUrlStr).netloc == urlsplit(KEY_VAL_PUBLIC_BASE_URL_STR).netloc

    def hasNamespace(self) -> bool:
        return isinstance(self.namespaceStr, str) and bool(self.namespaceStr.strip())

    def hashKey(self, keyStr: str) -> str:
        return hashKeyValKey(keyStr, namespaceStr=self.namespaceStr)

    def getSafeBaseUrlForLog(self) -> str | None:
        if not self.baseUrlStr:
            return None

        splitResult = urlsplit(self.baseUrlStr)
        if not splitResult.netloc:
            return self.baseUrlStr

        return f"{splitResult.scheme}://{splitResult.netloc}{splitResult.path}"

    def buildSafeKeyUrlForLog(self, keyStr: str) -> str | None:
        return self.buildSafeGetUrlForLog(keyStr)

    def buildSafeGetUrlForLog(self, keyStr: str) -> str | None:
        safeBaseUrlStr = self.getSafeBaseUrlForLog()
        if safeBaseUrlStr is None:
            return None

        if self.isPublicKeyValUrlMode():
            return (
                f"{safeBaseUrlStr.rstrip('/')}/"
                f"{KEY_VAL_GET_PATH_STR}/{quote(self.hashKey(keyStr))}"
            )

        return f"{safeBaseUrlStr.rstrip('/')}/{quote(self.hashKey(keyStr))}"

    def buildSafeSetUrlForLog(self, keyStr: str) -> str | None:
        safeBaseUrlStr = self.getSafeBaseUrlForLog()
        if safeBaseUrlStr is None:
            return None

        if self.isPublicKeyValUrlMode():
            return f"{safeBaseUrlStr.rstrip('/')}/{KEY_VAL_SET_PATH_STR}"

        return f"{safeBaseUrlStr.rstrip('/')}/{quote(self.hashKey(keyStr))}"

    def buildSafeChunkGetUrlListForLog(
        self,
        keyStr: str,
        chunkCountInt: int,
    ) -> list[str | None]:
        return [
            self.buildSafeGetUrlForLog(self.buildChunkKey(keyStr, chunkIndexInt))
            for chunkIndexInt in range(chunkCountInt)
        ]

    def getPublicValueChunkSize(self) -> int:
        return KEY_VAL_PUBLIC_VALUE_CHUNK_SIZE_INT
