from __future__ import annotations


class ChromeUserAgentPoolRepo:
    def __init__(self) -> None:
        self._userAgentList: list[str] = []
        self._lastRandomUserAgentStr: str | None = None
        self._channelVersionMap: dict[str, str] = {}
        self._callTimingList: list[dict[str, object]] = []

    def saveUserAgentList(self, userAgentList: list[str]) -> None:
        self._userAgentList = list(userAgentList)

    def getUserAgentList(self) -> list[str]:
        return list(self._userAgentList)

    def saveLastRandomUserAgent(self, userAgentStr: str) -> None:
        self._lastRandomUserAgentStr = userAgentStr

    def getLastRandomUserAgent(self) -> str | None:
        return self._lastRandomUserAgentStr

    def saveChannelVersionMap(self, channelVersionMap: dict[str, str]) -> None:
        self._channelVersionMap = dict(channelVersionMap)

    def getChannelVersionMap(self) -> dict[str, str]:
        return dict(self._channelVersionMap)

    def saveCallTiming(self, callTimingDict: dict[str, object]) -> None:
        self._callTimingList.append(dict(callTimingDict))

    def getLastCallTiming(self) -> dict[str, object] | None:
        if not self._callTimingList:
            return None

        return dict(self._callTimingList[-1])

    def getCallTimingList(self) -> list[dict[str, object]]:
        return [dict(callTimingDict) for callTimingDict in self._callTimingList]
