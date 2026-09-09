from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from typing import Protocol

from core.constant.chrome_user_agent_pool_constant import (
    CORE_LOGGER_NAME_STR,
    DEBUGGING_ENV_STR,
    KEY_VAL_BASE_URL_ENV_STR,
    KEY_VAL_DEFAULT_BASE_URL_STR,
    KEY_VAL_NAMESPACE_ENV_STR,
    KEY_VAL_PUBLIC_BASE_URL_STR,
    KEY_VAL_USER_AGENT_LIST_KEY_STR,
    LOGGER_LEVEL_ENV_STR,
    LOGGER_FORMAT_STR,
    VERBOSE_RANKED_USER_AGENT_COUNT_INT,
)
from core.helper.key_val_key_hash_helper import hashKeyValKey
from core.helper.logger_config_helper import formatLogMessage, getLoggerLevelNameFromEnv
from core.proxy.sentry_logs_proxy import sentryLogsProxy
from core.service.chrome_user_agent_pool_service import ChromeUserAgentPoolService


class ChromeUserAgentPoolRepoProtocol(Protocol):
    def getUserAgentList(self) -> list[str]:
        ...


class ChromeUserAgentPoolServiceProtocol(Protocol):
    chromeUserAgentPoolRepo: ChromeUserAgentPoolRepoProtocol

    def getCachedUserAgents(self) -> list[str]:
        ...

    def random(
        self,
        channelStr: str | None = None,
        count: int | None = None,
        platformFamilyList: str | Sequence[str] | None = None,
        releaseChannelList: str | Sequence[str] | None = None,
    ) -> str:
        ...

    def getRandomCandidateUserAgentList(
        self,
        releaseChannelList: str | Sequence[str] | None = None,
        count: int | None = None,
        platformFamilyList: str | Sequence[str] | None = None,
    ) -> list[str]:
        ...



