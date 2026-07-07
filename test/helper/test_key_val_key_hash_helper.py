import unittest

from core.constant.chrome_user_agent_pool_constant import KEY_VAL_KEY_HASH_ALGORITHM_STR
from core.helper.key_val_key_hash_helper import hashKeyValKey


class KeyValKeyHashHelperTest(unittest.TestCase):
    def testHashKeyValKeyIsConsistent(self) -> None:
        firstHashStr = hashKeyValKey("user_agent_pool_last_random_user_agent")
        secondHashStr = hashKeyValKey("user_agent_pool_last_random_user_agent")
        self.assertEqual(firstHashStr, secondHashStr)
        self.assertEqual(64, len(firstHashStr))

    def testHashKeyValKeyRejectsEmptyKey(self) -> None:
        with self.assertRaises(ValueError):
            hashKeyValKey("")

    def testHashKeyValKeyUsesConfiguredAlgorithm(self) -> None:
        resultStr = hashKeyValKey(
            "user_agent_pool_latest_user_agent_list",
            KEY_VAL_KEY_HASH_ALGORITHM_STR,
        )
        self.assertEqual(64, len(resultStr))

    def testHashKeyValKeyUsesNamespaceWhenProvided(self) -> None:
        plainHashStr = hashKeyValKey("user_agent_pool_latest_user_agent_list")
        namespacedHashStr = hashKeyValKey(
            "user_agent_pool_latest_user_agent_list",
            namespaceStr="unit-test",
        )
        self.assertNotEqual(plainHashStr, namespacedHashStr)
        self.assertEqual(namespacedHashStr, hashKeyValKey(
            "user_agent_pool_latest_user_agent_list",
            namespaceStr="unit-test",
        ))


if __name__ == "__main__":
    unittest.main()
