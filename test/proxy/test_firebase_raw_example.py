import json
import unittest
from pathlib import Path


class FirebaseRawExampleTest(unittest.TestCase):
    def testFirebaseRawExampleJsonFilesAreValid(self) -> None:
        repoPath = Path(__file__).resolve().parents[2]
        filePathList = [
            repoPath / "raw/proxy/firebase_realtime_database_history_proxy/json/input.json",
            repoPath / "raw/proxy/firebase_realtime_database_history_proxy/json/output.json",
            repoPath / "raw/proxy/firebase_firestore_history_proxy/json/input.json",
            repoPath / "raw/proxy/firebase_firestore_history_proxy/json/output.json",
        ]

        for filePath in filePathList:
            with self.subTest(filePath=str(filePath)):
                with filePath.open("r", encoding="utf-8") as fileObject:
                    self.assertIsInstance(json.load(fileObject), dict)


if __name__ == "__main__":
    unittest.main()
