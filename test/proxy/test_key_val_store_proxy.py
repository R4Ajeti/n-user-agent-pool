import unittest

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


if __name__ == "__main__":
    unittest.main()
