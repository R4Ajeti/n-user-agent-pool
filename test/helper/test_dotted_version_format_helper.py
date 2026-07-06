import unittest

from core.helper.dotted_version_format_helper import (
    getDottedVersionSortKey,
    isValidDottedVersion,
    sortDottedVersionList,
)


class DottedVersionFormatHelperTest(unittest.TestCase):
    def testValidDottedVersionRequiresChromeLikeParts(self) -> None:
        self.assertTrue(isValidDottedVersion("150.0.7871.46"))
        self.assertTrue(isValidDottedVersion("150.0.7871"))
        self.assertFalse(isValidDottedVersion("150"))
        self.assertFalse(isValidDottedVersion("latest"))
        self.assertFalse(isValidDottedVersion(""))

    def testSortDottedVersionListUsesNumericOrder(self) -> None:
        resultList = sortDottedVersionList(
            ["99.0.1.1", "150.0.7871.46", "149.0.8000.1"]
        )
        self.assertEqual(["150.0.7871.46", "149.0.8000.1", "99.0.1.1"], resultList)

    def testGetDottedVersionSortKeyRejectsInvalidVersion(self) -> None:
        with self.assertRaises(ValueError):
            getDottedVersionSortKey("not-a-version")


if __name__ == "__main__":
    unittest.main()
