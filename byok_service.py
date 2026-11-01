"""Stateless BYOK provider helpers and subscription persistence for JAI.

Provider credentials are supplied by the browser per request. This module never
persists them; only subscription state is stored in Supabase.
"""
from __future__ import annotations

import contextvars
import os
import re
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

import httpx


@dataclass(frozen=True)
class Provider:
    id: str
    label: str
    base_url: str
    models_url: str
    default_model: str


PROVIDERS: dict[str, Provider] = {
    "openai": Provider(
        id="openai",
        label="OpenAI",
        base_url="https://api.openai.com/v1",
        models_url="https://api.openai.com/v1/models",
        default_model="gpt-4o-mini",
    ),
    "openrouter": Provider(
        id="openrouter",
        label="OpenRouter",
        base_url="https://openrouter.ai/api/v1",
        models_url="https://openrouter.ai/api/v1/models",
        default_model="openai/gpt-4o-mini",
    ),
    "gemini": Provider(
        id="gemini",
        label="Google Gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        models_url="https://generativelanguage.googleapis.com/v1beta/models",
        default_model="gemini-3.8-flash",
    ),
}

_MODEL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")
_ACTIVE_MODEL_CONFIG: contextvars.ContextVar[dict[str, str] | None] = contextvars.ContextVar(
    "jai_active_model_config", default=None
)


