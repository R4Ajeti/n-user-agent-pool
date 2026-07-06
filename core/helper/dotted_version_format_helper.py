from __future__ import annotations

import re
from collections.abc import Iterable


def isValidDottedVersion(value: object) -> bool:
    if not isinstance(value, str):
        return False

    return re.fullmatch(r"\d+(?:\.\d+){2,3}", value.strip()) is not None


def getDottedVersionSortKey(versionStr: str) -> tuple[int, int, int, int]:
    if not isValidDottedVersion(versionStr):
        raise ValueError(f"Invalid dotted version: {versionStr!r}")

    partList = [int(partStr) for partStr in versionStr.strip().split(".")]
    paddedPartList = partList + [0] * (4 - len(partList))
    return tuple(paddedPartList[:4])


def uniqueValidDottedVersionList(versionList: Iterable[object]) -> list[str]:
    seenVersionSet: set[str] = set()
    cleanVersionList: list[str] = []

    for version in versionList:
        if not isinstance(version, str):
            continue

        versionStr = version.strip()
        if not isValidDottedVersion(versionStr):
            continue

        if versionStr in seenVersionSet:
            continue

        seenVersionSet.add(versionStr)
        cleanVersionList.append(versionStr)

    return cleanVersionList


def sortDottedVersionList(
    versionList: Iterable[object],
    reverseBool: bool = True,
) -> list[str]:
    cleanVersionList = uniqueValidDottedVersionList(versionList)
    return sorted(cleanVersionList, key=getDottedVersionSortKey, reverse=reverseBool)
