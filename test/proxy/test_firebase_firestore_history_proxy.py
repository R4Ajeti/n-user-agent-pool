import base64
import json
import unittest

from core.proxy.firebase_firestore_history_proxy import FirebaseFirestoreHistoryProxy


class FirebaseFirestoreHistoryProxyTest(unittest.TestCase):
    def buildCredentialBase64(self) -> str:
        return base64.b64encode(
            json.dumps({"accessToken": "placeholder-token"}).encode("utf-8")
        ).decode("utf-8")

    def buildHistoryRecord(self) -> dict[str, object]:
        return {
            "userAgent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/150.0.7871.46 Safari/537.36"
            ),
            "chromeVersion": "150.0.7871.46",
            "platformFamily": "Linux",
            "sourceMethod": "random",
            "createdAtUnixSecond": 1760000000,
        }

    def testMissingEnvDisablesFirebasePersistence(self) -> None:
        proxy = FirebaseFirestoreHistoryProxy(
            credentialBase64Str="",
            projectIdStr="",
        )

        self.assertFalse(proxy.isConfigured())
        self.assertFalse(proxy.appendHistoryRecord(self.buildHistoryRecord()))

    def testBuildHistoryDocumentPayloadDoesNotExposeCredential(self) -> None:
        proxy = FirebaseFirestoreHistoryProxy(
            credentialBase64Str=self.buildCredentialBase64(),
            projectIdStr="example-project",
        )

        payloadDict = proxy.buildHistoryDocumentPayload(self.buildHistoryRecord())

        self.assertEqual(
            "150.0.7871.46",
            payloadDict["fields"]["chromeVersion"]["stringValue"],
        )
        self.assertEqual(
            "1760000000",
            payloadDict["fields"]["createdAtUnixSecond"]["integerValue"],
        )
        self.assertNotIn("accessToken", payloadDict["fields"])
        self.assertNotIn("placeholder-token", json.dumps(payloadDict))

    def testBuildHistoryDocumentUrlUsesProjectId(self) -> None:
        proxy = FirebaseFirestoreHistoryProxy(
            credentialBase64Str=self.buildCredentialBase64(),
            projectIdStr="example-project",
        )

        self.assertEqual(
            "https://firestore.googleapis.com/v1/projects/example-project/databases/(default)/documents/userAgentHistory",
            proxy.buildHistoryDocumentUrl(),
        )


if __name__ == "__main__":
    unittest.main()
