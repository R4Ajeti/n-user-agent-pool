from __future__ import annotations

import logging
import os


def configureLoggerFromEnv(
    loggerNameStr: str,
    envNameStr: str,
    loggerFormatStr: str,
) -> logging.Logger:
    logger = logging.getLogger(loggerNameStr)
    levelNameStr = os.getenv(envNameStr, "").strip().upper()

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
