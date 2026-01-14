import unittest

from biobuddy.user import hash_password, verify_password


class TestHashPassword(unittest.TestCase):
    def test_hash_and_verify(self):
        password = "passw0rd"
        hashed = hash_password(password)
        print("Hashed password:", hashed)
        self.assertNotEqual(hashed, password)

        self.assertTrue(verify_password(hashed, password))
        self.assertFalse(verify_password(hashed, "wrong_password"))
