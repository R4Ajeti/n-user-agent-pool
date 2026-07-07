import unittest

from core.repo.user_agent_history_repo import UserAgentHistoryRepo


class UserAgentHistoryRepoTest(unittest.TestCase):
    def testAppendAndReadHistoryRecords(self) -> None:
        repo = UserAgentHistoryRepo()
        repo.appendHistoryRecord({"userAgent": "first"})
        repo.appendHistoryRecord({"userAgent": "second"})

        self.assertEqual(
            [{"userAgent": "first"}, {"userAgent": "second"}],
            repo.getHistoryRecordList(),
        )
        self.assertEqual(
            [{"userAgent": "second"}],
            repo.getHistoryRecordList(1),
        )


if __name__ == "__main__":
    unittest.main()
