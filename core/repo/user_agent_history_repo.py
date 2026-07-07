from __future__ import annotations

from collections.abc import Mapping


class UserAgentHistoryRepo:
    def __init__(self) -> None:
        self._historyRecordList: list[dict[str, object]] = []

    def appendHistoryRecord(self, historyRecordDict: Mapping[str, object]) -> None:
        self._historyRecordList.append(dict(historyRecordDict))

    def getHistoryRecordList(self, count: int | None = None) -> list[dict[str, object]]:
        if count is None:
            return [dict(historyRecordDict) for historyRecordDict in self._historyRecordList]

        if count <= 0:
            return []

        return [
            dict(historyRecordDict)
            for historyRecordDict in self._historyRecordList[-count:]
        ]
