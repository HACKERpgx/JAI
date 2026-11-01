import os
import unittest
from unittest.mock import AsyncMock, patch

import main
from jai_auth import User
from starlette.requests import Request


class ByokApiTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user = User(id="11111111-1111-4111-8111-111111111111", email="user@example.com", user_metadata={})
        self.patchers = []

    def tearDown(self):
        for patcher in reversed(self.patchers):
            patcher.stop()

    def patch_attr(self, target, name, value):
        patcher = patch.object(target, name, value)
        patcher.start()
        self.patchers.append(patcher)
        return value

    @staticmethod
    def make_request(provider="openai", model="gpt-4o-mini", key="sk-user-secret-abcdefgh"):
        headers = [
            (b"x-jai-provider", provider.encode()),
            (b"x-jai-model", model.encode()),
            (b"x-jai-api-key", key.encode()),
        ]
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "https",
            "path": "/api/byok/test",
            "raw_path": b"/api/byok/test",
            "query_string": b"",
            "headers": headers,
            "server": ("jai.test", 443),
            "client": ("test", 1234),
        }
        return Request(scope)

    async def test_key_test_is_stateless_and_never_returns_or_persists_key(self):
        validator = self.patch_attr(main, "validate_provider_key", AsyncMock())
        request = self.make_request()

        result = await main.test_byok_key(request, self.user)

        self.assertEqual(result, {
            "ok": True,
            "provider": "openai",
            "model": "gpt-4o-mini",
            "masked_key": "••••efgh",
        })
        self.assertNotIn("sk-user-secret-abcdefgh", str(result))
        validator.assert_awaited_once_with("openai", "sk-user-secret-abcdefgh")
        self.assertFalse(hasattr(main.BYOK_STORE, "save_provider_key"))

    async def test_settings_returns_provider_options_and_subscription_only(self):
        store = main.BYOK_STORE
        self.patch_attr(store, "get_subscription", AsyncMock(return_value={"status": "active", "stripe_customer_id": "cus_private"}))

        result = await main.get_byok_settings(self.user)

        self.assertEqual({item["id"] for item in result["providers"]}, {"openai", "openrouter", "gemini"})
        self.assertEqual(result["key_storage"], "this_browser_only")
        self.assertTrue(result["subscription"]["active"])
        self.assertNotIn("cus_private", str(result))
        self.assertNotIn("api_key", str(result))
        self.assertNotIn("key_ciphertext", str(result))

    async def test_missing_or_invalid_provider_headers_fail_before_validation(self):
        validator = self.patch_attr(main, "validate_provider_key", AsyncMock())
        request = self.make_request(provider="not-a-provider")

        response = await main.test_byok_key(request, self.user)

        self.assertEqual(response.status_code, 400)
        self.assertIn("unsupported_provider", response.body.decode())
        validator.assert_not_awaited()

    def test_subscription_gate_protects_ai_and_key_test_but_keeps_management_open(self):
        with patch.dict(os.environ, {"JAI_REQUIRE_ACTIVE_SUBSCRIPTION": "true"}):
            self.assertTrue(main.subscription_required_for_request("/api/text", "POST"))
            self.assertTrue(main.subscription_required_for_request("/api/image", "POST"))
            self.assertTrue(main.subscription_required_for_request("/api/byok/test", "POST"))
            self.assertFalse(main.subscription_required_for_request("/api/auth/config", "GET"))
            self.assertFalse(main.subscription_required_for_request("/api/byok/settings", "GET"))
            self.assertFalse(main.subscription_required_for_request("/api/billing/webhook", "POST"))
            self.assertFalse(main.subscription_required_for_request("/api/health", "GET"))
            self.assertFalse(main.subscription_required_for_request("/api/logout", "POST"))
            self.assertFalse(main.subscription_required_for_request("/", "GET"))


if __name__ == "__main__":
    unittest.main()
