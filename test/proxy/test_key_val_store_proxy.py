import json
import unittest
from unittest.mock import patch

from core.constant.chrome_user_agent_pool_constant import (
    KEY_VAL_DEFAULT_BASE_URL_STR,
    KEY_VAL_PUBLIC_BASE_URL_STR,
)
from core.helper.key_val_key_hash_helper import hashKeyValKey
from core.proxy.key_val_store_proxy import KeyValStoreProxy


class FakeHttpResponse:
    def __init__(self, payloadStr: str) -> None:
        self.payloadStr = payloadStr

    def __enter__(self):
        return self

    def __exit__(self, excType, excValue, tracebackObject) -> None:
        return None

    def read(self) -> bytes:
        return self.payloadStr.encode("utf-8")


class RecordingPublicKeyValStoreProxy(KeyValStoreProxy):
    def __init__(self) -> None:
        super().__init__(
            baseUrlStr=KEY_VAL_PUBLIC_BASE_URL_STR,
            authTokenStr="",
            namespaceStr="unit-test",
        )
        self.valueByKeyDict: dict[str, str] = {}

    def setValue(self, keyStr: str, valueStr: str) -> bool:
        self.valueByKeyDict[keyStr] = valueStr
        return True

    def getValue(self, keyStr: str) -> str | None:
        return self.valueByKeyDict.get(keyStr)


class KeyValStoreProxyTest(unittest.TestCase):
    def testGetValueWithoutBaseUrlReturnsNone(self) -> None:
        proxy = KeyValStoreProxy(baseUrlStr="", authTokenStr="")
        self.assertIsNone(proxy.getValue("user_agent_pool_latest_user_agent_list"))

    def testSetValueWithoutBaseUrlReturnsFalse(self) -> None:
        proxy = KeyValStoreProxy(baseUrlStr="", authTokenStr="")
        self.assertFalse(proxy.setValue("user_agent_pool_latest_user_agent_list", "[]"))

    def testBuildKeyUrlUsesHashedKey(self) -> None:
        proxy = KeyValStoreProxy(baseUrlStr="https://keyval.example.invalid/store")
        keyStr = "user_agent_pool_last_random_user_agent"
        self.assertEqual(
            f"https://keyval.example.invalid/store/{hashKeyValKey(keyStr)}",
            proxy.buildKeyUrl(keyStr),
        )

    def testBuildSafeKeyUrlForLogRemovesQueryString(self) -> None:
        proxy = KeyValStoreProxy(
            baseUrlStr="https://keyval.example.invalid/store?token=fake-token"
        )
        keyStr = "user_agent_pool_last_random_user_agent"
        self.assertEqual(
            f"https://keyval.example.invalid/store/{hashKeyValKey(keyStr)}",
            proxy.buildSafeKeyUrlForLog(keyStr),
        )

    def testDefaultKeyValBaseUrlIsDisabled(self) -> None:
        proxy = KeyValStoreProxy(baseUrlStr=KEY_VAL_DEFAULT_BASE_URL_STR)
        self.assertFalse(proxy.baseUrlStr)

    def testPublicKeyValBuildsNamespacedPublicGetUrl(self) -> None:
        namespaceStr = "unit-test"
        proxy = KeyValStoreProxy(
            baseUrlStr=KEY_VAL_PUBLIC_BASE_URL_STR,
            namespaceStr=namespaceStr,
        )
        keyStr = "user_agent_pool_last_random_user_agent"
        hashedKeyStr = hashKeyValKey(keyStr, namespaceStr=namespaceStr)
        self.assertEqual(
            f"https://api.keyval.org/get/{hashedKeyStr}",
            proxy.buildGetUrl(keyStr),
        )
        self.assertEqual(
            f"https://api.keyval.org/get/{hashedKeyStr}",
            proxy.buildSafeGetUrlForLog(keyStr),
        )

    def testPublicKeyValBuildsPostSetUrlForSafeLog(self) -> None:
        proxy = KeyValStoreProxy(
            baseUrlStr=KEY_VAL_PUBLIC_BASE_URL_STR,
            namespaceStr="unit-test",
        )
        keyStr = "user_agent_pool_last_random_user_agent"
        self.assertEqual(
            "https://api.keyval.org/set",
            proxy.buildSetUrl(keyStr, "hello"),
        )
        self.assertEqual(
            "https://api.keyval.org/set",
            proxy.buildSafeSetUrlForLog(keyStr),
        )

    def testPublicKeyValBuildsNamespacedChunkGetUrls(self) -> None:
        namespaceStr = "unit-test"
        proxy = KeyValStoreProxy(
            baseUrlStr=KEY_VAL_PUBLIC_BASE_URL_STR,
            namespaceStr=namespaceStr,
        )
        keyStr = "user_agent_pool_last_random_user_agent"
        self.assertEqual(
            [
                f"https://api.keyval.org/get/{hashKeyValKey(keyStr + '_chunk_0', namespaceStr=namespaceStr)}",
                f"https://api.keyval.org/get/{hashKeyValKey(keyStr + '_chunk_1', namespaceStr=namespaceStr)}",
            ],
            proxy.buildSafeChunkGetUrlListForLog(keyStr, 2),
        )

    @patch("core.proxy.key_val_store_proxy.urlopen")
    def testPublicKeyValWithoutNamespaceDoesNotCallHttp(self, urlOpenMock) -> None:
        proxy = KeyValStoreProxy(baseUrlStr=KEY_VAL_PUBLIC_BASE_URL_STR, namespaceStr="")
        self.assertIsNone(proxy.getValue("user_agent_pool_last_random_user_agent"))
        self.assertFalse(proxy.setValue("user_agent_pool_last_random_user_agent", "hello"))
        urlOpenMock.assert_not_called()

    @patch("core.proxy.key_val_store_proxy.urlopen")
    def testPublicSetValueUsesPostSetApiWithJsonBody(self, urlOpenMock) -> None:
        namespaceStr = "unit-test"
        urlOpenMock.return_value = FakeHttpResponse('{"status":"SUCCESS"}')
        proxy = KeyValStoreProxy(
            baseUrlStr=KEY_VAL_PUBLIC_BASE_URL_STR,
            namespaceStr=namespaceStr,
        )
        keyStr = "user_agent_pool_last_random_user_agent"

        self.assertTrue(proxy.setValue(keyStr, "hello"))

        requestObject = urlOpenMock.call_args.args[0]
        payloadDict = json.loads(requestObject.data.decode("utf-8"))
        self.assertEqual("https://api.keyval.org/set", requestObject.full_url)
        self.assertEqual("POST", requestObject.get_method())
        self.assertEqual(hashKeyValKey(keyStr, namespaceStr=namespaceStr), payloadDict["key"])
        self.assertEqual("hello", payloadDict["val"])

    def testPublicJsonSaveAndReadUsesChunksForLargePayload(self) -> None:
        proxy = RecordingPublicKeyValStoreProxy()
        keyStr = "user_agent_pool_latest_user_agent_list"
        payloadDict = {"userAgentList": ["x" * 180]}

        self.assertTrue(proxy.setJson(keyStr, payloadDict))

        self.assertEqual("chunked:3", proxy.valueByKeyDict[keyStr])
        self.assertEqual(payloadDict, proxy.getJson(keyStr))


if __name__ == "__main__":
    unittest.main()
