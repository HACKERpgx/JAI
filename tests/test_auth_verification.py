import time
import unittest
from unittest.mock import patch

import jwt

import jai_auth


class SupabaseTokenVerificationTests(unittest.TestCase):
    secret = "test-only-signing-secret-with-sufficient-entropy"
    project_url = "https://project.example"

    def token(self, **overrides):
        now = int(time.time())
        claims = {
            "sub": "user-123",
            "aud": "authenticated",
            "iss": self.project_url + "/auth/v1",
            "iat": now,
            "exp": now + 300,
        }
        claims.update(overrides)
        return jwt.encode(claims, self.secret, algorithm="HS256")

    def verify(self, token, secret=None, url=None):
        with patch.object(jai_auth, "SUPABASE_JWT_SECRET", self.secret if secret is None else secret), patch.object(
            jai_auth, "SUPABASE_URL", self.project_url if url is None else url
        ):
            return jai_auth.verify_supabase_token(token)

    def test_accepts_valid_signed_token(self):
        self.assertEqual(self.verify(self.token())["sub"], "user-123")

    def test_fails_closed_without_signing_secret(self):
        self.assertIsNone(self.verify(self.token(), secret=""))

    def test_fails_closed_without_project_issuer(self):
        self.assertIsNone(self.verify(self.token(), url=""))

    def test_rejects_tampered_token(self):
        token = self.token()
        token = token[:-1] + ("A" if token[-1] != "A" else "B")
        self.assertIsNone(self.verify(token))

    def test_rejects_wrong_issuer(self):
        self.assertIsNone(self.verify(self.token(iss="https://attacker.example/auth/v1")))

    def test_rejects_expired_token(self):
        self.assertIsNone(self.verify(self.token(exp=int(time.time()) - 1)))

    def test_rejects_missing_subject(self):
        self.assertIsNone(self.verify(self.token(sub="")))


if __name__ == "__main__":
    unittest.main()
