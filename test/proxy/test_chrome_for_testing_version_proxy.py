import unittest

from core.proxy.chrome_for_testing_version_proxy import (
    ChromeForTestingVersionProxy,
    ChromeForTestingVersionProxyError,
)


class ChromeForTestingVersionProxyTest(unittest.TestCase):
    def testExtractChromeVersionListMapsBuildPayload(self) -> None:
        proxy = ChromeForTestingVersionProxy()
        resultList = proxy.extractChromeVersionList(
            {
                "builds": {
                    "150.0.7871": {"version": "150.0.7871.46", "revision": "1"},
                    "151.0.7922": {"version": "151.0.7922.10", "revision": "2"},
                }
            }
        )
        self.assertEqual(["150.0.7871.46", "151.0.7922.10"], resultList)

    def testExtractChromeVersionListRejectsMissingBuilds(self) -> None:
        proxy = ChromeForTestingVersionProxy()
        with self.assertRaises(ChromeForTestingVersionProxyError):
            proxy.extractChromeVersionList({})

    def testExtractChannelVersionMapMapsChannelPayload(self) -> None:
        proxy = ChromeForTestingVersionProxy()
        resultMap = proxy.extractChannelVersionMap(
            {
                "channels": {
                    "Stable": {"version": "150.0.7871.46"},
                    "Beta": {"version": "151.0.7922.10"},
                }
            }
        )
        self.assertEqual(
            {"Stable": "150.0.7871.46", "Beta": "151.0.7922.10"},
            resultMap,
        )


if __name__ == "__main__":
    unittest.main()
