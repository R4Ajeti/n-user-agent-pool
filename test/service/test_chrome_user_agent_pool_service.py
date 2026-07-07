import os
import random
import unittest

from core.constant.chrome_user_agent_pool_constant import (
    CORE_LOGGER_NAME_STR,
    KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR,
    TIMING_DURATION_MILLISECOND_JSON_KEY_STR,
    TIMING_DURATION_SECOND_JSON_KEY_STR,
    TIMING_ERROR_TYPE_JSON_KEY_STR,
    TIMING_OPERATION_JSON_KEY_STR,
    TIMING_RESULT_JSON_KEY_STR,
    TIMING_SUCCESS_BOOL_JSON_KEY_STR,
    TIMING_TIMING_JSON_KEY_STR,
    USER_AGENT_HISTORY_BACKEND_ENV_STR,
    USER_AGENT_HISTORY_FIREBASE_REALTIME_DATABASE_BACKEND_STR,
)
from core.proxy.firebase_realtime_database_history_proxy import (
    FirebaseRealtimeDatabaseHistoryProxyError,
)
from core.proxy.chrome_for_testing_version_proxy import ChromeForTestingVersionProxyError
from core.service.chrome_user_agent_pool_error import ChromeUserAgentPoolUnavailableError
from core.service.chrome_user_agent_pool_service import ChromeUserAgentPoolService


class FakeChromeForTestingVersionProxy:
    def __init__(
        self,
        versionList=None,
        channelVersionMap=None,
        shouldRaiseBool=False,
    ) -> None:
        self.versionList = versionList or []
        self.channelVersionMapValue = channelVersionMap or {
            "Stable": "150.0.7871.46",
            "Beta": "151.0.7922.10",
            "Dev": "151.0.7912.0",
            "Canary": "152.0.7934.0",
        }
        self.shouldRaiseBool = shouldRaiseBool

    def fetchLatestChromeVersionList(self):
        if self.shouldRaiseBool:
            raise ChromeForTestingVersionProxyError("remote failed")
        return list(self.versionList)

    def fetchLatestChannelVersionMap(self):
        if self.shouldRaiseBool:
            raise ChromeForTestingVersionProxyError("remote failed")
        return dict(self.channelVersionMapValue)


class FakeKeyValStoreProxy:
    def __init__(self, initialStore=None) -> None:
        self.store = dict(initialStore or {})

    def getJson(self, keyStr):
        return self.store.get(keyStr)

    def setJson(self, keyStr, valueObject):
        self.store[keyStr] = valueObject
        return True

    def getValue(self, keyStr):
        return self.store.get(keyStr)

    def setValue(self, keyStr, valueStr):
        self.store[keyStr] = valueStr
        return True

    def buildSafeGetUrlForLog(self, keyStr):
        return f"https://api.keyval.org/get/fake-{keyStr}"


class FirstChoiceRandom:
    def choice(self, valueList):
        return valueList[0]


class FakeUserAgentHistoryProxy:
    def __init__(self, shouldRaiseBool=False) -> None:
        self.shouldRaiseBool = shouldRaiseBool
        self.historyRecordList = []

    def appendHistoryRecord(self, historyRecordDict):
        if self.shouldRaiseBool:
            raise FirebaseRealtimeDatabaseHistoryProxyError("history failed")
        self.historyRecordList.append(dict(historyRecordDict))
        return True


