import logging
import os
import unittest

from core.helper.logger_config_helper import configureLoggerFromEnv


class LoggerConfigHelperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.previousLoggerValueStr = os.environ.get("LOGGER")
        self.previousDebuggingValueStr = os.environ.get("DEBUGGING")
        os.environ.pop("LOGGER", None)
        os.environ.pop("DEBUGGING", None)
        self.loggerNameStr = f"user_agent_pool_{self._testMethodName}"

    def tearDown(self) -> None:
        self.restoreEnvironmentValue("LOGGER", self.previousLoggerValueStr)
        self.restoreEnvironmentValue("DEBUGGING", self.previousDebuggingValueStr)
        logger = logging.getLogger(self.loggerNameStr)
        logger.handlers.clear()
        logger.setLevel(logging.NOTSET)
        logger.propagate = True

    def restoreEnvironmentValue(self, nameStr: str, valueStr: str | None) -> None:
        if valueStr is None:
            os.environ.pop(nameStr, None)
        else:
            os.environ[nameStr] = valueStr

    def configureLogger(self) -> logging.Logger:
        return configureLoggerFromEnv(
            self.loggerNameStr,
            "LOGGER",
            "%(levelname)s:%(message)s",
            "DEBUGGING",
        )

    def testConfigureLoggerFromEnvSetsDebugLevelFromLogger(self) -> None:
        os.environ["LOGGER"] = "DEBUG"

        logger = self.configureLogger()

        self.assertEqual(logging.DEBUG, logger.level)

    def testConfigureLoggerFromEnvKeepsDefaultWhenBothAreMissing(self) -> None:
        logger = self.configureLogger()

        self.assertEqual(logging.NOTSET, logger.level)

    def testDebuggingTrueSetsDebugLevel(self) -> None:
        os.environ["DEBUGGING"] = "true"

        logger = self.configureLogger()

        self.assertEqual(logging.DEBUG, logger.level)

    def testDebuggingFalseSetsInfoLevel(self) -> None:
        os.environ["DEBUGGING"] = "false"

        logger = self.configureLogger()

        self.assertEqual(logging.INFO, logger.level)

    def testDebuggingTrueOverridesLoggerInfo(self) -> None:
        os.environ["DEBUGGING"] = "true"
        os.environ["LOGGER"] = "INFO"

        logger = self.configureLogger()

        self.assertEqual(logging.DEBUG, logger.level)

    def testDebuggingFalseOverridesLoggerDebug(self) -> None:
        os.environ["DEBUGGING"] = "false"
        os.environ["LOGGER"] = "DEBUG"

        logger = self.configureLogger()

        self.assertEqual(logging.INFO, logger.level)

    def testBlankDebuggingFallsBackToLogger(self) -> None:
        os.environ["DEBUGGING"] = "  "
        os.environ["LOGGER"] = "ERROR"

        logger = self.configureLogger()

        self.assertEqual(logging.ERROR, logger.level)

    def testNonTrueDebuggingValueUsesInfoLevel(self) -> None:
        os.environ["DEBUGGING"] = "unexpected"
        os.environ["LOGGER"] = "DEBUG"

        logger = self.configureLogger()

        self.assertEqual(logging.INFO, logger.level)


if __name__ == "__main__":
    unittest.main()
