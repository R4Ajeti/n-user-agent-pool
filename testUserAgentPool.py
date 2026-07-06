from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Protocol

from core import ChromeUserAgentPoolService
from core.constant.chrome_user_agent_pool_constant import (
    CORE_LOGGER_NAME_STR,
    KEY_VAL_BASE_URL_ENV_STR,
    KEY_VAL_DEFAULT_BASE_URL_STR,
    KEY_VAL_USER_AGENT_LIST_KEY_STR,
    LOGGER_LEVEL_ENV_STR,
)
from core.helper.key_val_key_hash_helper import hashKeyValKey


RUNNER_RANKED_USER_AGENT_COUNT_INT = 5


class ChromeUserAgentPoolRepoProtocol(Protocol):
    def getUserAgentList(self) -> list[str]:
        ...


class ChromeUserAgentPoolServiceProtocol(Protocol):
    chromeUserAgentPoolRepo: ChromeUserAgentPoolRepoProtocol

    def getCachedUserAgents(self) -> list[str]:
        ...

    def random(self) -> str:
        ...


def getLoggerLevelName() -> str:
    levelNameStr = os.getenv(LOGGER_LEVEL_ENV_STR, "").strip().upper()
    return levelNameStr or "OFF"


def shouldUseInfoRunFormat() -> bool:
    return getLoggerLevelName() == "INFO"


def getKeyValSafetyNote() -> str:
    baseUrlStr = os.getenv(KEY_VAL_BASE_URL_ENV_STR, KEY_VAL_DEFAULT_BASE_URL_STR)
    if baseUrlStr.rstrip("/") == KEY_VAL_DEFAULT_BASE_URL_STR:
        return "KeyVal is public; credentials are never stored"

    return "KeyVal credentials are never printed or stored"


def getRankedUserAgentList(
    service: ChromeUserAgentPoolServiceProtocol,
    selectedUserAgentStr: str,
) -> list[str]:
    userAgentList = service.chromeUserAgentPoolRepo.getUserAgentList()
    if not userAgentList:
        return [selectedUserAgentStr]

    return userAgentList[:RUNNER_RANKED_USER_AGENT_COUNT_INT]


@contextmanager
def mutedCoreLogger() -> Iterator[None]:
    logger = logging.getLogger(CORE_LOGGER_NAME_STR)
    previousDisabledBool = logger.disabled
    logger.disabled = True
    try:
        yield
    finally:
        logger.disabled = previousDisabledBool


def runUserAgentPoolDiscovery(
    serviceFactory: Callable[[], ChromeUserAgentPoolServiceProtocol] = ChromeUserAgentPoolService,
    outputFunc: Callable[[str], None] = print,
    perfCounterFunc: Callable[[], float] = time.perf_counter,
) -> str:
    startSecondFloat = perfCounterFunc()
    outputFunc("=== User-agent pool discovery run ===")
    outputFunc(f"[run] hashed storage key: {hashKeyValKey(KEY_VAL_USER_AGENT_LIST_KEY_STR)}")
    outputFunc(f"[run] log level: {getLoggerLevelName()}")
    outputFunc(f"[run] note: {getKeyValSafetyNote()}")

    with mutedCoreLogger():
        service = serviceFactory()
        outputFunc("[cache] checking saved user-agent list")
        cachedUserAgentList = service.getCachedUserAgents()
        if cachedUserAgentList:
            outputFunc(f"[cache] usable saved user-agent: {cachedUserAgentList[0]}")
        else:
            outputFunc("[cache] no usable saved user-agent")

        selectedUserAgentStr = service.random()
        rankedUserAgentList = getRankedUserAgentList(service, selectedUserAgentStr)

    elapsedSecondFloat = perfCounterFunc() - startSecondFloat
    outputFunc(f"[run] selected user-agent: {selectedUserAgentStr}")
    outputFunc(f"[run] took {elapsedSecondFloat:.3f} seconds")
    outputFunc(f"Final selected user-agent: {selectedUserAgentStr}")
    outputFunc(f"Ranked user-agent list: {rankedUserAgentList}")
    return selectedUserAgentStr


def main() -> None:
    if shouldUseInfoRunFormat():
        runUserAgentPoolDiscovery()
        return

    service = ChromeUserAgentPoolService()
    userAgentStr = service.random()
    print(userAgentStr)


if __name__ == "__main__":
    main()