class ChromeUserAgentPoolServiceTest(unittest.TestCase):
    def buildService(
        self,
        versionList=None,
        keyValStore=None,
        shouldRaiseBool=False,
        randomGenerator=None,
        firebaseRealtimeDatabaseHistoryProxy=None,
    ):
        return ChromeUserAgentPoolService(
            chromeForTestingVersionProxy=FakeChromeForTestingVersionProxy(
                versionList=versionList or [
                    "149.0.7000.1",
                    "150.0.7871.46",
                    "151.0.7922.10",
                ],
                shouldRaiseBool=shouldRaiseBool,
            ),
            keyValStoreProxy=keyValStore or FakeKeyValStoreProxy(),
            firebaseRealtimeDatabaseHistoryProxy=firebaseRealtimeDatabaseHistoryProxy,
            randomGenerator=randomGenerator or random.Random(7),
        )

    def testLatestReturnsOneLatestUserAgentString(self) -> None:
        service = self.buildService()
        userAgentStr = service.latest()
        self.assertIsInstance(userAgentStr, str)
        self.assertIn("Chrome/151.0.7922.10", userAgentStr)

    def testLatestCountReturnsRequestedNumberOfUserAgents(self) -> None:
        service = self.buildService()
        resultList = service.latest(5)
        self.assertEqual(5, len(resultList))
        self.assertTrue(all("Chrome/" in userAgentStr for userAgentStr in resultList))

    def testLatestCountLargerThanAvailableListIsSafe(self) -> None:
        service = self.buildService(versionList=["150.0.7871.46"])
        resultList = service.latest(999)
        self.assertLess(len(resultList), 999)
        self.assertGreater(len(resultList), 1)

    def testRandomReturnsValidUserAgentString(self) -> None:
        service = self.buildService()
        userAgentStr = service.random()
        self.assertIsInstance(userAgentStr, str)
        self.assertIn("Chrome/", userAgentStr)
        self.assertIn("Safari/537.36", userAgentStr)

    def testRandomDoesNotReturnSameUserAgentTwiceWhenAlternativesExist(self) -> None:
        service = self.buildService()
        firstUserAgentStr = service.random()
        secondUserAgentStr = service.random()
        self.assertNotEqual(firstUserAgentStr, secondUserAgentStr)

    def testRandomSavesLastUserAgentInKeyVal(self) -> None:
        keyValStore = FakeKeyValStoreProxy()
        service = self.buildService(keyValStore=keyValStore)
        userAgentStr = service.random()
        self.assertEqual(userAgentStr, keyValStore.store[KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR])

    def testRandomAppendsHistoryWhenFirebaseRealtimeBackendEnabled(self) -> None:
        previousBackendStr = os.environ.get(USER_AGENT_HISTORY_BACKEND_ENV_STR)
        os.environ[USER_AGENT_HISTORY_BACKEND_ENV_STR] = (
            USER_AGENT_HISTORY_FIREBASE_REALTIME_DATABASE_BACKEND_STR
        )
        historyProxy = FakeUserAgentHistoryProxy()
        try:
            service = self.buildService(
                firebaseRealtimeDatabaseHistoryProxy=historyProxy,
            )
            userAgentStr = service.random()
        finally:
            if previousBackendStr is None:
                os.environ.pop(USER_AGENT_HISTORY_BACKEND_ENV_STR, None)
            else:
                os.environ[USER_AGENT_HISTORY_BACKEND_ENV_STR] = previousBackendStr

        self.assertEqual(1, len(historyProxy.historyRecordList))
        self.assertEqual(userAgentStr, historyProxy.historyRecordList[0]["userAgent"])
        self.assertEqual("random", historyProxy.historyRecordList[0]["sourceMethod"])
        self.assertEqual(1, len(service.history()))

    def testRandomIgnoresHistoryPersistenceFailure(self) -> None:
        previousBackendStr = os.environ.get(USER_AGENT_HISTORY_BACKEND_ENV_STR)
        os.environ[USER_AGENT_HISTORY_BACKEND_ENV_STR] = (
            USER_AGENT_HISTORY_FIREBASE_REALTIME_DATABASE_BACKEND_STR
        )
        try:
            service = self.buildService(
                firebaseRealtimeDatabaseHistoryProxy=FakeUserAgentHistoryProxy(
                    shouldRaiseBool=True
                ),
            )
            userAgentStr = service.random()
        finally:
            if previousBackendStr is None:
                os.environ.pop(USER_AGENT_HISTORY_BACKEND_ENV_STR, None)
            else:
                os.environ[USER_AGENT_HISTORY_BACKEND_ENV_STR] = previousBackendStr

        self.assertIn("Chrome/", userAgentStr)
        self.assertEqual(1, len(service.history()))

    def testRandomSupportsReleaseChannelCountAndPlatformOptions(self) -> None:
        service = self.buildService(randomGenerator=FirstChoiceRandom())

        userAgentStr = service.random(
            releaseChannelList=["Stable", "Canary"],
            count=1,
            platformFamilyList=["Linux"],
        )

        self.assertIn("Chrome/152.0.7934.0", userAgentStr)
        self.assertIn("Linux", userAgentStr)
        self.assertNotIn("Windows NT", userAgentStr)

    def testRandomRejectsAmbiguousChannelOptions(self) -> None:
        service = self.buildService()

        with self.assertRaises(ValueError):
            service.random("Stable", releaseChannelList=["Beta"])

    def testServiceFallsBackToCachedKeyValDataWhenRemoteFails(self) -> None:
        cachedUserAgentStr = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/150.0.7871.46 Safari/537.36"
        )
        keyValStore = FakeKeyValStoreProxy(
            {
                "user_agent_pool_latest_user_agent_list": {
                    "userAgentList": [cachedUserAgentStr]
                }
            }
        )
        service = self.buildService(keyValStore=keyValStore, shouldRaiseBool=True)
        self.assertEqual(cachedUserAgentStr, service.latest())

    def testLatestVersionFallsBackToCachedKeyValDataWhenRemoteFails(self) -> None:
        cachedUserAgentStr = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/150.0.7871.46 Safari/537.36"
        )
        keyValStore = FakeKeyValStoreProxy(
            {
                "user_agent_pool_latest_user_agent_list": {
                    "userAgentList": [cachedUserAgentStr]
                }
            }
        )
        service = self.buildService(keyValStore=keyValStore, shouldRaiseBool=True)
        self.assertEqual("150.0.7871.46", service.latestVersion())

    def testInvalidRemoteResponsesRaiseWhenNoCacheExists(self) -> None:
        service = self.buildService(versionList=["invalid", "", None])
        with self.assertRaises(ChromeUserAgentPoolUnavailableError):
            service.latest()

    def testGeneratedUserAgentsContainValidChromeVersions(self) -> None:
        service = self.buildService()
        resultList = service.generateUserAgents(["150.0.7871.46"])
        self.assertTrue(resultList)
        self.assertTrue(
            all("Chrome/150.0.7871.46" in userAgentStr for userAgentStr in resultList)
        )

    def testLatestByChannelUsesChannelVersion(self) -> None:
        service = self.buildService()
        userAgentStr = service.latestByChannel("Canary")
        self.assertIn("Chrome/152.0.7934.0", userAgentStr)

    def testChannelVersionMapReturnsSupportedChannels(self) -> None:
        service = self.buildService()
        self.assertEqual(
            {
                "Stable": "150.0.7871.46",
                "Beta": "151.0.7922.10",
                "Dev": "151.0.7912.0",
                "Canary": "152.0.7934.0",
            },
            service.channelVersionMap(),
        )

    def testLatestRecordsTimingMetadata(self) -> None:
        service = self.buildService()
        service.latest()

        timingDict = service.lastTiming()
        self.assertIsNotNone(timingDict)
        self.assertEqual("latest", timingDict[TIMING_OPERATION_JSON_KEY_STR])
        self.assertTrue(timingDict[TIMING_SUCCESS_BOOL_JSON_KEY_STR])
        self.assertGreaterEqual(timingDict[TIMING_DURATION_SECOND_JSON_KEY_STR], 0)
        self.assertEqual(
            round(timingDict[TIMING_DURATION_SECOND_JSON_KEY_STR], 2),
            timingDict[TIMING_DURATION_SECOND_JSON_KEY_STR],
        )
        self.assertGreaterEqual(timingDict[TIMING_DURATION_MILLISECOND_JSON_KEY_STR], 0)

    def testRandomWithTimingReturnsResultAndTiming(self) -> None:
        service = self.buildService()
        resultDict = service.randomWithTiming()

        self.assertIn("Chrome/", resultDict[TIMING_RESULT_JSON_KEY_STR])
        self.assertEqual(
            "random",
            resultDict[TIMING_TIMING_JSON_KEY_STR][TIMING_OPERATION_JSON_KEY_STR],
        )

    def testTimingHistoryTracksEachGenerationCall(self) -> None:
        service = self.buildService()
        service.latest()
        service.random()
        service.latestByChannel("Stable")

        historyList = service.timingHistory()
        self.assertEqual(
            ["latest", "random", "latestByChannel"],
            [timingDict[TIMING_OPERATION_JSON_KEY_STR] for timingDict in historyList],
        )

    def testFailedCallRecordsErrorTiming(self) -> None:
        service = self.buildService(versionList=["invalid", "", None])

        with self.assertRaises(ChromeUserAgentPoolUnavailableError):
            service.latest()

        timingDict = service.lastTiming()
        self.assertFalse(timingDict[TIMING_SUCCESS_BOOL_JSON_KEY_STR])
        self.assertEqual(
            "ChromeUserAgentPoolUnavailableError",
            timingDict[TIMING_ERROR_TYPE_JSON_KEY_STR],
        )

    def testDebugLogsExplainRandomFlow(self) -> None:
        service = self.buildService()

        with self.assertLogs(CORE_LOGGER_NAME_STR, level="DEBUG") as logContext:
            service.random()

        logTextStr = "\n".join(logContext.output)
        self.assertIn("Random user-agent requested", logTextStr)
        self.assertIn("Chrome user-agent pool generated", logTextStr)
        self.assertIn("Last random Chrome user-agent Keyval save attempted", logTextStr)

    def testInfoLogsShowTimingAndKeyValUrl(self) -> None:
        service = self.buildService()

        with self.assertLogs(CORE_LOGGER_NAME_STR, level="INFO") as logContext:
            service.random()

        logTextStr = "\n".join(logContext.output)
        self.assertIn("Last random Chrome user-agent Keyval location", logTextStr)
        self.assertIn("https://api.keyval.org/get/fake-", logTextStr)
        self.assertIn("Operation completed operation=random", logTextStr)
        self.assertRegex(logTextStr, r"durationSecond=\d+\.\d{2}")


if __name__ == "__main__":
    unittest.main()
