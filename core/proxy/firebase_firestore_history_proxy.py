from __future__ import annotations

import json
import logging
import os
from collections.abc import Mapping
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from core.constant.chrome_user_agent_pool_constant import (
    CORE_LOGGER_NAME_STR,
    DEFAULT_TIMEOUT_SECOND_INT,
    FIREBASE_AUTHORIZATION_HEADER_STR,
    FIREBASE_FIRESTORE_BASE_URL_STR,
    FIREBASE_FIRESTORE_CREDENTIAL_BASE64_ENV_STR,
    FIREBASE_FIRESTORE_PROJECT_ID_ENV_STR,
    FIREBASE_HTTP_POST_METHOD_STR,
    FIREBASE_JSON_CONTENT_TYPE_STR,
    LOGGER_FORMAT_STR,
    LOGGER_LEVEL_ENV_STR,
    PACKAGE_USER_AGENT_STR,
    USER_AGENT_HISTORY_COLLECTION_PATH_STR,
    USER_AGENT_HISTORY_CREATED_AT_UNIX_SECOND_JSON_KEY_STR,
)
from core.helper.base64_json_decode_helper import decodeBase64JsonObject
from core.helper.logger_config_helper import configureLoggerFromEnv


logger = logging.getLogger(CORE_LOGGER_NAME_STR)


class FirebaseFirestoreHistoryProxyError(Exception):
    pass


class FirebaseFirestoreHistoryProxy:
    def __init__(
        self,
        credentialBase64Str: str | None = None,
        projectIdStr: str | None = None,
        collectionPathStr: str = USER_AGENT_HISTORY_COLLECTION_PATH_STR,
        timeoutSecondInt: int = DEFAULT_TIMEOUT_SECOND_INT,
    ) -> None:
        configureLoggerFromEnv(
            CORE_LOGGER_NAME_STR,
            LOGGER_LEVEL_ENV_STR,
            LOGGER_FORMAT_STR,
        )
        self.credentialBase64Str = (
            os.getenv(FIREBASE_FIRESTORE_CREDENTIAL_BASE64_ENV_STR, "")
            if credentialBase64Str is None
            else credentialBase64Str
        )
        self.projectIdStr = (
            os.getenv(FIREBASE_FIRESTORE_PROJECT_ID_ENV_STR, "")
            if projectIdStr is None
            else projectIdStr
        )
        self.collectionPathStr = collectionPathStr
        self.timeoutSecondInt = timeoutSecondInt
        logger.debug(
            "Firebase Firestore history proxy initialized projectConfigured=%s credentialConfigured=%s collectionPath=%s",
            bool(self.projectIdStr),
            bool(self.credentialBase64Str),
            self.collectionPathStr,
        )

    def appendHistoryRecord(self, historyRecordDict: Mapping[str, object]) -> bool:
        if not self.isConfigured():
            logger.debug("Firebase Firestore history append skipped reason=not_configured")
            return False

        requestObject = Request(
            self.buildHistoryDocumentUrl(),
            data=json.dumps(
                self.buildHistoryDocumentPayload(historyRecordDict),
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
                "Firebase Firestore history append failed errorType=%s",
                type(exc).__name__,
            )
            raise FirebaseFirestoreHistoryProxyError(
                "Unable to append Firebase Firestore history record."
            ) from exc

        logger.debug("Firebase Firestore history append succeeded")
        return True

    def isConfigured(self) -> bool:
        return bool(self.projectIdStr.strip()) and bool(self.getAuthToken())

    def buildHistoryDocumentUrl(self) -> str:
        if not self.projectIdStr.strip():
            raise FirebaseFirestoreHistoryProxyError(
                "FIREBASE_FIRESTORE_PROJECT_ID is not configured."
            )

        cleanCollectionPathStr = self.collectionPathStr.strip().strip("/")
        return (
            f"{FIREBASE_FIRESTORE_BASE_URL_STR}/projects/"
            f"{quote(self.projectIdStr.strip(), safe='')}/databases/(default)/documents/"
            f"{quote(cleanCollectionPathStr, safe='/')}"
        )

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

    def buildHistoryDocumentPayload(
        self,
        historyRecordDict: Mapping[str, object],
    ) -> dict[str, object]:
        fieldDict: dict[str, dict[str, str]] = {}
        for keyStr, valueObject in historyRecordDict.items():
            if keyStr == USER_AGENT_HISTORY_CREATED_AT_UNIX_SECOND_JSON_KEY_STR:
                fieldDict[keyStr] = {"integerValue": str(int(valueObject))}
            else:
                fieldDict[keyStr] = {"stringValue": str(valueObject)}

        return {"fields": fieldDict}

    def getCredentialDict(self) -> dict[str, Any]:
        if not self.credentialBase64Str.strip():
            return {}

        return decodeBase64JsonObject(self.credentialBase64Str)

    def getAuthToken(self) -> str | None:
        try:
            credentialDict = self.getCredentialDict()
        except ValueError as exc:
            raise FirebaseFirestoreHistoryProxyError(
                "Firebase Firestore credential is invalid."
            ) from exc

        for keyStr in ("accessToken", "authToken", "idToken", "token"):
            tokenObject = credentialDict.get(keyStr)
            if isinstance(tokenObject, str) and tokenObject.strip():
                return tokenObject.strip()

        return None
