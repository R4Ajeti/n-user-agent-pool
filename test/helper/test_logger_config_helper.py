import os
import unittest

from core.helper.logger_config_helper import configureLoggingFromEnv


class LoggerConfigHelperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.previousLoggerValueStr = os.environ.get("LOGGER")
        self.previousDebuggingValueStr = os.environ.get("DEBUGGING")
        os.environ.pop("LOGGER", None)
        os.environ.pop("DEBUGGING", None)
        self.loggerNameStr = f"n-user-agent.test.{self._testMethodName}"

    def tearDown(self) -> None:
        self.restoreEnvironmentValue("LOGGER", self.previousLoggerValueStr)
        self.restoreEnvironmentValue("DEBUGGING", self.previousDebuggingValueStr)

    def restoreEnvironmentValue(self, nameStr: str, valueStr: str | None) -> None:
        if valueStr is None:
            os.environ.pop(nameStr, None)
        else:
            os.environ[nameStr] = valueStr

    def configureLogger(self) -> str | None:
        return configureLoggingFromEnv(
            self.loggerNameStr,
            "LOGGER",
            "DEBUGGING",
        )

    def testLoggerLevelConfiguresDebug(self) -> None:
        os.environ["LOGGER"] = "DEBUG"
        self.assertEqual("DEBUG", self.configureLogger())

    def testMissingControlsKeepPackageQuiet(self) -> None:
        self.assertIsNone(self.configureLogger())

    def testDebuggingTrueSelectsDebug(self) -> None:
        os.environ["DEBUGGING"] = "true"
        self.assertEqual("DEBUG", self.configureLogger())

    def testDebuggingFalseSelectsInfo(self) -> None:
        os.environ["DEBUGGING"] = "false"
        self.assertEqual("INFO", self.configureLogger())

    def testDebuggingOverridesLogger(self) -> None:
        os.environ.update(DEBUGGING="false", LOGGER="DEBUG")
        self.assertEqual("INFO", self.configureLogger())

    def testBlankDebuggingFallsBackToLogger(self) -> None:
        os.environ.update(DEBUGGING="  ", LOGGER="ERROR")
        self.assertEqual("ERROR", self.configureLogger())

    def testAliasesAndNumericLevelsAreNormalized(self) -> None:
        expectedByValueDict = {
            "warm": "WARNING",
            "0": "NOTSET",
            "10": "DEBUG",
            "20": "INFO",
            "30": "WARNING",
            "40": "ERROR",
            "50": "CRITICAL",
        }
        for valueStr, expectedLevelStr in expectedByValueDict.items():
            with self.subTest(value=valueStr):
                os.environ["LOGGER"] = valueStr
                self.assertEqual(expectedLevelStr, self.configureLogger())

    def testInvalidLoggerFallsBackToInfo(self) -> None:
        os.environ["LOGGER"] = "verbose"
        self.assertEqual("INFO", self.configureLogger())


if __name__ == "__main__":
    unittest.main()
