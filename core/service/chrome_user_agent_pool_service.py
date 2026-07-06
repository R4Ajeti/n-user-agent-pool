from __future__ import annotations

import secrets
from collections import defaultdict
from collections.abc import Sequence
from typing import Any

from core.constant.chrome_user_agent_pool_constant import (
    CHANNEL_VERSION_MAP_JSON_KEY_STR,
    CHROME_RELEASE_CHANNEL_LIST,
    DEFAULT_CHROME_RELEASE_CHANNEL_STR,
    KEY_VAL_CHANNEL_VERSION_MAP_KEY_STR,
    KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR,
    KEY_VAL_USER_AGENT_LIST_KEY_STR,
    MAX_CHROME_VERSION_COUNT_INT,
    SUPPORTED_DESKTOP_PLATFORM_FRAGMENT_BY_FAMILY_DICT,
    SUPPORTED_DESKTOP_PLATFORM_FRAGMENT_LIST,
    USER_AGENT_JSON_KEY_STR,
    USER_AGENT_LIST_JSON_KEY_STR,
)
from core.helper.dotted_version_format_helper import (
    isValidDottedVersion,
    sortDottedVersionList,
)
from core.helper.user_agent_format_helper import (
    buildChromeUserAgent,
    extractChromeVersionFromUserAgent,
    getDesktopPlatformFamily,
    isValidChromeUserAgent,
)
from core.proxy.chrome_for_testing_version_proxy import (
    ChromeForTestingVersionProxy,
    ChromeForTestingVersionProxyError,
)
from core.proxy.key_val_store_proxy import KeyValStoreProxy, KeyValStoreProxyError
from core.repo.chrome_user_agent_pool_repo import ChromeUserAgentPoolRepo
from core.service.chrome_user_agent_pool_error import (
    ChromeUserAgentPoolUnavailableError,
    ChromeVersionPayloadError,
)


