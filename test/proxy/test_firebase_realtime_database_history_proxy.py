import base64
import json
import unittest

from core.proxy.firebase_realtime_database_history_proxy import (
    FirebaseRealtimeDatabaseHistoryProxy,
)


class FirebaseRealtimeDatabaseHistoryProxyTest(unittest.TestCase):
    def buildCredentialBase64(self) -> str:
        return base64.b64encode(
            json.dumps({"accessToken": "placeholder-token"}).encode("utf-8")
        ).decode("utf-8")

    def buildHistoryRecord(self) -> dict[str, object]:
        return {
            "userAgent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/150.0.7871.46 Safari/537.36"
            ),
            "chromeVersion": "150.0.7871.46",
            "platformFamily": "Windows",
            "sourceMethod": "random",
            "createdAtUnixSecond": 1760000000,
        }

    def testMissingEnvDisablesFirebasePersistence(self) -> None:
        proxy = FirebaseRealtimeDatabaseHistoryProxy(
            credentialBase64Str="",
            databaseUrlStr="",
        )

        self.assertFalse(proxy.isConfigured())
        self.assertFalse(proxy.appendHistoryRecord(self.buildHistoryRecord()))

    def testBuildHistoryPayloadDoesNotExposeCredential(self) -> None:
        proxy = FirebaseRealtimeDatabaseHistoryProxy(
            credentialBase64Str=self.buildCredentialBase64(),
            databaseUrlStr="https://example-project-default-rtdb.firebaseio.com",
        )

        payloadDict = proxy.buildHistoryPayload(self.buildHistoryRecord())

        self.assertEqual("150.0.7871.46", payloadDict["chromeVersion"])
        self.assertNotIn("accessToken", payloadDict)
        self.assertNotIn("placeholder-token", json.dumps(payloadDict))

    def testBuildHistoryUrlUsesConfiguredDatabaseUrl(self) -> None:
        proxy = FirebaseRealtimeDatabaseHistoryProxy(
            credentialBase64Str=self.buildCredentialBase64(),
            databaseUrlStr="https://example-project-default-rtdb.firebaseio.com",
        )

        self.assertEqual(
            "https://example-project-default-rtdb.firebaseio.com/userAgentHistory.json",
            proxy.buildHistoryUrl(),
        )


if __name__ == "__main__":
    unittest.main()
