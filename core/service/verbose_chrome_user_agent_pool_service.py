from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from typing import Protocol

from core.constant.chrome_user_agent_pool_constant import (
    CORE_LOGGER_NAME_STR,
    KEY_VAL_BASE_URL_ENV_STR,
    KEY_VAL_DEFAULT_BASE_URL_STR,
    KEY_VAL_USER_AGENT_LIST_KEY_STR,
    LOGGER_LEVEL_ENV_STR,
    VERBOSE_RANKED_USER_AGENT_COUNT_INT,
)
from core.helper.key_val_key_hash_helper import hashKeyValKey
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
        self.outputFunc("=== User-agent pool discovery run ===")
        self.outputFunc(
            f"[run] hashed storage key: {hashKeyValKey(KEY_VAL_USER_AGENT_LIST_KEY_STR)}"
        )
        self.outputFunc(f"[run] log level: {self.getLoggerLevelName()}")
        self.outputFunc(f"[run] note: {self.getKeyValSafetyNote()}")
        runOptionTextStr = self.formatRunOptionText(
            channelStr=channelStr,
            releaseChannelList=releaseChannelList,
            count=count,
            platformFamilyList=platformFamilyList,
            rankedCount=rankedCount,
        )
        if runOptionTextStr:
            self.outputFunc(f"[run] options: {runOptionTextStr}")

        with self.maybeMutedCoreLogger():
            self.outputFunc("[cache] checking saved user-agent list")
            cachedUserAgentList = self.chromeUserAgentPoolService.getCachedUserAgents()
            if cachedUserAgentList:
                self.outputFunc(
                    f"[cache] usable saved user-agent: {cachedUserAgentList[0]}"
                )
            else:
                self.outputFunc("[cache] no usable saved user-agent")

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

        elapsedSecondFloat = self.perfCounterFunc() - startSecondFloat
        self.outputFunc(f"[run] selected user-agent: {self.finalValueStr}")
        self.outputFunc(f"[run] took {elapsedSecondFloat:.3f} seconds")
        return self.finalValueStr

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
        levelNameStr = os.getenv(LOGGER_LEVEL_ENV_STR, "").strip().upper()
        return levelNameStr or "OFF"

    def getKeyValSafetyNote(self) -> str:
        baseUrlStr = os.getenv(KEY_VAL_BASE_URL_ENV_STR, KEY_VAL_DEFAULT_BASE_URL_STR)
        if baseUrlStr.rstrip("/") == KEY_VAL_DEFAULT_BASE_URL_STR:
            return "KeyVal is public; credentials are never stored"

        return "KeyVal credentials are never printed or stored"

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
