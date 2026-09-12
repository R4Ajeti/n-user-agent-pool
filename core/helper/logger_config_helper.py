from __future__ import annotations

import os

from n_log_forge import configure, setPackageLevel


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


def configureLoggingFromEnv(
    loggerNameStr: str,
    loggerEnvNameStr: str,
    debuggingEnvNameStr: str = "DEBUGGING",
) -> str | None:
    """Configure n-log-forge and the exact package hierarchy from the environment."""
    levelNameStr = getLoggerLevelNameFromEnv(
        loggerEnvNameStr,
        debuggingEnvNameStr,
    )
    if levelNameStr and levelNameStr not in {
        "NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL",
    }:
        levelNameStr = "INFO"

    originalLoggerValueStr = os.environ.get(loggerEnvNameStr)
    originalDebuggingValueStr = os.environ.get(debuggingEnvNameStr)
    try:
        if originalLoggerValueStr is not None and levelNameStr:
            os.environ[loggerEnvNameStr] = levelNameStr
        if originalDebuggingValueStr is not None and originalDebuggingValueStr.strip():
            os.environ[debuggingEnvNameStr] = (
                "true" if originalDebuggingValueStr.strip().lower() == "true" else "false"
            )
        configure(manageRootLevel=False)
    finally:
        if originalLoggerValueStr is None:
            os.environ.pop(loggerEnvNameStr, None)
        else:
            os.environ[loggerEnvNameStr] = originalLoggerValueStr
        if originalDebuggingValueStr is None:
            os.environ.pop(debuggingEnvNameStr, None)
        else:
            os.environ[debuggingEnvNameStr] = originalDebuggingValueStr
    setPackageLevel(loggerNameStr, levelNameStr or "CRITICAL")
    return levelNameStr or None
