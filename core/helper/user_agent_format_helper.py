from __future__ import annotations

import re

from core.constant.chrome_user_agent_pool_constant import CHROME_USER_AGENT_TEMPLATE_STR
from core.helper.dotted_version_format_helper import isValidDottedVersion


def buildChromeUserAgent(chromeVersionStr: str, platformFragmentStr: str) -> str:
    if not isValidDottedVersion(chromeVersionStr):
        raise ValueError(f"Invalid Chrome version: {chromeVersionStr!r}")

    if not isinstance(platformFragmentStr, str) or not platformFragmentStr.strip():
        raise ValueError("Platform fragment must be a non-empty string.")

    return CHROME_USER_AGENT_TEMPLATE_STR.format(
        platformFragment=platformFragmentStr.strip(),
        chromeVersion=chromeVersionStr.strip(),
    )


def extractChromeVersionFromUserAgent(userAgentStr: str) -> str | None:
    if not isinstance(userAgentStr, str):
        return None

    matchObject = re.search(r"\bChrome/(\d+(?:\.\d+){2,3})\b", userAgentStr)
    if matchObject is None:
        return None

    versionStr = matchObject.group(1)
    if not isValidDottedVersion(versionStr):
        return None

    return versionStr


def isValidChromeUserAgent(userAgentStr: object) -> bool:
    if not isinstance(userAgentStr, str):
        return False

    cleanUserAgentStr = userAgentStr.strip()
    versionStr = extractChromeVersionFromUserAgent(cleanUserAgentStr)
    if versionStr is None:
        return False

    requiredPartList = [
        "Mozilla/5.0",
        "AppleWebKit/537.36",
        "(KHTML, like Gecko)",
        "Safari/537.36",
    ]
    return all(partStr in cleanUserAgentStr for partStr in requiredPartList)


def getDesktopPlatformFamily(userAgentStr: str) -> str:
    if not isinstance(userAgentStr, str):
        return "Unknown"

    if "Windows NT" in userAgentStr:
        return "Windows"

    if "Macintosh;" in userAgentStr:
        return "macOS"

    if "Linux" in userAgentStr or "X11;" in userAgentStr:
        return "Linux"

    return "Unknown"
