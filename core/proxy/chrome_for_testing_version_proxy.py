from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from core.constant.chrome_user_agent_pool_constant import (
    CHROME_FOR_TESTING_BUILDS_KEY_STR,
    CHROME_FOR_TESTING_CHANNELS_KEY_STR,
    CHROME_FOR_TESTING_LAST_KNOWN_GOOD_VERSION_URL_STR,
    CHROME_FOR_TESTING_LATEST_PATCH_VERSION_URL_STR,
    CHROME_FOR_TESTING_VERSION_KEY_STR,
    CORE_LOGGER_NAME_STR,
    DEFAULT_TIMEOUT_SECOND_INT,
    LOGGER_FORMAT_STR,
    LOGGER_LEVEL_ENV_STR,
    PACKAGE_USER_AGENT_STR,
)
from core.helper.logger_config_helper import configureLoggerFromEnv


logger = logging.getLogger(CORE_LOGGER_NAME_STR)


class ChromeForTestingVersionProxyError(Exception):
    pass


class ChromeForTestingVersionProxy:
    def __init__(
        self,
        latestPatchVersionUrlStr: str = CHROME_FOR_TESTING_LATEST_PATCH_VERSION_URL_STR,
        lastKnownGoodVersionUrlStr: str = CHROME_FOR_TESTING_LAST_KNOWN_GOOD_VERSION_URL_STR,
        timeoutSecondInt: int = DEFAULT_TIMEOUT_SECOND_INT,
    ) -> None:
        configureLoggerFromEnv(
            CORE_LOGGER_NAME_STR,
            LOGGER_LEVEL_ENV_STR,
            LOGGER_FORMAT_STR,
        )
        self.latestPatchVersionUrlStr = latestPatchVersionUrlStr
        self.lastKnownGoodVersionUrlStr = lastKnownGoodVersionUrlStr
        self.timeoutSecondInt = timeoutSecondInt
        logger.debug(
            "Chrome for Testing proxy initialized latestPatchUrl=%s lastKnownGoodUrl=%s timeoutSecond=%s",
            self.latestPatchVersionUrlStr,
            self.lastKnownGoodVersionUrlStr,
            self.timeoutSecondInt,
        )

    def fetchLatestChromeVersionList(self) -> list[str]:
        logger.debug(
            "Chrome for Testing latest patch version fetch requested url=%s",
            self.latestPatchVersionUrlStr,
        )
        payloadDict = self.fetchJsonPayload(self.latestPatchVersionUrlStr)
        versionList = self.extractChromeVersionList(payloadDict)
        logger.debug(
            "Chrome for Testing latest patch version fetch parsed rawVersionCount=%s",
            len(versionList),
        )
        return versionList

    def fetchLatestChannelVersionMap(self) -> dict[str, str]:
        logger.debug(
            "Chrome for Testing channel version fetch requested url=%s",
            self.lastKnownGoodVersionUrlStr,
        )
        payloadDict = self.fetchJsonPayload(self.lastKnownGoodVersionUrlStr)
        channelVersionMap = self.extractChannelVersionMap(payloadDict)
        logger.debug(
            "Chrome for Testing channel version fetch parsed channelVersionMap=%s",
            channelVersionMap,
        )
        return channelVersionMap

    def fetchJsonPayload(self, urlStr: str) -> dict[str, Any]:
        logger.debug("Chrome for Testing JSON request start url=%s", urlStr)
        requestObject = Request(
            urlStr,
            headers={
                "Accept": "application/json",
                "User-Agent": PACKAGE_USER_AGENT_STR,
            },
        )

        try:
            with urlopen(requestObject, timeout=self.timeoutSecondInt) as responseObject:
                rawPayloadByte = responseObject.read()
                logger.debug(
                    "Chrome for Testing JSON request success url=%s byteCount=%s",
                    urlStr,
                    len(rawPayloadByte),
                )
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            logger.debug(
                "Chrome for Testing JSON request failed url=%s errorType=%s",
                urlStr,
                type(exc).__name__,
            )
            raise ChromeForTestingVersionProxyError(
                f"Unable to fetch Chrome for Testing payload from {urlStr}"
            ) from exc

        try:
            payloadObject = json.loads(rawPayloadByte.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.debug(
                "Chrome for Testing JSON parse failed url=%s errorType=%s",
                urlStr,
                type(exc).__name__,
            )
            raise ChromeForTestingVersionProxyError(
                "Chrome for Testing returned invalid JSON."
            ) from exc

        if not isinstance(payloadObject, dict):
            logger.debug(
                "Chrome for Testing JSON payload rejected url=%s payloadType=%s",
                urlStr,
                type(payloadObject).__name__,
            )
            raise ChromeForTestingVersionProxyError(
                "Chrome for Testing payload must be a JSON object."
            )

        logger.debug(
            "Chrome for Testing JSON payload accepted url=%s topLevelKeyList=%s",
            urlStr,
            list(payloadObject.keys()),
        )
        return payloadObject

    def extractChromeVersionList(self, payloadDict: Mapping[str, Any]) -> list[str]:
        buildPayloadObject = payloadDict.get(CHROME_FOR_TESTING_BUILDS_KEY_STR)
        if not isinstance(buildPayloadObject, Mapping):
            raise ChromeForTestingVersionProxyError(
                "Chrome for Testing payload is missing the builds object."
            )

        versionList: list[str] = []
        for buildPayload in buildPayloadObject.values():
            if not isinstance(buildPayload, Mapping):
                continue

            versionObject = buildPayload.get(CHROME_FOR_TESTING_VERSION_KEY_STR)
            if isinstance(versionObject, str):
                versionList.append(versionObject)

        logger.debug(
            "Chrome for Testing build payload extracted versionCount=%s",
            len(versionList),
        )
        return versionList

    def extractChannelVersionMap(self, payloadDict: Mapping[str, Any]) -> dict[str, str]:
        channelPayloadObject = payloadDict.get(CHROME_FOR_TESTING_CHANNELS_KEY_STR)
        if not isinstance(channelPayloadObject, Mapping):
            raise ChromeForTestingVersionProxyError(
                "Chrome for Testing payload is missing the channels object."
            )

        channelVersionMap: dict[str, str] = {}
        for channelStr, channelPayload in channelPayloadObject.items():
            if not isinstance(channelStr, str) or not isinstance(channelPayload, Mapping):
                continue

            versionObject = channelPayload.get(CHROME_FOR_TESTING_VERSION_KEY_STR)
            if isinstance(versionObject, str):
                channelVersionMap[channelStr] = versionObject

        logger.debug(
            "Chrome for Testing channel payload extracted channelCount=%s",
            len(channelVersionMap),
        )
        return channelVersionMap