class VerboseChromeUserAgentPoolService:
    def __init__(
        self,
        chromeUserAgentPoolService: ChromeUserAgentPoolServiceProtocol | None = None,
        outputFunc: Callable[[str], None] = print,
        perfCounterFunc: Callable[[], float] = time.perf_counter,
    ) -> None:
        self.chromeUserAgentPoolService = (
            chromeUserAgentPoolService or ChromeUserAgentPoolService()
        )
        self.outputFunc = outputFunc
        self.perfCounterFunc = perfCounterFunc
        self.finalValueStr: str | None = None
        self.rankedUserAgentList: list[str] = []

    def run(
        self,
        channelStr: str | None = None,
        releaseChannelList: str | Sequence[str] | None = None,
        count: int | None = None,
        platformFamilyList: str | Sequence[str] | None = None,
        rankedCount: int = VERBOSE_RANKED_USER_AGENT_COUNT_INT,
    ) -> str:
        startSecondFloat = self.perfCounterFunc()
        try:
            self.logInfo("=== User-agent pool discovery run ===")
            self.logInfo(
                "[run] hashed storage key: "
                f"{hashKeyValKey(KEY_VAL_USER_AGENT_LIST_KEY_STR, namespaceStr=self.getKeyValNamespace())}"
            )
            self.logInfo(f"[run] log level: {self.getLoggerLevelName()}")
            self.logInfo(f"[run] note: {self.getKeyValSafetyNote()}")
            runOptionTextStr = self.formatRunOptionText(
                channelStr=channelStr,
                releaseChannelList=releaseChannelList,
                count=count,
                platformFamilyList=platformFamilyList,
                rankedCount=rankedCount,
            )
            if runOptionTextStr:
                self.logInfo(f"[run] options: {runOptionTextStr}")

            with self.maybeMutedCoreLogger():
                self.logInfo("[cache] checking saved user-agent list")
                cachedUserAgentList = self.chromeUserAgentPoolService.getCachedUserAgents()
                if cachedUserAgentList:
                    self.logInfo(
                        f"[cache] usable saved user-agent: {cachedUserAgentList[0]}"
                    )
                else:
                    self.logInfo("[cache] no usable saved user-agent")

                self.finalValueStr = self.chromeUserAgentPoolService.random(
                    channelStr=channelStr,
                    count=count,
                    platformFamilyList=platformFamilyList,
                    releaseChannelList=releaseChannelList,
                )
                rankedReleaseChannelList = releaseChannelList
                if rankedReleaseChannelList is None and channelStr is not None:
                    rankedReleaseChannelList = [channelStr]
                self.rankedUserAgentList = self.getRankedUserAgentList(
                    selectedUserAgentStr=self.finalValueStr,
                    releaseChannelList=rankedReleaseChannelList,
                    count=count,
                    platformFamilyList=platformFamilyList,
                    rankedCount=rankedCount,
                )

            self.logInfo(f"[run] selected user-agent: {self.finalValueStr}")
            return self.finalValueStr
        finally:
            elapsedSecondFloat = self.perfCounterFunc() - startSecondFloat
            self.logInfo(f"Total run time: {elapsedSecondFloat:.2f} seconds operation=run")

    def logInfo(self, messageStr: str) -> None:
        if self.getLoggerLevelName() in {"WARNING", "ERROR", "CRITICAL"}:
            return
        for lineStr in messageStr.splitlines() or [""]:
            self.outputFunc(formatLogMessage(lineStr, CORE_LOGGER_NAME_STR, "INFO", LOGGER_FORMAT_STR))
            sentryLogsProxy.captureMessage(lineStr, "INFO", CORE_LOGGER_NAME_STR)

    def getRankedUserAgentList(
        self,
        selectedUserAgentStr: str,
        releaseChannelList: str | Sequence[str] | None = None,
        count: int | None = None,
        platformFamilyList: str | Sequence[str] | None = None,
        rankedCount: int = VERBOSE_RANKED_USER_AGENT_COUNT_INT,
    ) -> list[str]:
        if not isinstance(rankedCount, int):
            raise ValueError("rankedCount must be an integer.")

        if rankedCount <= 0:
            return []

        if releaseChannelList is None and count is None and platformFamilyList is None:
            userAgentList = (
                self.chromeUserAgentPoolService.chromeUserAgentPoolRepo.getUserAgentList()
            )
        else:
            userAgentList = self.chromeUserAgentPoolService.getRandomCandidateUserAgentList(
                releaseChannelList=releaseChannelList,
                count=count,
                platformFamilyList=platformFamilyList,
            )
        rankedUserAgentList = [selectedUserAgentStr]
        for userAgentStr in userAgentList:
            if len(rankedUserAgentList) >= rankedCount:
                break
            if userAgentStr != selectedUserAgentStr:
                rankedUserAgentList.append(userAgentStr)

        return rankedUserAgentList

    def formatRunOptionText(
        self,
        channelStr: str | None = None,
        releaseChannelList: str | Sequence[str] | None = None,
        count: int | None = None,
        platformFamilyList: str | Sequence[str] | None = None,
        rankedCount: int = VERBOSE_RANKED_USER_AGENT_COUNT_INT,
    ) -> str:
        optionTextList: list[str] = []
        if channelStr is not None:
            optionTextList.append(f"channel={channelStr}")
        if releaseChannelList is not None:
            optionTextList.append(
                f"releaseChannels={self.formatOptionValue(releaseChannelList)}"
            )
        if count is not None:
            optionTextList.append(f"count={count}")
        if platformFamilyList is not None:
            optionTextList.append(
                f"platformFamilies={self.formatOptionValue(platformFamilyList)}"
            )
        if rankedCount != VERBOSE_RANKED_USER_AGENT_COUNT_INT:
            optionTextList.append(f"rankedCount={rankedCount}")

        return ", ".join(optionTextList)

    def formatOptionValue(self, valueObject: object) -> str:
        if isinstance(valueObject, str):
            return valueObject

        if isinstance(valueObject, Sequence):
            return "|".join(str(value) for value in valueObject)

        return str(valueObject)

    def getLoggerLevelName(self) -> str:
        levelNameStr = getLoggerLevelNameFromEnv(
            LOGGER_LEVEL_ENV_STR,
            DEBUGGING_ENV_STR,
        )
        return levelNameStr or "OFF"

    def getKeyValSafetyNote(self) -> str:
        baseUrlStr = os.getenv(KEY_VAL_BASE_URL_ENV_STR, KEY_VAL_DEFAULT_BASE_URL_STR)
        if not baseUrlStr:
            return "KeyVal persistence is off unless KEY_VAL_BASE_URL is set"

        if baseUrlStr.rstrip("/") == KEY_VAL_PUBLIC_BASE_URL_STR:
            if self.getKeyValNamespace():
                return "Public KeyVal uses the configured namespace; credentials are never stored"
            return "Public KeyVal is skipped until USER_AGENT_POOL_NAMESPACE is set"

        return "KeyVal credentials are never printed or stored"

    def getKeyValNamespace(self) -> str:
        return os.getenv(KEY_VAL_NAMESPACE_ENV_STR, "").strip()

    @contextmanager
    def maybeMutedCoreLogger(self) -> Iterator[None]:
        logger = logging.getLogger(CORE_LOGGER_NAME_STR)
        previousDisabledBool = logger.disabled
        if self.getLoggerLevelName() == "INFO":
            logger.disabled = True
        try:
            yield
        finally:
            logger.disabled = previousDisabledBool
