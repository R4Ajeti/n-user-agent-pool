from __future__ import annotations

import json
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
    DEFAULT_TIMEOUT_SECOND_INT,
    PACKAGE_USER_AGENT_STR,
)


class ChromeForTestingVersionProxyError(Exception):
    pass


class ChromeForTestingVersionProxy:
    def __init__(
        self,
        latestPatchVersionUrlStr: str = CHROME_FOR_TESTING_LATEST_PATCH_VERSION_URL_STR,
        lastKnownGoodVersionUrlStr: str = CHROME_FOR_TESTING_LAST_KNOWN_GOOD_VERSION_URL_STR,
        timeoutSecondInt: int = DEFAULT_TIMEOUT_SECOND_INT,
    ) -> None:
        self.latestPatchVersionUrlStr = latestPatchVersionUrlStr
        self.lastKnownGoodVersionUrlStr = lastKnownGoodVersionUrlStr
        self.timeoutSecondInt = timeoutSecondInt

    def fetchLatestChromeVersionList(self) -> list[str]:
        payloadDict = self.fetchJsonPayload(self.latestPatchVersionUrlStr)
        return self.extractChromeVersionList(payloadDict)

    def fetchLatestChannelVersionMap(self) -> dict[str, str]:
        payloadDict = self.fetchJsonPayload(self.lastKnownGoodVersionUrlStr)
        return self.extractChannelVersionMap(payloadDict)

    def fetchJsonPayload(self, urlStr: str) -> dict[str, Any]:
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
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise ChromeForTestingVersionProxyError(
                f"Unable to fetch Chrome for Testing payload from {urlStr}"
            ) from exc

        try:
            payloadObject = json.loads(rawPayloadByte.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ChromeForTestingVersionProxyError(
                "Chrome for Testing returned invalid JSON."
            ) from exc

        if not isinstance(payloadObject, dict):
            raise ChromeForTestingVersionProxyError(
                "Chrome for Testing payload must be a JSON object."
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

        return channelVersionMap
