import unittest

from core.repo.chrome_user_agent_pool_repo import ChromeUserAgentPoolRepo


class ChromeUserAgentPoolRepoTest(unittest.TestCase):
    def testRepoStoresUserAgentListCopy(self) -> None:
        repo = ChromeUserAgentPoolRepo()
        originalList = ["ua-1"]
        repo.saveUserAgentList(originalList)
        originalList.append("ua-2")
        self.assertEqual(["ua-1"], repo.getUserAgentList())

    def testRepoStoresLastRandomUserAgent(self) -> None:
        repo = ChromeUserAgentPoolRepo()
        repo.saveLastRandomUserAgent("ua")
        self.assertEqual("ua", repo.getLastRandomUserAgent())

    def testRepoStoresChannelVersionMapCopy(self) -> None:
        repo = ChromeUserAgentPoolRepo()
        versionMap = {"Stable": "150.0.7871.46"}
        repo.saveChannelVersionMap(versionMap)
        versionMap["Stable"] = "1.0.0.0"
        self.assertEqual({"Stable": "150.0.7871.46"}, repo.getChannelVersionMap())


if __name__ == "__main__":
    unittest.main()