class ByokError(Exception):
    """A safe, user-presentable BYOK or billing error."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@contextmanager
def model_request_context(config: dict[str, str] | None) -> Iterator[None]:
    """Set provider configuration for this request only; never use shared globals."""
    token = _ACTIVE_MODEL_CONFIG.set(config)
    try:
        yield
    finally:
        _ACTIVE_MODEL_CONFIG.reset(token)


def get_model_request_config() -> dict[str, str] | None:
    return _ACTIVE_MODEL_CONFIG.get()


def get_provider(provider_id: str) -> Provider:
    provider = PROVIDERS.get((provider_id or "").strip().lower())
    if not provider:
        raise ByokError("unsupported_provider", "Choose OpenAI, OpenRouter, or Google Gemini.")
    return provider


def validate_model_id(model: str, provider_id: str) -> str:
    value = (model or "").strip()
    if not value:
        return get_provider(provider_id).default_model
    provider = get_provider(provider_id)
    path_segments = value.split("/")
    if (
        not _MODEL_ID.fullmatch(value)
        or (provider.id == "gemini" and "/" in value)
        or any(segment in {"", ".", ".."} for segment in path_segments)
    ):
        raise ByokError("invalid_model", "Enter a valid model ID (up to 128 letters, digits, dots, underscores, slashes, or hyphens).")
    return value


def validate_api_key_format(api_key: str) -> str:
    key = (api_key or "").strip()
    if not 16 <= len(key) <= 4096 or any(ch.isspace() for ch in key):
        raise ByokError("invalid_api_key", "Enter a valid provider API key without spaces.")
    return key


def request_model_config_from_headers(headers: Any) -> dict[str, str] | None:
    """Read a one-request credential from the browser-supplied headers."""
    provider_id = headers.get("x-jai-provider", "").strip().lower()
    api_key = headers.get("x-jai-api-key", "")
    model = headers.get("x-jai-model", "")
    if not provider_id and not api_key and not model:
        return None
    if not provider_id or not api_key:
        raise ByokError("provider_key_required", "Choose a provider and connect its API key in AI Settings.", 409)
    provider = get_provider(provider_id)
    key = validate_api_key_format(api_key)
    return {
        "provider": provider.id,
        "api_key": key,
        "base_url": provider.base_url,
        "model": validate_model_id(model, provider.id),
    }


def provider_auth_headers(provider_id: str, api_key: str) -> dict[str, str]:
    if provider_id == "gemini":
        return {"x-goog-api-key": api_key, "Accept": "application/json"}
    return {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}


async def validate_provider_key(provider_id: str, api_key: str) -> None:
    """Validate a browser-owned key through a one-shot HTTPS request; never persist it."""
    provider = get_provider(provider_id)
    key = validate_api_key_format(api_key)
    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=False) as client:
            response = await client.get(
                provider.models_url,
                headers=provider_auth_headers(provider.id, key),
            )
    except httpx.HTTPError:
        raise ByokError("provider_unavailable", f"Could not reach {provider.label}. Try again shortly.", 502)
    if response.status_code in (401, 403):
        raise ByokError("invalid_api_key", f"{provider.label} rejected this key. Check it and try again.", 400)
    if response.status_code >= 500:
        raise ByokError("provider_unavailable", f"{provider.label} is temporarily unavailable.", 502)
    if response.status_code >= 400:
        raise ByokError("provider_key_check_failed", f"{provider.label} could not validate this key. Check the key and provider account.", 400)


def gemini_generate_content(
    config: dict[str, str],
    contents: list[dict[str, Any]],
    *,
    system_instruction: str | None = None,
    max_output_tokens: int = 1000,
    temperature: float = 0.7,
) -> str:
    """Call the fixed Gemini REST endpoint using the key only in an HTTPS header."""
    if config.get("provider") != "gemini":
        raise ByokError("unsupported_provider", "This request is not configured for Google Gemini.")
    model = validate_model_id(config.get("model", ""), "gemini")
    provider = get_provider("gemini")
    body: dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": max(1, min(int(max_output_tokens), 8192)),
            "temperature": max(0.0, min(float(temperature), 2.0)),
        },
    }
    if system_instruction:
        body["systemInstruction"] = {"parts": [{"text": system_instruction}]}
    url = f"{provider.base_url}/models/{model}:generateContent"
    try:
        with httpx.Client(timeout=45.0, follow_redirects=False) as client:
            response = client.post(
                url,
                headers={"x-goog-api-key": config["api_key"], "Content-Type": "application/json"},
                json=body,
            )
    except httpx.HTTPError:
        raise ByokError("provider_unavailable", "Google Gemini could not be reached. Try again shortly.", 502)
    if response.status_code in (401, 403):
        raise ByokError("invalid_api_key", "Google Gemini rejected this key. Check it and try again.", 400)
    if response.status_code >= 400:
        raise ByokError("provider_request_failed", "Google Gemini could not complete the request. Check the model and account limits.", 502)
    try:
        data = response.json()
        parts = data["candidates"][0]["content"]["parts"]
        answer = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
    except (ValueError, KeyError, IndexError, TypeError):
        answer = ""
    if not answer.strip():
        raise ByokError("provider_empty_response", "Google Gemini returned no text for this request.", 502)
    return answer.strip()


def gemini_chat(config: dict[str, str], messages: list[dict[str, Any]]) -> str:
    system_instruction = ""
    contents: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role")
        content = message.get("content", "")
        if not isinstance(content, str):
            continue
        if role == "system":
            system_instruction = content
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})
        else:
            contents.append({"role": "user", "parts": [{"text": content}]})
    if not contents:
        raise ByokError("provider_request_failed", "There is no user message to send to Google Gemini.")
    return gemini_generate_content(
        config,
        contents,
        system_instruction=system_instruction or None,
        max_output_tokens=1000,
        temperature=0.7,
    )


def _required_supabase_config() -> tuple[str, str]:
    url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not service_key:
        raise ByokError("subscription_storage_not_configured", "JAI subscription storage is not configured yet.", 503)
    if not url.startswith("https://"):
        raise ByokError("subscription_storage_not_configured", "JAI subscription storage must use HTTPS.", 503)
    return url, service_key


class SupabaseStore:
    """Narrow server-only PostgREST access for subscription state only."""

    async def _request(
        self,
        method: str,
        table: str,
        *,
        params: dict[str, str] | None = None,
        json: Any = None,
        prefer: str | None = None,
    ) -> Any:
        base_url, service_key = _required_supabase_config()
        headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Accept": "application/json",
        }
        if json is not None:
            headers["Content-Type"] = "application/json"
        if prefer:
            headers["Prefer"] = prefer
        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=False) as client:
                response = await client.request(
                    method,
                    f"{base_url}/rest/v1/{table}",
                    params=params,
                    headers=headers,
                    json=json,
                )
        except httpx.HTTPError:
            raise ByokError("storage_unavailable", "JAI subscription storage is temporarily unavailable.", 503)
        if response.status_code >= 400:
            raise ByokError("storage_unavailable", "JAI subscription storage is temporarily unavailable.", 503)
        if response.status_code == 204 or not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            raise ByokError("storage_unavailable", "JAI subscription storage returned an invalid response.", 503)

    async def get_subscription(self, user_id: str) -> dict[str, Any] | None:
        rows = await self._request(
            "GET",
            "jai_subscriptions",
            params={
                "user_id": f"eq.{user_id}",
                "select": "status,stripe_customer_id,stripe_subscription_id,current_period_end",
                "limit": "1",
            },
        )
        return rows[0] if isinstance(rows, list) and rows else None

    async def save_subscription(self, values: dict[str, Any]) -> None:
        await self._request(
            "POST",
            "rpc/jai_update_subscription",
            json={
                "p_user_id": values["user_id"],
                "p_stripe_customer_id": values.get("stripe_customer_id"),
                "p_stripe_subscription_id": values.get("stripe_subscription_id"),
                "p_status": values.get("status", "inactive"),
                "p_current_period_end": values.get("current_period_end"),
                "p_event_created": values.get("stripe_event_created"),
                "p_event_id": values.get("stripe_event_id"),
            },
            prefer="return=minimal",
        )


STORE = SupabaseStore()


def active_subscription(subscription: dict[str, Any] | None) -> bool:
    return bool(subscription and subscription.get("status") in {"active", "trialing"})


def stripe_configuration() -> dict[str, str]:
    return {
        "secret_key": os.environ.get("STRIPE_SECRET_KEY", "").strip(),
        "webhook_secret": os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip(),
        "price_id": os.environ.get("STRIPE_PRICE_ID", "").strip(),
        "public_url": os.environ.get("JAI_PUBLIC_URL", "https://j-ai.top").strip().rstrip("/"),
    }


def billing_ready() -> bool:
    config = stripe_configuration()
    return bool(config["secret_key"] and config["price_id"] and config["webhook_secret"])
