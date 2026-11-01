import unittest
from unittest.mock import MagicMock, patch

import byok_service as service
from byok_service import (
    ByokError,
    active_subscription,
    gemini_chat,
    gemini_generate_content,
    get_model_request_config,
    get_provider,
    model_request_context,
    request_model_config_from_headers,
    validate_api_key_format,
    validate_model_id,
)


class ByokServiceTests(unittest.TestCase):
    def test_provider_endpoints_are_fixed(self):
        self.assertEqual(get_provider("openai").base_url, "https://api.openai.com/v1")
        self.assertEqual(get_provider("openrouter").base_url, "https://openrouter.ai/api/v1")
        self.assertEqual(get_provider("gemini").base_url, "https://generativelanguage.googleapis.com/v1beta")
        with self.assertRaises(ByokError):
            get_provider("https://attacker.example")

    def test_model_ids_are_validated_per_provider(self):
        self.assertEqual(validate_model_id("openai/gpt-4o-mini", "openrouter"), "openai/gpt-4o-mini")
        self.assertEqual(validate_model_id("", "gemini"), "gemini-3.8-flash")
        for value in ("https://attacker.example", "model?x=1", "model with spaces", "../secret"):
            with self.subTest(value=value), self.assertRaises(ByokError):
                validate_model_id(value, "openai")
        with self.assertRaises(ByokError):
            validate_model_id("models/../../attacker", "gemini")

    def test_api_key_format_rejects_short_or_whitespace_keys(self):
        self.assertEqual(validate_api_key_format("  sk-example-key-123456789  "), "sk-example-key-123456789")
        for value in ("short", "sk-example key with spaces"):
            with self.subTest(value=value), self.assertRaises(ByokError):
                validate_api_key_format(value)

    def test_request_headers_produce_ephemeral_provider_config(self):
        headers = {
            "x-jai-provider": "openrouter",
            "x-jai-api-key": "sk-or-example-key-123456789",
            "x-jai-model": "openai/gpt-4o-mini",
        }
        config = request_model_config_from_headers(headers)
        self.assertEqual(config["provider"], "openrouter")
        self.assertEqual(config["base_url"], "https://openrouter.ai/api/v1")
        self.assertEqual(config["model"], "openai/gpt-4o-mini")
        self.assertEqual(config["api_key"], headers["x-jai-api-key"])
        self.assertIsNone(request_model_config_from_headers({}))
        with self.assertRaises(ByokError):
            request_model_config_from_headers({"x-jai-provider": "openai"})

    def test_request_model_config_is_scoped_and_reset(self):
        self.assertIsNone(get_model_request_config())
        config = {"provider": "openai", "api_key": "user-key", "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"}
        with self.assertRaisesRegex(RuntimeError, "expected"):
            with model_request_context(config):
                self.assertEqual(get_model_request_config(), config)
                raise RuntimeError("expected")
        self.assertIsNone(get_model_request_config())

    def test_gemini_request_uses_fixed_url_and_key_header(self):
        fake_response = MagicMock(status_code=200)
        fake_response.json.return_value = {"candidates": [{"content": {"parts": [{"text": "Hello from Gemini"}]}}]}
        fake_client = MagicMock()
        fake_client.post.return_value = fake_response
        client_context = MagicMock()
        client_context.__enter__.return_value = fake_client
        client_context.__exit__.return_value = False
        config = {"provider": "gemini", "api_key": "AIza-example-key-123456789", "model": "gemini-3.8-flash"}

        with patch.object(service.httpx, "Client", return_value=client_context):
            answer = gemini_generate_content(config, [{"role": "user", "parts": [{"text": "Hi"}]}])

        self.assertEqual(answer, "Hello from Gemini")
        kwargs = fake_client.post.call_args.kwargs
        self.assertEqual(fake_client.post.call_args.args[0], "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent")
        self.assertEqual(kwargs["headers"]["x-goog-api-key"], config["api_key"])
        self.assertNotIn("key=", fake_client.post.call_args.args[0])

    def test_gemini_chat_maps_system_and_user_messages(self):
        config = {"provider": "gemini", "api_key": "AIza-example-key-123456789", "model": "gemini-3.8-flash"}
        with patch.object(service, "gemini_generate_content", return_value="Hi") as call:
            result = gemini_chat(config, [
                {"role": "system", "content": "Be concise."},
                {"role": "user", "content": "Hello"},
            ])
        self.assertEqual(result, "Hi")
        self.assertEqual(call.call_args.kwargs["system_instruction"], "Be concise.")
        self.assertEqual(call.call_args.args[1], [{"role": "user", "parts": [{"text": "Hello"}]}])

    def test_only_active_and_trialing_subscriptions_are_entitled(self):
        self.assertTrue(active_subscription({"status": "active"}))
        self.assertTrue(active_subscription({"status": "trialing"}))
        for status in (None, "inactive", "canceled", "past_due", "unpaid"):
            self.assertFalse(active_subscription({"status": status}))
        self.assertFalse(active_subscription(None))


if __name__ == "__main__":
    unittest.main()
