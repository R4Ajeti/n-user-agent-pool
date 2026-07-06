import os
import unittest

from core.service.verbose_chrome_user_agent_pool_service import (
    VerboseChromeUserAgentPoolService,
)


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
        self.randomCallDict = None
        self.candidateCallDict = None

    def getCachedUserAgents(self):
        return list(self.cachedUserAgentList)

    def random(
        self,
        channelStr=None,
        count=None,
        platformFamilyList=None,
        releaseChannelList=None,
    ):
        self.randomCallDict = {
            "channelStr": channelStr,
            "count": count,
            "platformFamilyList": platformFamilyList,
            "releaseChannelList": releaseChannelList,
        }
        return self.selectedUserAgentStr

    def getRandomCandidateUserAgentList(
        self,
        releaseChannelList=None,
        count=None,
        platformFamilyList=None,
    ):
        self.candidateCallDict = {
            "releaseChannelList": releaseChannelList,
            "count": count,
            "platformFamilyList": platformFamilyList,
        }
        return [
            self.selectedUserAgentStr,
            self.cachedUserAgentList[0],
        ]


class VerboseChromeUserAgentPoolServiceTest(unittest.TestCase):
    def testRunSetsFinalValueAndRankedUserAgentList(self) -> None:
        previousLoggerStr = os.environ.get("LOGGER")
        os.environ["LOGGER"] = "INFO"
        outputList = []
        clockList = [10.0, 19.064]

        try:
            service = VerboseChromeUserAgentPoolService(
                chromeUserAgentPoolService=FakeChromeUserAgentPoolService(),
                outputFunc=outputList.append,
                perfCounterFunc=lambda: clockList.pop(0),
            )
            resultStr = service.run()
        finally:
            if previousLoggerStr is None:
                os.environ.pop("LOGGER", None)
            else:
                os.environ["LOGGER"] = previousLoggerStr

        self.assertEqual(service.finalValueStr, resultStr)
        self.assertIn("Chrome/151.0.7922.10", service.finalValueStr)
        self.assertEqual(2, len(service.rankedUserAgentList))
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

    def testRunAcceptsRandomOptionParameters(self) -> None:
        outputList = []
        fakePoolService = FakeChromeUserAgentPoolService()
        clockList = [10.0, 10.5]
        service = VerboseChromeUserAgentPoolService(
            chromeUserAgentPoolService=fakePoolService,
            outputFunc=outputList.append,
            perfCounterFunc=lambda: clockList.pop(0),
        )

        resultStr = service.run(
            releaseChannelList=["Stable", "Canary"],
            count=2,
            platformFamilyList=["Linux"],
            rankedCount=2,
        )

        self.assertEqual(fakePoolService.selectedUserAgentStr, resultStr)
        self.assertEqual(
            {
                "channelStr": None,
                "count": 2,
                "platformFamilyList": ["Linux"],
                "releaseChannelList": ["Stable", "Canary"],
            },
            fakePoolService.randomCallDict,
        )
        self.assertEqual(
            {
                "releaseChannelList": ["Stable", "Canary"],
                "count": 2,
                "platformFamilyList": ["Linux"],
            },
            fakePoolService.candidateCallDict,
        )
        self.assertEqual(2, len(service.rankedUserAgentList))
        self.assertIn(
            "[run] options: releaseChannels=Stable|Canary, count=2, platformFamilies=Linux, rankedCount=2",
            outputList,
        )


if __name__ == "__main__":
    unittest.main()
