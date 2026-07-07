import unittest

from core.constant.chrome_user_agent_pool_constant import (
    CHROME_FOR_TESTING_LAST_KNOWN_GOOD_VERSION_URL_STR,
    CHROME_FOR_TESTING_LATEST_PATCH_VERSION_URL_STR,
    CHROME_RELEASE_CHANNEL_LIST,
    KEY_VAL_DEFAULT_BASE_URL_STR,
    KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR,
    KEY_VAL_PUBLIC_BASE_URL_STR,
    KEY_VAL_USER_AGENT_LIST_KEY_STR,
    PACKAGE_USER_AGENT_STR,
    SUPPORTED_DESKTOP_PLATFORM_FRAGMENT_BY_FAMILY_DICT,
)


class ChromeUserAgentPoolConstantTest(unittest.TestCase):
    def testChromeForTestingUrlsAreOfficial(self) -> None:
        self.assertIn(
            "googlechromelabs.github.io/chrome-for-testing",
            CHROME_FOR_TESTING_LATEST_PATCH_VERSION_URL_STR,
        )
        self.assertIn(
            "googlechromelabs.github.io/chrome-for-testing",
            CHROME_FOR_TESTING_LAST_KNOWN_GOOD_VERSION_URL_STR,
        )

    def testKeyValKeysAreDescriptive(self) -> None:
        self.assertIn("user_agent", KEY_VAL_USER_AGENT_LIST_KEY_STR)
        self.assertIn("last_random_user_agent", KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR)

    def testDefaultKeyValIsOptInAndPublicUrlIsExplicit(self) -> None:
        self.assertEqual("", KEY_VAL_DEFAULT_BASE_URL_STR)
        self.assertEqual("https://api.keyval.org", KEY_VAL_PUBLIC_BASE_URL_STR)

    def testPackageUserAgentMatchesProjectVersion(self) -> None:
        self.assertEqual("n-user-agent-pool/1.0.0", PACKAGE_USER_AGENT_STR)

    def testSupportedPlatformFamiliesCoverDesktopTargets(self) -> None:
        self.assertIn("Windows", SUPPORTED_DESKTOP_PLATFORM_FRAGMENT_BY_FAMILY_DICT)
        self.assertIn("macOS", SUPPORTED_DESKTOP_PLATFORM_FRAGMENT_BY_FAMILY_DICT)
        self.assertIn("Linux", SUPPORTED_DESKTOP_PLATFORM_FRAGMENT_BY_FAMILY_DICT)

    def testReleaseChannelsMatchChromeForTestingPage(self) -> None:
        self.assertEqual(["Stable", "Beta", "Dev", "Canary"], CHROME_RELEASE_CHANNEL_LIST)


if __name__ == "__main__":
    unittest.main()
