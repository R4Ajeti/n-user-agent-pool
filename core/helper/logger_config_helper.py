from __future__ import annotations

import logging
import os


def normalizeLoggerLevelName(levelValueStr: str) -> str:
    levelNameStr = levelValueStr.strip().upper()
    levelAliasDict = {
        "WARN": "WARNING",
        "WARM": "WARNING",
        "0": "NOTSET",
        "10": "DEBUG",
        "20": "INFO",
        "30": "WARNING",
        "40": "ERROR",
        "50": "CRITICAL",
    }
    return levelAliasDict.get(levelNameStr, levelNameStr)


def getLoggerLevelNameFromEnv(
    loggerEnvNameStr: str,
    debuggingEnvNameStr: str,
) -> str:
    debuggingValueStr = os.getenv(debuggingEnvNameStr, "").strip().lower()
    if debuggingValueStr:
        return "DEBUG" if debuggingValueStr == "true" else "INFO"

    return normalizeLoggerLevelName(os.getenv(loggerEnvNameStr, ""))


def configureLoggerFromEnv(
    loggerNameStr: str,
    loggerEnvNameStr: str,
    loggerFormatStr: str,
    debuggingEnvNameStr: str = "DEBUGGING",
) -> logging.Logger:
    logger = logging.getLogger(loggerNameStr)
    levelNameStr = getLoggerLevelNameFromEnv(
        loggerEnvNameStr,
        debuggingEnvNameStr,
    )

    if not levelNameStr:
        return logger

    levelObject = getattr(logging, levelNameStr, None)
    if not isinstance(levelObject, int):
        levelObject = logging.INFO

    logger.setLevel(levelObject)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(loggerFormatStr))
        logger.addHandler(handler)

    for handler in logger.handlers:
        handler.setLevel(levelObject)

    return logger
