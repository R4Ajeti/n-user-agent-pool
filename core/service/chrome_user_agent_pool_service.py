from __future__ import annotations

import logging
import secrets
import time
from collections import defaultdict
from collections.abc import Callable, Sequence
from typing import Any, TypeVar

from core.constant.chrome_user_agent_pool_constant import (
    CHANNEL_VERSION_MAP_JSON_KEY_STR,
    CHROME_RELEASE_CHANNEL_LIST,
    CORE_LOGGER_NAME_STR,
    DEFAULT_CHROME_RELEASE_CHANNEL_STR,
    KEY_VAL_CHANNEL_VERSION_MAP_KEY_STR,
    KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR,
    KEY_VAL_USER_AGENT_LIST_KEY_STR,
    LOGGER_FORMAT_STR,
    LOGGER_LEVEL_ENV_STR,
    MAX_CHROME_VERSION_COUNT_INT,
    SUPPORTED_DESKTOP_PLATFORM_FRAGMENT_BY_FAMILY_DICT,
    SUPPORTED_DESKTOP_PLATFORM_FRAGMENT_LIST,
    TIMING_DURATION_MILLISECOND_JSON_KEY_STR,
    TIMING_DURATION_SECOND_JSON_KEY_STR,
    TIMING_ERROR_TYPE_JSON_KEY_STR,
    TIMING_FINISHED_AT_UNIX_SECOND_JSON_KEY_STR,
    TIMING_OPERATION_JSON_KEY_STR,
    TIMING_RESULT_JSON_KEY_STR,
    TIMING_SUCCESS_BOOL_JSON_KEY_STR,
    TIMING_TIMING_JSON_KEY_STR,
    USER_AGENT_JSON_KEY_STR,
    USER_AGENT_LIST_JSON_KEY_STR,
)
from core.helper.dotted_version_format_helper import (
    isValidDottedVersion,
    sortDottedVersionList,
)
from core.helper.logger_config_helper import configureLoggerFromEnv
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


ResultType = TypeVar("ResultType")
logger = logging.getLogger(CORE_LOGGER_NAME_STR)


