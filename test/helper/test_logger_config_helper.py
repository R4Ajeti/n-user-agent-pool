import logging
import os
import unittest

from core.helper.logger_config_helper import configureLoggerFromEnv


class LoggerConfigHelperTest(unittest.TestCase):
    def testConfigureLoggerFromEnvSetsDebugLevel(self) -> None:
        previousValueStr = os.environ.get("LOGGER")
        os.environ["LOGGER"] = "DEBUG"

        try:
            logger = configureLoggerFromEnv(
                "user_agent_pool_test_logger",
                "LOGGER",
                "%(levelname)s:%(message)s",
            )
            self.assertEqual(logging.DEBUG, logger.level)
        finally:
            if previousValueStr is None:
                os.environ.pop("LOGGER", None)
            else:
                os.environ["LOGGER"] = previousValueStr

    def testConfigureLoggerFromEnvKeepsDefaultWhenMissing(self) -> None:
        previousValueStr = os.environ.pop("LOGGER", None)

        try:
            logger = configureLoggerFromEnv(
                "user_agent_pool_missing_logger",
                "LOGGER",
                "%(levelname)s:%(message)s",
            )
            self.assertEqual(logging.NOTSET, logger.level)
        finally:
            if previousValueStr is not None:
                os.environ["LOGGER"] = previousValueStr


if __name__ == "__main__":
    unittest.main()
