from __future__ import annotations

import logging
import os


def getLoggerLevelNameFromEnv(
    loggerEnvNameStr: str,
    debuggingEnvNameStr: str,
) -> str:
    debuggingValueStr = os.getenv(debuggingEnvNameStr, "").strip().lower()
    if debuggingValueStr:
        return "DEBUG" if debuggingValueStr == "true" else "INFO"

    return os.getenv(loggerEnvNameStr, "").strip().upper()


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
