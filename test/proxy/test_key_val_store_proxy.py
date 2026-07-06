import unittest

from core.constant.chrome_user_agent_pool_constant import KEY_VAL_DEFAULT_BASE_URL_STR
from core.helper.key_val_key_hash_helper import hashKeyValKey
from core.proxy.key_val_store_proxy import KeyValStoreProxy


class KeyValStoreProxyTest(unittest.TestCase):
    def testGetValueWithoutBaseUrlReturnsNone(self) -> None:
        proxy = KeyValStoreProxy(baseUrlStr="", authTokenStr="")
        self.assertIsNone(proxy.getValue("n_user_agent_pool_latest_user_agent_list"))

    def testSetValueWithoutBaseUrlReturnsFalse(self) -> None:
        proxy = KeyValStoreProxy(baseUrlStr="", authTokenStr="")
        self.assertFalse(proxy.setValue("n_user_agent_pool_latest_user_agent_list", "[]"))

    def testBuildKeyUrlUsesHashedKey(self) -> None:
        proxy = KeyValStoreProxy(baseUrlStr="https://keyval.example.invalid/store")
        keyStr = "n_user_agent_pool_last_random_user_agent"
        self.assertEqual(
            f"https://keyval.example.invalid/store/{hashKeyValKey(keyStr)}",
            proxy.buildKeyUrl(keyStr),
        )

    def testBuildSafeKeyUrlForLogRemovesQueryString(self) -> None:
        proxy = KeyValStoreProxy(
            baseUrlStr="https://keyval.example.invalid/store?token=secret"
        )
        keyStr = "n_user_agent_pool_last_random_user_agent"
        self.assertEqual(
            f"https://keyval.example.invalid/store/{hashKeyValKey(keyStr)}",
            proxy.buildSafeKeyUrlForLog(keyStr),
        )

    def testDefaultKeyValBuildsPublicGetUrl(self) -> None:
        proxy = KeyValStoreProxy(baseUrlStr=KEY_VAL_DEFAULT_BASE_URL_STR)
        keyStr = "n_user_agent_pool_last_random_user_agent"
        self.assertEqual(
            f"https://api.keyval.org/get/{hashKeyValKey(keyStr)}",
            proxy.buildGetUrl(keyStr),
        )
        self.assertEqual(
            f"https://api.keyval.org/get/{hashKeyValKey(keyStr)}",
            proxy.buildSafeGetUrlForLog(keyStr),
        )

    def testDefaultKeyValBuildsPublicSetUrlWithRedactedLogUrl(self) -> None:
        proxy = KeyValStoreProxy(baseUrlStr=KEY_VAL_DEFAULT_BASE_URL_STR)
        keyStr = "n_user_agent_pool_last_random_user_agent"
        self.assertEqual(
            f"https://api.keyval.org/set/{hashKeyValKey(keyStr)}/hello",
            proxy.buildSetUrl(keyStr, "hello"),
        )
        self.assertEqual(
            f"https://api.keyval.org/set/{hashKeyValKey(keyStr)}/<value-redacted>",
            proxy.buildSafeSetUrlForLog(keyStr),
        )

    def testDefaultKeyValBuildsChunkGetUrls(self) -> None:
        proxy = KeyValStoreProxy(baseUrlStr=KEY_VAL_DEFAULT_BASE_URL_STR)
        keyStr = "n_user_agent_pool_last_random_user_agent"
        self.assertEqual(
            [
                f"https://api.keyval.org/get/{hashKeyValKey(keyStr + '_chunk_0')}",
                f"https://api.keyval.org/get/{hashKeyValKey(keyStr + '_chunk_1')}",
            ],
            proxy.buildSafeChunkGetUrlListForLog(keyStr, 2),
        )


if __name__ == "__main__":
    unittest.main()
