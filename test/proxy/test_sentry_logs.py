"""Offline contract tests using actual Sentry log envelopes."""
import json
import logging
import unittest
from unittest.mock import patch

import sentry_sdk
from sentry_sdk.transport import Transport
from core.proxy.sentry_logs_proxy import SentryLogsProxy


class MemoryTransport(Transport):
    def __init__(self, options):
        super().__init__(options)
        self.envelopes = []

    def capture_envelope(self, envelope):
        self.envelopes.append(envelope)


class SentryLogsTest(unittest.TestCase):
    def setUp(self):
        self.environment = {"SENTRY_DSN": "https://public@sentry.example/1"}
        self.proxy = SentryLogsProxy(self.environment.get)
        self.transports = []
        original = sentry_sdk.Client

        def create(**options):
            client = original(**options, transport=MemoryTransport)
            self.transports.append(client.transport)
            return client

        self.factory = patch.object(sentry_sdk, "Client", side_effect=create).start()

    def tearDown(self):
        if self.proxy.client:
            self.proxy.client.close()
        self.proxy.client = None
        patch.stopall()

    def logs(self):
        self.proxy.flush()
        result = []
        for transport in self.transports:
            for envelope in transport.envelopes:
                for item in envelope.items:
                    if item.type == "log":
                        result.extend(json.loads(item.get_bytes())["items"])
        return result

    def testDisabledDoesNotInitializeSdk(self):
        for value in (None, "", "  "):
            self.environment["SENTRY_DSN"] = value
            self.proxy.captureMessage("local", "INFO", "project")
        self.factory.assert_not_called()

    def testDeliveryLabelsFormattingAndHostClientIsolation(self):
        host = sentry_sdk.Client(dsn="https://host@sentry.example/2", default_integrations=False)
        self.environment.update(SENTRY_ENVIRONMENT="staging", SENTRY_RELEASE="test-release")
        record = logging.LogRecord("project", logging.INFO, "", 0,
                                   "Completed %s {literal}", (3,), None)
        record.password = "never-send-this-extra"
        with sentry_sdk.new_scope() as scope:
            scope.set_client(host)
            self.proxy.handle(record)
            self.assertIs(host, sentry_sdk.get_client())
        host.close()
        logs = self.logs()
        self.assertEqual(1, len(logs))
        self.assertEqual("Completed 3 {literal}", logs[0]["body"])
        attrs = logs[0]["attributes"]
        self.assertEqual("n-user-agent", attrs["repository"]["value"])
        self.assertEqual("n-user-agent", attrs["service.name"]["value"])
        self.assertEqual("staging", attrs["sentry.environment"]["value"])
        self.assertEqual("test-release", attrs["sentry.release"]["value"])
        self.assertNotIn("password", attrs)

    def testRemoteThresholdAndInvalidFallback(self):
        self.environment["SENTRY_LOG_LEVEL"] = "WARN"
        self.proxy.captureMessage("skip", "INFO", "project")
        self.proxy.captureMessage("keep", "WARNING", "project")
        self.assertEqual(["keep"], [log["body"] for log in self.logs()])
        self.environment["SENTRY_LOG_LEVEL"] = "invalid"
        self.proxy.captureMessage("skip-debug", "DEBUG", "project")
        self.proxy.captureMessage("keep-info", "INFO", "project")
        self.assertEqual(["keep", "keep-info"], [log["body"] for log in self.logs()])

    def testRepeatedSetupHasOneHandlerAndOneClient(self):
        logger = logging.Logger("project", logging.DEBUG)
        self.proxy.attachLogger(logger)
        self.proxy.attachLogger(logger)
        logger.info("once")
        self.assertEqual(1, len(logger.handlers))
        self.assertEqual(1, self.factory.call_count)
        self.assertEqual(1, len(self.logs()))

    def testMalformedDsnWarnsOnceWithoutExposingValue(self):
        self.environment["SENTRY_DSN"] = "invalid-secret-dsn"
        with self.assertWarns(RuntimeWarning) as captured:
            self.proxy.captureMessage("local", "INFO", "project")
        self.assertNotIn("invalid-secret-dsn", str(captured.warning))
        with patch("warnings.warn") as warn:
            self.proxy.captureMessage("local", "INFO", "project")
        warn.assert_not_called()
        self.assertIsNone(self.proxy.client)

    def testRemovingDsnStopsDelivery(self):
        self.proxy.captureMessage("before", "INFO", "project")
        self.environment["SENTRY_DSN"] = ""
        self.proxy.captureMessage("after", "INFO", "project")
        self.assertEqual(["before"], [log["body"] for log in self.logs()])

    def testConsoleConfigurationPreservesRemoteThreshold(self):
        import os
        from core.helper.logger_config_helper import configureLoggerFromEnv
        logger = logging.getLogger("sentry-test-console")
        previous = (logger.handlers[:], logger.level, logger.propagate)
        try:
            self.proxy.attachLogger(logger)
            with patch.dict(os.environ, {"LOGGER": "DEBUG", "DEBUGGING": ""}):
                configureLoggerFromEnv(logger.name, "LOGGER", "%(message)s")
                configureLoggerFromEnv(logger.name, "LOGGER", "%(message)s")
            self.assertEqual(1, sum(isinstance(h, logging.StreamHandler) for h in logger.handlers))
            self.assertEqual(logging.NOTSET, self.proxy.level)
            logger.debug("filtered")
            logger.info("delivered")
            self.assertEqual(["delivered"], [log["body"] for log in self.logs()])
        finally:
            logger.handlers, logger.level, logger.propagate = previous

    def testVerboseOutputIsForwardedOnce(self):
        from core.service.verbose_chrome_user_agent_pool_service import VerboseChromeUserAgentPoolService
        service = object.__new__(VerboseChromeUserAgentPoolService)
        output = []
        service.outputFunc = output.append
        with patch.object(service, "getLoggerLevelName", return_value="INFO"), patch(
            "core.service.verbose_chrome_user_agent_pool_service.sentryLogsProxy", self.proxy
        ):
            service.logInfo("Ready count=3")
        self.assertEqual(1, len(output))
        self.assertEqual(["Ready count=3"], [log["body"] for log in self.logs()])