class ChromeUserAgentPoolService:
    def __init__(
        self,
        chromeForTestingVersionProxy: ChromeForTestingVersionProxy | None = None,
        keyValStoreProxy: KeyValStoreProxy | None = None,
        chromeUserAgentPoolRepo: ChromeUserAgentPoolRepo | None = None,
        randomGenerator: Any | None = None,
    ) -> None:
        configureLoggerFromEnv(
            CORE_LOGGER_NAME_STR,
            LOGGER_LEVEL_ENV_STR,
            LOGGER_FORMAT_STR,
        )
        self.chromeForTestingVersionProxy = (
            chromeForTestingVersionProxy or ChromeForTestingVersionProxy()
        )
        self.keyValStoreProxy = keyValStoreProxy or KeyValStoreProxy()
        self.chromeUserAgentPoolRepo = chromeUserAgentPoolRepo or ChromeUserAgentPoolRepo()
        self.randomGenerator = randomGenerator or secrets.SystemRandom()
        logger.debug(
            "Chrome user-agent pool service initialized randomGenerator=%s",
            type(self.randomGenerator).__name__,
        )

    def latest(self, count: int | None = None) -> str | list[str]:
        return self.runTimedOperation("latest", lambda: self._latest(count))

    def _latest(self, count: int | None = None) -> str | list[str]:
        logger.debug("Latest user-agent requested count=%s", count)
        userAgentList = self.getFreshOrCachedUserAgents()
        resultObject = self.sliceUserAgentResult(userAgentList, count)
        logger.debug(
            "Latest user-agent resolved count=%s poolSize=%s resultType=%s",
            count,
            len(userAgentList),
            type(resultObject).__name__,
        )
        return resultObject

    def random(self, channelStr: str | None = None) -> str:
        return self.runTimedOperation("random", lambda: self._random(channelStr))

    def _random(self, channelStr: str | None = None) -> str:
        logger.debug("Random user-agent requested channel=%s", channelStr)
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
        previousExcludedBool = False
        if len(candidateUserAgentList) > 1 and lastRandomUserAgentStr in candidateUserAgentList:
            candidateUserAgentList = [
                userAgentStr
                for userAgentStr in candidateUserAgentList
                if userAgentStr != lastRandomUserAgentStr
            ]
            previousExcludedBool = True

        logger.debug(
            "Random user-agent candidate pool prepared originalPoolSize=%s candidatePoolSize=%s hadLastRandom=%s previousExcluded=%s",
            len(userAgentList),
            len(candidateUserAgentList),
            lastRandomUserAgentStr is not None,
            previousExcludedBool,
        )

        selectedUserAgentStr = self.chooseRandomUserAgent(candidateUserAgentList)
        self.saveLastRandomUserAgent(selectedUserAgentStr)
        logger.debug(
            "Random user-agent selected chromeVersion=%s platformFamily=%s",
            extractChromeVersionFromUserAgent(selectedUserAgentStr),
            getDesktopPlatformFamily(selectedUserAgentStr),
        )
        return selectedUserAgentStr

    def latestWithTiming(self, count: int | None = None) -> dict[str, Any]:
        resultObject = self.latest(count)
        return self.buildResultWithTiming(resultObject)

    def randomWithTiming(self, channelStr: str | None = None) -> dict[str, Any]:
        resultObject = self.random(channelStr)
        return self.buildResultWithTiming(resultObject)

    def latestByChannel(
        self,
        channelStr: str = DEFAULT_CHROME_RELEASE_CHANNEL_STR,
        count: int | None = None,
    ) -> str | list[str]:
        return self.runTimedOperation(
            "latestByChannel",
            lambda: self._latestByChannel(channelStr, count),
        )

    def _latestByChannel(
        self,
        channelStr: str = DEFAULT_CHROME_RELEASE_CHANNEL_STR,
        count: int | None = None,
    ) -> str | list[str]:
        logger.debug("Latest user-agent by channel requested channel=%s count=%s", channelStr, count)
        userAgentList = self.getLatestByChannelUserAgentList(channelStr)
        resultObject = self.sliceUserAgentResult(userAgentList, count)
        logger.debug(
            "Latest user-agent by channel resolved channel=%s poolSize=%s resultType=%s",
            channelStr,
            len(userAgentList),
            type(resultObject).__name__,
        )
        return resultObject

    def latestByChannelWithTiming(
        self,
        channelStr: str = DEFAULT_CHROME_RELEASE_CHANNEL_STR,
        count: int | None = None,
    ) -> dict[str, Any]:
        resultObject = self.latestByChannel(channelStr, count)
        return self.buildResultWithTiming(resultObject)

    def latestVersion(self, channelStr: str | None = None) -> str:
        return self.runTimedOperation(
            "latestVersion",
            lambda: self._latestVersion(channelStr),
        )

    def _latestVersion(self, channelStr: str | None = None) -> str:
        logger.debug("Latest Chrome version requested channel=%s", channelStr)
        if channelStr is not None:
            cleanChannelStr = self.normalizeChannel(channelStr)
            channelVersionMap = self._channelVersionMap()
            versionStr = channelVersionMap.get(cleanChannelStr)
            if not versionStr:
                raise ChromeUserAgentPoolUnavailableError(
                    f"No Chrome version is available for channel {cleanChannelStr}."
                )
            logger.debug(
                "Latest Chrome version resolved channel=%s version=%s",
                cleanChannelStr,
                versionStr,
            )
            return versionStr

        try:
            versionList = self.fetchLatestChromeVersions()
            if versionList:
                logger.debug("Latest Chrome version resolved version=%s", versionList[0])
                return versionList[0]
        except (ChromeForTestingVersionProxyError, ChromeVersionPayloadError):
            logger.debug("Latest Chrome version remote fetch failed, trying cached user agents")
            cachedUserAgentList = self.getCachedUserAgents()
            for userAgentStr in cachedUserAgentList:
                versionStr = extractChromeVersionFromUserAgent(userAgentStr)
                if versionStr is not None:
                    logger.debug("Latest Chrome version resolved from cache version=%s", versionStr)
                    return versionStr

        logger.debug("Latest Chrome version unavailable after remote and cache attempts")
        raise ChromeUserAgentPoolUnavailableError("No valid Chrome versions are available.")

    def channelVersionMap(self) -> dict[str, str]:
        return self.runTimedOperation("channelVersionMap", self._channelVersionMap)

    def _channelVersionMap(self) -> dict[str, str]:
        logger.debug("Chrome channel version map requested")
        try:
            channelVersionMap = self.fetchLatestChannelVersionMap()
            self.saveChannelVersionMap(channelVersionMap)
            logger.debug(
                "Chrome channel version map resolved from remote channelVersionMap=%s",
                channelVersionMap,
            )
            return channelVersionMap
        except (ChromeForTestingVersionProxyError, ChromeVersionPayloadError):
            logger.debug("Chrome channel version map remote fetch failed, trying cache")
            cachedChannelVersionMap = self.getCachedChannelVersionMap()
            if cachedChannelVersionMap:
                logger.debug(
                    "Chrome channel version map resolved from cache channelVersionMap=%s",
                    cachedChannelVersionMap,
                )
                return cachedChannelVersionMap
            logger.debug("Chrome channel version map unavailable after remote and cache attempts")
            raise ChromeUserAgentPoolUnavailableError(
                "Chrome channel versions are unavailable and no cached values exist."
            )

    def supportedPlatformList(self) -> dict[str, list[str]]:
        logger.debug("Supported platform list requested")
        return {
            familyStr: list(platformFragmentList)
            for familyStr, platformFragmentList
            in SUPPORTED_DESKTOP_PLATFORM_FRAGMENT_BY_FAMILY_DICT.items()
        }

    def lastTiming(self) -> dict[str, object] | None:
        return self.chromeUserAgentPoolRepo.getLastCallTiming()

    def timingHistory(self) -> list[dict[str, object]]:
        return self.chromeUserAgentPoolRepo.getCallTimingList()

    def fetchLatestChromeVersions(self) -> list[str]:
        logger.debug("Fetching latest Chrome versions from Chrome for Testing proxy")
        versionList = self.chromeForTestingVersionProxy.fetchLatestChromeVersionList()
        cleanVersionList = sortDottedVersionList(versionList)
        if not cleanVersionList:
            logger.debug(
                "Latest Chrome version payload invalid rawVersionCount=%s validVersionCount=0",
                len(versionList),
            )
            raise ChromeVersionPayloadError("Chrome for Testing returned no valid versions.")

        limitedVersionList = cleanVersionList[:MAX_CHROME_VERSION_COUNT_INT]
        logger.debug(
            "Latest Chrome versions fetched rawVersionCount=%s validVersionCount=%s keptVersionCount=%s newestVersion=%s",
            len(versionList),
            len(cleanVersionList),
            len(limitedVersionList),
            limitedVersionList[0],
        )
        return limitedVersionList

    def fetchLatestChannelVersionMap(self) -> dict[str, str]:
        logger.debug("Fetching latest Chrome channel versions from Chrome for Testing proxy")
        rawChannelVersionMap = self.chromeForTestingVersionProxy.fetchLatestChannelVersionMap()
        cleanChannelVersionMap: dict[str, str] = {}

        for channelStr in CHROME_RELEASE_CHANNEL_LIST:
            versionStr = rawChannelVersionMap.get(channelStr)
            if isValidDottedVersion(versionStr):
                cleanChannelVersionMap[channelStr] = versionStr

        if not cleanChannelVersionMap:
            logger.debug(
                "Chrome channel version payload invalid rawChannelCount=%s validChannelCount=0",
                len(rawChannelVersionMap),
            )
            raise ChromeVersionPayloadError("Chrome for Testing returned no valid channels.")

        logger.debug(
            "Chrome channel versions fetched rawChannelCount=%s validChannelCount=%s channelVersionMap=%s",
            len(rawChannelVersionMap),
            len(cleanChannelVersionMap),
            cleanChannelVersionMap,
        )
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
        skippedUserAgentCountInt = 0

        for chromeVersionStr in cleanVersionList:
            for platformFragmentStr in selectedPlatformFragmentList:
                try:
                    userAgentStr = buildChromeUserAgent(
                        chromeVersionStr,
                        platformFragmentStr,
                    )
                except ValueError:
                    skippedUserAgentCountInt += 1
                    continue

                if userAgentStr in seenUserAgentSet:
                    continue

                if not isValidChromeUserAgent(userAgentStr):
                    skippedUserAgentCountInt += 1
                    continue

                seenUserAgentSet.add(userAgentStr)
                userAgentList.append(userAgentStr)

        logger.debug(
            "Chrome user-agent pool generated inputVersionCount=%s validVersionCount=%s platformCount=%s generatedUserAgentCount=%s skippedUserAgentCount=%s",
            len(chromeVersionList),
            len(cleanVersionList),
            len(selectedPlatformFragmentList),
            len(userAgentList),
            skippedUserAgentCountInt,
        )
        return userAgentList

    def getFreshOrCachedUserAgents(self) -> list[str]:
        logger.debug("Resolving fresh or cached Chrome user-agent pool")
        try:
            chromeVersionList = self.fetchLatestChromeVersions()
            userAgentList = self.generateUserAgents(chromeVersionList)
            if not userAgentList:
                raise ChromeVersionPayloadError("No valid Chrome user agents were generated.")
            self.saveUserAgents(userAgentList)
            logger.debug(
                "Chrome user-agent pool resolved from remote generatedUserAgentCount=%s",
                len(userAgentList),
            )
            return userAgentList
        except (ChromeForTestingVersionProxyError, ChromeVersionPayloadError):
            logger.debug("Remote Chrome user-agent pool resolution failed, trying cache")
            cachedUserAgentList = self.getCachedUserAgents()
            if cachedUserAgentList:
                logger.debug(
                    "Chrome user-agent pool resolved from cache cachedUserAgentCount=%s",
                    len(cachedUserAgentList),
                )
                return cachedUserAgentList

            logger.debug("Chrome user-agent pool unavailable after remote and cache attempts")
            raise ChromeUserAgentPoolUnavailableError(
                "Chrome versions are unavailable and no cached user-agent pool exists."
            )

    def getLatestByChannelUserAgentList(self, channelStr: str) -> list[str]:
        cleanChannelStr = self.normalizeChannel(channelStr)
        channelVersionMap = self._channelVersionMap()
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
        logger.debug(
            "Chrome user-agent pool generated for channel channel=%s version=%s generatedUserAgentCount=%s",
            cleanChannelStr,
            versionStr,
            len(userAgentList),
        )
        return userAgentList

    def getCachedUserAgents(self) -> list[str]:
        logger.debug("Reading cached Chrome user-agent pool")
        keyValUserAgentList = self.readUserAgentListFromKeyVal()
        if keyValUserAgentList:
            self.chromeUserAgentPoolRepo.saveUserAgentList(keyValUserAgentList)
            logger.debug(
                "Cached Chrome user-agent pool loaded from Keyval userAgentCount=%s",
                len(keyValUserAgentList),
            )
            return keyValUserAgentList

        repoUserAgentList = self.chromeUserAgentPoolRepo.getUserAgentList()
        cleanRepoUserAgentList = [
            userAgentStr
            for userAgentStr in repoUserAgentList
            if isValidChromeUserAgent(userAgentStr)
        ]
        logger.debug(
            "Cached Chrome user-agent pool loaded from repo userAgentCount=%s",
            len(cleanRepoUserAgentList),
        )
        return cleanRepoUserAgentList

    def saveUserAgents(self, userAgentList: list[str]) -> None:
        cleanUserAgentList = [
            userAgentStr
            for userAgentStr in userAgentList
            if isValidChromeUserAgent(userAgentStr)
        ]
        self.chromeUserAgentPoolRepo.saveUserAgentList(cleanUserAgentList)
        logger.debug(
            "Chrome user-agent pool saved to repo key=%s userAgentCount=%s",
            KEY_VAL_USER_AGENT_LIST_KEY_STR,
            len(cleanUserAgentList),
        )

        keyValSavedBool = self.safeSetKeyValJson(
            KEY_VAL_USER_AGENT_LIST_KEY_STR,
            {USER_AGENT_LIST_JSON_KEY_STR: cleanUserAgentList},
        )
        logger.debug(
            "Chrome user-agent pool Keyval save attempted key=%s saved=%s userAgentCount=%s",
            KEY_VAL_USER_AGENT_LIST_KEY_STR,
            keyValSavedBool,
            len(cleanUserAgentList),
        )

    def getLastRandomUserAgent(self) -> str | None:
        logger.debug("Reading last random Chrome user-agent")
        keyValLastRandomUserAgentStr = self.readLastRandomUserAgentFromKeyVal()
        if keyValLastRandomUserAgentStr:
            self.chromeUserAgentPoolRepo.saveLastRandomUserAgent(
                keyValLastRandomUserAgentStr
            )
            logger.debug("Last random Chrome user-agent loaded from Keyval")
            return keyValLastRandomUserAgentStr

        repoLastRandomUserAgentStr = self.chromeUserAgentPoolRepo.getLastRandomUserAgent()
        logger.debug(
            "Last random Chrome user-agent loaded from repo found=%s",
            repoLastRandomUserAgentStr is not None,
        )
        return repoLastRandomUserAgentStr

    def saveLastRandomUserAgent(self, userAgentStr: str) -> None:
        if not isValidChromeUserAgent(userAgentStr):
            raise ValueError("Cannot save an invalid Chrome user-agent string.")

        self.chromeUserAgentPoolRepo.saveLastRandomUserAgent(userAgentStr)
        logger.debug(
            "Last random Chrome user-agent saved to repo chromeVersion=%s platformFamily=%s",
            extractChromeVersionFromUserAgent(userAgentStr),
            getDesktopPlatformFamily(userAgentStr),
        )
        keyValSavedBool = self.safeSetKeyValValue(
            KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR,
            userAgentStr,
        )
        logger.info(
            "Last random Chrome user-agent Keyval location saved=%s getUrl=%s chunkGetUrlList=%s chromeVersion=%s platformFamily=%s",
            keyValSavedBool,
            self.getKeyValGetUrlForLog(KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR),
            self.getKeyValChunkGetUrlListForLog(
                KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR,
                userAgentStr,
            ),
            extractChromeVersionFromUserAgent(userAgentStr),
            getDesktopPlatformFamily(userAgentStr),
        )
        logger.debug(
            "Last random Chrome user-agent Keyval save attempted key=%s saved=%s chromeVersion=%s platformFamily=%s",
            KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR,
            keyValSavedBool,
            extractChromeVersionFromUserAgent(userAgentStr),
            getDesktopPlatformFamily(userAgentStr),
        )

    def getCachedChannelVersionMap(self) -> dict[str, str]:
        logger.debug("Reading cached Chrome channel version map")
        keyValChannelVersionMap = self.readChannelVersionMapFromKeyVal()
        if keyValChannelVersionMap:
            self.chromeUserAgentPoolRepo.saveChannelVersionMap(keyValChannelVersionMap)
            logger.debug(
                "Chrome channel version map loaded from Keyval channelVersionMap=%s",
                keyValChannelVersionMap,
            )
            return keyValChannelVersionMap

        repoChannelVersionMap = self.chromeUserAgentPoolRepo.getChannelVersionMap()
        cleanRepoChannelVersionMap = {
            channelStr: versionStr
            for channelStr, versionStr in repoChannelVersionMap.items()
            if channelStr in CHROME_RELEASE_CHANNEL_LIST and isValidDottedVersion(versionStr)
        }
        logger.debug(
            "Chrome channel version map loaded from repo channelVersionMap=%s",
            cleanRepoChannelVersionMap,
        )
        return cleanRepoChannelVersionMap

    def saveChannelVersionMap(self, channelVersionMap: dict[str, str]) -> None:
        cleanChannelVersionMap = {
            channelStr: versionStr
            for channelStr, versionStr in channelVersionMap.items()
            if channelStr in CHROME_RELEASE_CHANNEL_LIST and isValidDottedVersion(versionStr)
        }
        self.chromeUserAgentPoolRepo.saveChannelVersionMap(cleanChannelVersionMap)
        logger.debug(
            "Chrome channel version map saved to repo key=%s channelVersionMap=%s",
            KEY_VAL_CHANNEL_VERSION_MAP_KEY_STR,
            cleanChannelVersionMap,
        )

        keyValSavedBool = self.safeSetKeyValJson(
            KEY_VAL_CHANNEL_VERSION_MAP_KEY_STR,
            {CHANNEL_VERSION_MAP_JSON_KEY_STR: cleanChannelVersionMap},
        )
        logger.debug(
            "Chrome channel version map Keyval save attempted key=%s saved=%s channelCount=%s",
            KEY_VAL_CHANNEL_VERSION_MAP_KEY_STR,
            keyValSavedBool,
            len(cleanChannelVersionMap),
        )

    def readUserAgentListFromKeyVal(self) -> list[str]:
        logger.debug("Reading user-agent list from Keyval key=%s", KEY_VAL_USER_AGENT_LIST_KEY_STR)
        valueObject = self.safeGetKeyValJson(KEY_VAL_USER_AGENT_LIST_KEY_STR)
        if isinstance(valueObject, dict):
            candidateObject = valueObject.get(USER_AGENT_LIST_JSON_KEY_STR)
        else:
            candidateObject = valueObject

        if not isinstance(candidateObject, list):
            logger.debug(
                "Keyval user-agent list missing or invalid key=%s valueType=%s",
                KEY_VAL_USER_AGENT_LIST_KEY_STR,
                type(candidateObject).__name__,
            )
            return []

        cleanUserAgentList = [
            userAgentStr
            for userAgentStr in candidateObject
            if isValidChromeUserAgent(userAgentStr)
        ]
        logger.debug(
            "Keyval user-agent list read key=%s rawCount=%s validCount=%s",
            KEY_VAL_USER_AGENT_LIST_KEY_STR,
            len(candidateObject),
            len(cleanUserAgentList),
        )
        return cleanUserAgentList

    def readLastRandomUserAgentFromKeyVal(self) -> str | None:
        logger.debug(
            "Reading last random user-agent from Keyval key=%s",
            KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR,
        )
        rawValueObject = self.safeGetKeyValValue(KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR)
        if isinstance(rawValueObject, str) and isValidChromeUserAgent(rawValueObject):
            logger.debug(
                "Keyval last random user-agent raw value read key=%s chromeVersion=%s platformFamily=%s",
                KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR,
                extractChromeVersionFromUserAgent(rawValueObject),
                getDesktopPlatformFamily(rawValueObject),
            )
            return rawValueObject

        valueObject = self.safeGetKeyValJson(KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR)
        if isinstance(valueObject, dict):
            candidateObject = valueObject.get(USER_AGENT_JSON_KEY_STR)
        else:
            candidateObject = valueObject

        if isinstance(candidateObject, str) and isValidChromeUserAgent(candidateObject):
            logger.debug(
                "Keyval last random user-agent read key=%s chromeVersion=%s platformFamily=%s",
                KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR,
                extractChromeVersionFromUserAgent(candidateObject),
                getDesktopPlatformFamily(candidateObject),
            )
            return candidateObject

        logger.debug(
            "Keyval last random user-agent missing or invalid key=%s valueType=%s",
            KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR,
            type(candidateObject).__name__,
        )
        return None

    def readChannelVersionMapFromKeyVal(self) -> dict[str, str]:
        logger.debug(
            "Reading channel version map from Keyval key=%s",
            KEY_VAL_CHANNEL_VERSION_MAP_KEY_STR,
        )
        valueObject = self.safeGetKeyValJson(KEY_VAL_CHANNEL_VERSION_MAP_KEY_STR)
        if isinstance(valueObject, dict) and CHANNEL_VERSION_MAP_JSON_KEY_STR in valueObject:
            candidateObject = valueObject.get(CHANNEL_VERSION_MAP_JSON_KEY_STR)
        else:
            candidateObject = valueObject

        if not isinstance(candidateObject, dict):
            logger.debug(
                "Keyval channel version map missing or invalid key=%s valueType=%s",
                KEY_VAL_CHANNEL_VERSION_MAP_KEY_STR,
                type(candidateObject).__name__,
            )
            return {}

        cleanChannelVersionMap = {
            channelStr: versionStr
            for channelStr, versionStr in candidateObject.items()
            if channelStr in CHROME_RELEASE_CHANNEL_LIST and isValidDottedVersion(versionStr)
        }
        logger.debug(
            "Keyval channel version map read key=%s rawChannelCount=%s validChannelCount=%s",
            KEY_VAL_CHANNEL_VERSION_MAP_KEY_STR,
            len(candidateObject),
            len(cleanChannelVersionMap),
        )
        return cleanChannelVersionMap

    def safeGetKeyValJson(self, keyStr: str) -> Any:
        try:
            valueObject = self.keyValStoreProxy.getJson(keyStr)
            logger.debug(
                "Safe Keyval JSON get completed key=%s found=%s valueType=%s",
                keyStr,
                valueObject is not None,
                type(valueObject).__name__,
            )
            return valueObject
        except (KeyValStoreProxyError, AttributeError):
            logger.debug("Safe Keyval JSON get failed key=%s", keyStr)
            return None

    def safeGetKeyValValue(self, keyStr: str) -> str | None:
        try:
            if hasattr(self.keyValStoreProxy, "getLargeValue"):
                valueObject = self.keyValStoreProxy.getLargeValue(keyStr)
            else:
                valueObject = self.keyValStoreProxy.getValue(keyStr)
            logger.debug(
                "Safe Keyval value get completed key=%s found=%s valueType=%s",
                keyStr,
                valueObject is not None,
                type(valueObject).__name__,
            )
            return valueObject
        except (KeyValStoreProxyError, AttributeError):
            logger.debug("Safe Keyval value get failed key=%s", keyStr)
            return None

    def safeSetKeyValJson(self, keyStr: str, valueObject: Any) -> bool:
        try:
            savedBool = bool(self.keyValStoreProxy.setJson(keyStr, valueObject))
            logger.debug(
                "Safe Keyval JSON set completed key=%s saved=%s valueType=%s",
                keyStr,
                savedBool,
                type(valueObject).__name__,
            )
            return savedBool
        except (KeyValStoreProxyError, AttributeError):
            logger.debug("Safe Keyval JSON set failed key=%s", keyStr)
            return False

    def safeSetKeyValValue(self, keyStr: str, valueStr: str) -> bool:
        try:
            if hasattr(self.keyValStoreProxy, "setLargeValue"):
                savedBool = bool(self.keyValStoreProxy.setLargeValue(keyStr, valueStr))
            else:
                savedBool = bool(self.keyValStoreProxy.setValue(keyStr, valueStr))
            logger.debug(
                "Safe Keyval value set completed key=%s saved=%s charCount=%s",
                keyStr,
                savedBool,
                len(valueStr),
            )
            return savedBool
        except (KeyValStoreProxyError, AttributeError):
            logger.debug("Safe Keyval value set failed key=%s", keyStr)
            return False

    def runTimedOperation(
        self,
        operationNameStr: str,
        operationFunc: Callable[[], ResultType],
    ) -> ResultType:
        startSecondFloat = time.perf_counter()

        try:
            resultObject = operationFunc()
        except Exception as exc:
            self.saveCallTiming(operationNameStr, startSecondFloat, exc)
            raise

        self.saveCallTiming(operationNameStr, startSecondFloat)
        return resultObject

    def saveCallTiming(
        self,
        operationNameStr: str,
        startSecondFloat: float,
        errorObject: Exception | None = None,
    ) -> None:
        durationSecondFloat = time.perf_counter() - startSecondFloat
        callTimingDict: dict[str, object] = {
            TIMING_OPERATION_JSON_KEY_STR: operationNameStr,
            TIMING_DURATION_SECOND_JSON_KEY_STR: durationSecondFloat,
            TIMING_DURATION_MILLISECOND_JSON_KEY_STR: durationSecondFloat * 1000,
            TIMING_SUCCESS_BOOL_JSON_KEY_STR: errorObject is None,
            TIMING_ERROR_TYPE_JSON_KEY_STR: (
                None if errorObject is None else type(errorObject).__name__
            ),
            TIMING_FINISHED_AT_UNIX_SECOND_JSON_KEY_STR: time.time(),
        }
        self.chromeUserAgentPoolRepo.saveCallTiming(callTimingDict)
        logger.info(
            "Operation completed operation=%s durationMillisecond=%.3f success=%s errorType=%s",
            operationNameStr,
            durationSecondFloat * 1000,
            errorObject is None,
            None if errorObject is None else type(errorObject).__name__,
        )
        logger.debug(
            "Operation timing recorded operation=%s durationMillisecond=%.3f success=%s errorType=%s",
            operationNameStr,
            durationSecondFloat * 1000,
            errorObject is None,
            None if errorObject is None else type(errorObject).__name__,
        )

    def buildResultWithTiming(self, resultObject: Any) -> dict[str, Any]:
        return {
            TIMING_RESULT_JSON_KEY_STR: resultObject,
            TIMING_TIMING_JSON_KEY_STR: self.lastTiming(),
        }

    def getKeyValGetUrlForLog(self, keyStr: str) -> str | None:
        try:
            return self.keyValStoreProxy.buildSafeGetUrlForLog(keyStr)
        except AttributeError:
            return None

    def getKeyValChunkGetUrlListForLog(
        self,
        keyStr: str,
        valueStr: str,
    ) -> list[str | None]:
        try:
            if not self.keyValStoreProxy.isPublicKeyValUrlMode():
                return []
            chunkSizeInt = self.keyValStoreProxy.getPublicValueChunkSize()
            chunkCountInt = (len(valueStr) + chunkSizeInt - 1) // chunkSizeInt
            if chunkCountInt <= 1:
                return []
            return self.keyValStoreProxy.buildSafeChunkGetUrlListForLog(
                keyStr,
                chunkCountInt,
            )
        except AttributeError:
            return []

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
        selectedUserAgentStr = self.randomGenerator.choice(familyUserAgentMap[selectedFamilyStr])
        logger.debug(
            "Random user-agent family selected family=%s familyCandidateCount=%s familyCount=%s",
            selectedFamilyStr,
            len(familyUserAgentMap[selectedFamilyStr]),
            len(familyList),
        )
        return selectedUserAgentStr

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
