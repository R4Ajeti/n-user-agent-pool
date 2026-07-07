import base64
import json
import unittest

from core.helper.base64_json_decode_helper import decodeBase64JsonObject


class Base64JsonDecodeHelperTest(unittest.TestCase):
    def testDecodeBase64JsonObjectReturnsDict(self) -> None:
        encodedValueStr = base64.b64encode(
            json.dumps({"accessToken": "placeholder-token"}).encode("utf-8")
        ).decode("utf-8")

        self.assertEqual(
            {"accessToken": "placeholder-token"},
            decodeBase64JsonObject(encodedValueStr),
        )

    def testDecodeBase64JsonObjectRejectsInvalidBase64(self) -> None:
        with self.assertRaises(ValueError):
            decodeBase64JsonObject("not-base64")

    def testDecodeBase64JsonObjectRejectsNonObjectJson(self) -> None:
        encodedValueStr = base64.b64encode(b'["not", "object"]').decode("utf-8")

        with self.assertRaises(ValueError):
            decodeBase64JsonObject(encodedValueStr)


if __name__ == "__main__":
    unittest.main()
