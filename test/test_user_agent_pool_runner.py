import os
import unittest

from testUserAgentPool import runUserAgentPoolDiscovery


class FakeChromeUserAgentPoolRepo:
    def __init__(self, userAgentList=None) -> None:
        self.userAgentList = list(userAgentList or [])

    def getUserAgentList(self):
        return list(self.userAgentList)


class FakeChromeUserAgentPoolService:
    def __init__(self) -> None:
        self.cachedUserAgentList = [
            (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/150.0.7871.46 Safari/537.36"
            )
        ]
        self.selectedUserAgentStr = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/151.0.7922.10 Safari/537.36"
        )
        self.chromeUserAgentPoolRepo = FakeChromeUserAgentPoolRepo(
            [
                self.selectedUserAgentStr,
                self.cachedUserAgentList[0],
            ]
        )

    def getCachedUserAgents(self):
        return list(self.cachedUserAgentList)

    def random(self):
        return self.selectedUserAgentStr


class UserAgentPoolRunnerTest(unittest.TestCase):
    def testRunUserAgentPoolDiscoveryPrintsInfoStyleTranscript(self) -> None:
        previousLoggerStr = os.environ.get("LOGGER")
        os.environ["LOGGER"] = "INFO"
        outputList = []
        clockList = [10.0, 19.064]

        try:
            selectedUserAgentStr = runUserAgentPoolDiscovery(
                serviceFactory=FakeChromeUserAgentPoolService,
                outputFunc=outputList.append,
                perfCounterFunc=lambda: clockList.pop(0),
            )
        finally:
            if previousLoggerStr is None:
                os.environ.pop("LOGGER", None)
            else:
                os.environ["LOGGER"] = previousLoggerStr

        self.assertIn("Chrome/151.0.7922.10", selectedUserAgentStr)
        self.assertEqual("=== User-agent pool discovery run ===", outputList[0])
        self.assertRegex(outputList[1], r"^\[run\] hashed storage key: [a-f0-9]{64}$")
        self.assertEqual("[run] log level: INFO", outputList[2])
        self.assertEqual(
            "[run] note: KeyVal is public; credentials are never stored",
            outputList[3],
        )
        self.assertEqual("[cache] checking saved user-agent list", outputList[4])
        self.assertIn("[cache] usable saved user-agent:", outputList[5])
        self.assertIn("[run] selected user-agent:", outputList[6])
        self.assertEqual("[run] took 9.064 seconds", outputList[7])
        self.assertIn("Final selected user-agent:", outputList[8])
        self.assertIn("Ranked user-agent list:", outputList[9])


if __name__ == "__main__":
    unittest.main()
