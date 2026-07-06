import random
import unittest

from core.constant.chrome_user_agent_pool_constant import (
    KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR,
    USER_AGENT_JSON_KEY_STR,
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


class ChromeUserAgentPoolServiceTest(unittest.TestCase):
    def buildService(self, versionList=None, keyValStore=None, shouldRaiseBool=False):
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
            randomGenerator=random.Random(7),
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
        self.assertEqual(
            userAgentStr,
            keyValStore.store[KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR][
                USER_AGENT_JSON_KEY_STR
            ],
        )

    def testServiceFallsBackToCachedKeyValDataWhenRemoteFails(self) -> None:
        cachedUserAgentStr = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/150.0.7871.46 Safari/537.36"
        )
        keyValStore = FakeKeyValStoreProxy(
            {
                "n_user_agent_pool_latest_user_agent_list": {
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
                "n_user_agent_pool_latest_user_agent_list": {
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


if __name__ == "__main__":
    unittest.main()
