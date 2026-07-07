from __future__ import annotations

import json
import logging
import os
from collections.abc import Mapping
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from core.constant.chrome_user_agent_pool_constant import (
    CORE_LOGGER_NAME_STR,
    DEFAULT_TIMEOUT_SECOND_INT,
    FIREBASE_AUTHORIZATION_HEADER_STR,
    FIREBASE_HTTP_POST_METHOD_STR,
    FIREBASE_JSON_CONTENT_TYPE_STR,
    FIREBASE_REALTIME_DATABASE_CREDENTIAL_BASE64_ENV_STR,
    FIREBASE_REALTIME_DATABASE_URL_ENV_STR,
    LOGGER_FORMAT_STR,
    LOGGER_LEVEL_ENV_STR,
    PACKAGE_USER_AGENT_STR,
    USER_AGENT_HISTORY_COLLECTION_PATH_STR,
)
from core.helper.base64_json_decode_helper import decodeBase64JsonObject
from core.helper.logger_config_helper import configureLoggerFromEnv


logger = logging.getLogger(CORE_LOGGER_NAME_STR)


class FirebaseRealtimeDatabaseHistoryProxyError(Exception):
    pass


class FirebaseRealtimeDatabaseHistoryProxy:
    def __init__(
        self,
        credentialBase64Str: str | None = None,
        databaseUrlStr: str | None = None,
        historyPathStr: str = USER_AGENT_HISTORY_COLLECTION_PATH_STR,
        timeoutSecondInt: int = DEFAULT_TIMEOUT_SECOND_INT,
    ) -> None:
        configureLoggerFromEnv(
            CORE_LOGGER_NAME_STR,
            LOGGER_LEVEL_ENV_STR,
            LOGGER_FORMAT_STR,
        )
        self.credentialBase64Str = (
            os.getenv(FIREBASE_REALTIME_DATABASE_CREDENTIAL_BASE64_ENV_STR, "")
            if credentialBase64Str is None
            else credentialBase64Str
        )
        self.databaseUrlStr = (
            os.getenv(FIREBASE_REALTIME_DATABASE_URL_ENV_STR, "")
            if databaseUrlStr is None
            else databaseUrlStr
        )
        self.historyPathStr = historyPathStr
        self.timeoutSecondInt = timeoutSecondInt
        logger.debug(
            "Firebase Realtime Database history proxy initialized databaseUrlConfigured=%s credentialConfigured=%s historyPath=%s",
            bool(self.databaseUrlStr),
            bool(self.credentialBase64Str),
            self.historyPathStr,
        )

    def appendHistoryRecord(self, historyRecordDict: Mapping[str, object]) -> bool:
        if not self.isConfigured():
            logger.debug("Firebase Realtime Database history append skipped reason=not_configured")
            return False

        requestObject = Request(
            self.buildHistoryUrl(),
            data=json.dumps(
                self.buildHistoryPayload(historyRecordDict),
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8"),
            method=FIREBASE_HTTP_POST_METHOD_STR,
            headers=self.buildHeaderDict(),
        )

        try:
            with urlopen(requestObject, timeout=self.timeoutSecondInt) as responseObject:
                responseObject.read()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            logger.debug(
                "Firebase Realtime Database history append failed errorType=%s",
                type(exc).__name__,
            )
            raise FirebaseRealtimeDatabaseHistoryProxyError(
                "Unable to append Firebase Realtime Database history record."
            ) from exc

        logger.debug("Firebase Realtime Database history append succeeded")
        return True

    def isConfigured(self) -> bool:
        return bool(self.databaseUrlStr.strip()) and bool(self.getAuthToken())

    def buildHistoryUrl(self) -> str:
        if not self.databaseUrlStr.strip():
            raise FirebaseRealtimeDatabaseHistoryProxyError(
                "FIREBASE_REALTIME_DATABASE_URL is not configured."
            )

        cleanPathStr = self.historyPathStr.strip().strip("/")
        return f"{self.databaseUrlStr.rstrip('/')}/{cleanPathStr}.json"

    def buildHeaderDict(self) -> dict[str, str]:
        headerDict = {
            "Accept": FIREBASE_JSON_CONTENT_TYPE_STR,
            "Content-Type": FIREBASE_JSON_CONTENT_TYPE_STR,
            "User-Agent": PACKAGE_USER_AGENT_STR,
        }
        authTokenStr = self.getAuthToken()
        if authTokenStr:
            headerDict[FIREBASE_AUTHORIZATION_HEADER_STR] = f"Bearer {authTokenStr}"

        return headerDict

    def buildHistoryPayload(
        self,
        historyRecordDict: Mapping[str, object],
    ) -> dict[str, object]:
        return dict(historyRecordDict)

    def getCredentialDict(self) -> dict[str, Any]:
        if not self.credentialBase64Str.strip():
            return {}

        return decodeBase64JsonObject(self.credentialBase64Str)

    def getAuthToken(self) -> str | None:
        try:
            credentialDict = self.getCredentialDict()
        except ValueError as exc:
            raise FirebaseRealtimeDatabaseHistoryProxyError(
                "Firebase Realtime Database credential is invalid."
            ) from exc

        for keyStr in ("accessToken", "authToken", "idToken", "token"):
            tokenObject = credentialDict.get(keyStr)
            if isinstance(tokenObject, str) and tokenObject.strip():
                return tokenObject.strip()

        return None