class ChromeUserAgentPoolService:
    def __init__(
        self,
        chromeForTestingVersionProxy: ChromeForTestingVersionProxy | None = None,
        keyValStoreProxy: KeyValStoreProxy | None = None,
        chromeUserAgentPoolRepo: ChromeUserAgentPoolRepo | None = None,
        randomGenerator: Any | None = None,
    ) -> None:
        self.chromeForTestingVersionProxy = (
            chromeForTestingVersionProxy or ChromeForTestingVersionProxy()
        )
        self.keyValStoreProxy = keyValStoreProxy or KeyValStoreProxy()
        self.chromeUserAgentPoolRepo = chromeUserAgentPoolRepo or ChromeUserAgentPoolRepo()
        self.randomGenerator = randomGenerator or secrets.SystemRandom()

    def latest(self, count: int | None = None) -> str | list[str]:
        userAgentList = self.getFreshOrCachedUserAgents()
        return self.sliceUserAgentResult(userAgentList, count)

    def random(self, channelStr: str | None = None) -> str:
        if channelStr is None:
            userAgentList = self.getFreshOrCachedUserAgents()
        else:
            userAgentList = self.getLatestByChannelUserAgentList(channelStr)

        if not userAgentList:
            raise ChromeUserAgentPoolUnavailableError(
                "No valid Chrome user-agent strings are available."
            )

        lastRandomUserAgentStr = self.getLastRandomUserAgent()
        candidateUserAgentList = list(userAgentList)
        if len(candidateUserAgentList) > 1 and lastRandomUserAgentStr in candidateUserAgentList:
            candidateUserAgentList = [
                userAgentStr
                for userAgentStr in candidateUserAgentList
                if userAgentStr != lastRandomUserAgentStr
            ]

        selectedUserAgentStr = self.chooseRandomUserAgent(candidateUserAgentList)
        self.saveLastRandomUserAgent(selectedUserAgentStr)
        return selectedUserAgentStr

    def latestByChannel(
        self,
        channelStr: str = DEFAULT_CHROME_RELEASE_CHANNEL_STR,
        count: int | None = None,
    ) -> str | list[str]:
        userAgentList = self.getLatestByChannelUserAgentList(channelStr)
        return self.sliceUserAgentResult(userAgentList, count)

    def latestVersion(self, channelStr: str | None = None) -> str:
        if channelStr is not None:
            cleanChannelStr = self.normalizeChannel(channelStr)
            channelVersionMap = self.channelVersionMap()
            versionStr = channelVersionMap.get(cleanChannelStr)
            if not versionStr:
                raise ChromeUserAgentPoolUnavailableError(
                    f"No Chrome version is available for channel {cleanChannelStr}."
                )
            return versionStr

        try:
            versionList = self.fetchLatestChromeVersions()
            if versionList:
                return versionList[0]
        except (ChromeForTestingVersionProxyError, ChromeVersionPayloadError):
            cachedUserAgentList = self.getCachedUserAgents()
            for userAgentStr in cachedUserAgentList:
                versionStr = extractChromeVersionFromUserAgent(userAgentStr)
                if versionStr is not None:
                    return versionStr

        raise ChromeUserAgentPoolUnavailableError("No valid Chrome versions are available.")

    def channelVersionMap(self) -> dict[str, str]:
        try:
            channelVersionMap = self.fetchLatestChannelVersionMap()
            self.saveChannelVersionMap(channelVersionMap)
            return channelVersionMap
        except (ChromeForTestingVersionProxyError, ChromeVersionPayloadError):
            cachedChannelVersionMap = self.getCachedChannelVersionMap()
            if cachedChannelVersionMap:
                return cachedChannelVersionMap
            raise ChromeUserAgentPoolUnavailableError(
                "Chrome channel versions are unavailable and no cached values exist."
            )

    def supportedPlatformList(self) -> dict[str, list[str]]:
        return {
            familyStr: list(platformFragmentList)
            for familyStr, platformFragmentList
            in SUPPORTED_DESKTOP_PLATFORM_FRAGMENT_BY_FAMILY_DICT.items()
        }

    def fetchLatestChromeVersions(self) -> list[str]:
        versionList = self.chromeForTestingVersionProxy.fetchLatestChromeVersionList()
        cleanVersionList = sortDottedVersionList(versionList)
        if not cleanVersionList:
            raise ChromeVersionPayloadError("Chrome for Testing returned no valid versions.")

        return cleanVersionList[:MAX_CHROME_VERSION_COUNT_INT]

    def fetchLatestChannelVersionMap(self) -> dict[str, str]:
        rawChannelVersionMap = self.chromeForTestingVersionProxy.fetchLatestChannelVersionMap()
        cleanChannelVersionMap: dict[str, str] = {}

        for channelStr in CHROME_RELEASE_CHANNEL_LIST:
            versionStr = rawChannelVersionMap.get(channelStr)
            if isValidDottedVersion(versionStr):
                cleanChannelVersionMap[channelStr] = versionStr

        if not cleanChannelVersionMap:
            raise ChromeVersionPayloadError("Chrome for Testing returned no valid channels.")

        return cleanChannelVersionMap

    def generateUserAgents(
        self,
        chromeVersionList: Sequence[str],
        platformFragmentList: Sequence[str] | None = None,
    ) -> list[str]:
        cleanVersionList = sortDottedVersionList(chromeVersionList)
        selectedPlatformFragmentList = (
            list(platformFragmentList)
            if platformFragmentList is not None
            else SUPPORTED_DESKTOP_PLATFORM_FRAGMENT_LIST
        )

        userAgentList: list[str] = []
        seenUserAgentSet: set[str] = set()

        for chromeVersionStr in cleanVersionList:
            for platformFragmentStr in selectedPlatformFragmentList:
                try:
                    userAgentStr = buildChromeUserAgent(
                        chromeVersionStr,
                        platformFragmentStr,
                    )
                except ValueError:
                    continue

                if userAgentStr in seenUserAgentSet:
                    continue

                if not isValidChromeUserAgent(userAgentStr):
                    continue

                seenUserAgentSet.add(userAgentStr)
                userAgentList.append(userAgentStr)

        return userAgentList

    def getFreshOrCachedUserAgents(self) -> list[str]:
        try:
            chromeVersionList = self.fetchLatestChromeVersions()
            userAgentList = self.generateUserAgents(chromeVersionList)
            if not userAgentList:
                raise ChromeVersionPayloadError("No valid Chrome user agents were generated.")
            self.saveUserAgents(userAgentList)
            return userAgentList
        except (ChromeForTestingVersionProxyError, ChromeVersionPayloadError):
            cachedUserAgentList = self.getCachedUserAgents()
            if cachedUserAgentList:
                return cachedUserAgentList

            raise ChromeUserAgentPoolUnavailableError(
                "Chrome versions are unavailable and no cached user-agent pool exists."
            )

    def getLatestByChannelUserAgentList(self, channelStr: str) -> list[str]:
        cleanChannelStr = self.normalizeChannel(channelStr)
        channelVersionMap = self.channelVersionMap()
        versionStr = channelVersionMap.get(cleanChannelStr)
        if not versionStr:
            raise ChromeUserAgentPoolUnavailableError(
                f"No Chrome version is available for channel {cleanChannelStr}."
            )

        userAgentList = self.generateUserAgents([versionStr])
        if not userAgentList:
            raise ChromeUserAgentPoolUnavailableError(
                f"No valid user agents were generated for channel {cleanChannelStr}."
            )
        return userAgentList

    def getCachedUserAgents(self) -> list[str]:
        keyValUserAgentList = self.readUserAgentListFromKeyVal()
        if keyValUserAgentList:
            self.chromeUserAgentPoolRepo.saveUserAgentList(keyValUserAgentList)
            return keyValUserAgentList

        repoUserAgentList = self.chromeUserAgentPoolRepo.getUserAgentList()
        return [
            userAgentStr
            for userAgentStr in repoUserAgentList
            if isValidChromeUserAgent(userAgentStr)
        ]

    def saveUserAgents(self, userAgentList: list[str]) -> None:
        cleanUserAgentList = [
            userAgentStr
            for userAgentStr in userAgentList
            if isValidChromeUserAgent(userAgentStr)
        ]
        self.chromeUserAgentPoolRepo.saveUserAgentList(cleanUserAgentList)

        self.safeSetKeyValJson(
            KEY_VAL_USER_AGENT_LIST_KEY_STR,
            {USER_AGENT_LIST_JSON_KEY_STR: cleanUserAgentList},
        )

    def getLastRandomUserAgent(self) -> str | None:
        keyValLastRandomUserAgentStr = self.readLastRandomUserAgentFromKeyVal()
        if keyValLastRandomUserAgentStr:
            self.chromeUserAgentPoolRepo.saveLastRandomUserAgent(
                keyValLastRandomUserAgentStr
            )
            return keyValLastRandomUserAgentStr

        return self.chromeUserAgentPoolRepo.getLastRandomUserAgent()

    def saveLastRandomUserAgent(self, userAgentStr: str) -> None:
        if not isValidChromeUserAgent(userAgentStr):
            raise ValueError("Cannot save an invalid Chrome user-agent string.")

        self.chromeUserAgentPoolRepo.saveLastRandomUserAgent(userAgentStr)
        self.safeSetKeyValJson(
            KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR,
            {USER_AGENT_JSON_KEY_STR: userAgentStr},
        )

    def getCachedChannelVersionMap(self) -> dict[str, str]:
        keyValChannelVersionMap = self.readChannelVersionMapFromKeyVal()
        if keyValChannelVersionMap:
            self.chromeUserAgentPoolRepo.saveChannelVersionMap(keyValChannelVersionMap)
            return keyValChannelVersionMap

        repoChannelVersionMap = self.chromeUserAgentPoolRepo.getChannelVersionMap()
        return {
            channelStr: versionStr
            for channelStr, versionStr in repoChannelVersionMap.items()
            if channelStr in CHROME_RELEASE_CHANNEL_LIST and isValidDottedVersion(versionStr)
        }

    def saveChannelVersionMap(self, channelVersionMap: dict[str, str]) -> None:
        cleanChannelVersionMap = {
            channelStr: versionStr
            for channelStr, versionStr in channelVersionMap.items()
            if channelStr in CHROME_RELEASE_CHANNEL_LIST and isValidDottedVersion(versionStr)
        }
        self.chromeUserAgentPoolRepo.saveChannelVersionMap(cleanChannelVersionMap)

        self.safeSetKeyValJson(
            KEY_VAL_CHANNEL_VERSION_MAP_KEY_STR,
            {CHANNEL_VERSION_MAP_JSON_KEY_STR: cleanChannelVersionMap},
        )

    def readUserAgentListFromKeyVal(self) -> list[str]:
        valueObject = self.safeGetKeyValJson(KEY_VAL_USER_AGENT_LIST_KEY_STR)
        if isinstance(valueObject, dict):
            candidateObject = valueObject.get(USER_AGENT_LIST_JSON_KEY_STR)
        else:
            candidateObject = valueObject

        if not isinstance(candidateObject, list):
            return []

        return [
            userAgentStr
            for userAgentStr in candidateObject
            if isValidChromeUserAgent(userAgentStr)
        ]

    def readLastRandomUserAgentFromKeyVal(self) -> str | None:
        valueObject = self.safeGetKeyValJson(KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR)
        if isinstance(valueObject, dict):
            candidateObject = valueObject.get(USER_AGENT_JSON_KEY_STR)
        else:
            candidateObject = valueObject

        if isinstance(candidateObject, str) and isValidChromeUserAgent(candidateObject):
            return candidateObject

        return None

    def readChannelVersionMapFromKeyVal(self) -> dict[str, str]:
        valueObject = self.safeGetKeyValJson(KEY_VAL_CHANNEL_VERSION_MAP_KEY_STR)
        if isinstance(valueObject, dict) and CHANNEL_VERSION_MAP_JSON_KEY_STR in valueObject:
            candidateObject = valueObject.get(CHANNEL_VERSION_MAP_JSON_KEY_STR)
        else:
            candidateObject = valueObject

        if not isinstance(candidateObject, dict):
            return {}

        return {
            channelStr: versionStr
            for channelStr, versionStr in candidateObject.items()
            if channelStr in CHROME_RELEASE_CHANNEL_LIST and isValidDottedVersion(versionStr)
        }

    def safeGetKeyValJson(self, keyStr: str) -> Any:
        try:
            return self.keyValStoreProxy.getJson(keyStr)
        except (KeyValStoreProxyError, AttributeError):
            return None

    def safeSetKeyValJson(self, keyStr: str, valueObject: Any) -> bool:
        try:
            return bool(self.keyValStoreProxy.setJson(keyStr, valueObject))
        except (KeyValStoreProxyError, AttributeError):
            return False

    def chooseRandomUserAgent(self, userAgentList: Sequence[str]) -> str:
        if not userAgentList:
            raise ChromeUserAgentPoolUnavailableError(
                "No valid Chrome user-agent strings are available."
            )

        familyUserAgentMap: dict[str, list[str]] = defaultdict(list)
        for userAgentStr in userAgentList:
            familyStr = getDesktopPlatformFamily(userAgentStr)
            familyUserAgentMap[familyStr].append(userAgentStr)

        preferredFamilyList = [
            familyStr
            for familyStr in SUPPORTED_DESKTOP_PLATFORM_FRAGMENT_BY_FAMILY_DICT
            if familyStr in familyUserAgentMap
        ]
        familyList = preferredFamilyList or list(familyUserAgentMap.keys())
        selectedFamilyStr = self.randomGenerator.choice(familyList)
        return self.randomGenerator.choice(familyUserAgentMap[selectedFamilyStr])

    def sliceUserAgentResult(
        self,
        userAgentList: Sequence[str],
        count: int | None,
    ) -> str | list[str]:
        if not userAgentList:
            raise ChromeUserAgentPoolUnavailableError(
                "No valid Chrome user-agent strings are available."
            )

        if count is None:
            return userAgentList[0]

        if not isinstance(count, int):
            raise ValueError("count must be an integer.")

        if count <= 0:
            return []

        return list(userAgentList[:count])

    def normalizeChannel(self, channelStr: str) -> str:
        if not isinstance(channelStr, str) or not channelStr.strip():
            raise ValueError("Chrome release channel must be a non-empty string.")

        cleanChannelStr = channelStr.strip().lower()
        for supportedChannelStr in CHROME_RELEASE_CHANNEL_LIST:
            if cleanChannelStr == supportedChannelStr.lower():
                return supportedChannelStr

        raise ValueError(
            "Unsupported Chrome release channel. "
            f"Use one of: {', '.join(CHROME_RELEASE_CHANNEL_LIST)}."
        )
