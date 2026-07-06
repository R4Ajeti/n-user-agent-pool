import unittest

from core.helper.user_agent_format_helper import (
    buildChromeUserAgent,
    extractChromeVersionFromUserAgent,
    getDesktopPlatformFamily,
    isValidChromeUserAgent,
)


class UserAgentFormatHelperTest(unittest.TestCase):
    def testBuildChromeUserAgentCreatesValidChromeString(self) -> None:
        userAgentStr = buildChromeUserAgent(
            "150.0.7871.46",
            "Windows NT 10.0; Win64; x64",
        )
        self.assertTrue(isValidChromeUserAgent(userAgentStr))
        self.assertIn("Chrome/150.0.7871.46", userAgentStr)

    def testBuildChromeUserAgentRejectsInvalidVersion(self) -> None:
        with self.assertRaises(ValueError):
            buildChromeUserAgent("latest", "X11; Linux x86_64")

    def testExtractChromeVersionFromUserAgent(self) -> None:
        userAgentStr = buildChromeUserAgent(
            "151.0.7922.10",
            "Macintosh; Intel Mac OS X 14_7_1",
        )
        self.assertEqual("151.0.7922.10", extractChromeVersionFromUserAgent(userAgentStr))

    def testGetDesktopPlatformFamily(self) -> None:
        self.assertEqual(
            "Windows",
            getDesktopPlatformFamily(
                buildChromeUserAgent("150.0.7871.46", "Windows NT 10.0; Win64; x64")
            ),
        )
        self.assertEqual(
            "macOS",
            getDesktopPlatformFamily(
                buildChromeUserAgent(
                    "150.0.7871.46",
                    "Macintosh; Intel Mac OS X 10_15_7",
                )
            ),
        )
        self.assertEqual(
            "Linux",
            getDesktopPlatformFamily(
                buildChromeUserAgent("150.0.7871.46", "X11; Linux x86_64")
            ),
        )


if __name__ == "__main__":
    unittest.main()
