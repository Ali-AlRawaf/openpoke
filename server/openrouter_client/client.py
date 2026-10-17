from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx

from ..config import get_settings
from ..logging_config import logger

OpenRouterBaseURL = "https://openrouter.ai/api/v1"


class OpenRouterError(RuntimeError):
    """Raised when the OpenRouter API returns an error response."""


def _headers(*, api_key: Optional[str] = None) -> Dict[str, str]:
    settings = get_settings()
    key = (api_key or settings.openrouter_api_key or "").strip()
    if not key:
        raise OpenRouterError("Missing OpenRouter API key")

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    return headers


def _build_messages(messages: List[Dict[str, str]], system: Optional[str]) -> List[Dict[str, str]]:
    if system:
        return [{"role": "system", "content": system}, *messages]
    return messages


def _handle_response_error(exc: httpx.HTTPStatusError) -> None:
    response = exc.response
    detail: str
    try:
        payload = response.json()
        detail = payload.get("error") or payload.get("message") or json.dumps(payload)
    except Exception:
        detail = response.text
    raise OpenRouterError(f"OpenRouter request failed ({response.status_code}): {detail}") from exc


def _cache_control() -> Optional[Dict[str, str]]:
    """Top-level Anthropic cache_control; OpenRouter moves the breakpoint to the last cacheable block."""
    settings = get_settings()
    if not settings.prompt_cache_enabled:
        return None
    control = {"type": "ephemeral"}
    if settings.prompt_cache_ttl == "1h":
        control["ttl"] = "1h"
    return control


def _log_completion(model: str, data: Dict[str, Any]) -> None:
    """Log token usage (including cache hits) and surface refusals, which arrive as HTTP 200."""
    choice = (data.get("choices") or [{}])[0]
    finish_reason = choice.get("native_finish_reason") or choice.get("finish_reason")
    if finish_reason == "refusal":
        logger.warning("LLM refused request", extra={"model": model})
    elif finish_reason in {"length", "max_tokens"}:
        logger.warning("LLM response truncated at max_tokens", extra={"model": model})

    usage = data.get("usage") or {}
    prompt_details = usage.get("prompt_tokens_details") or {}
    completion_details = usage.get("completion_tokens_details") or {}
    logger.debug(
        "LLM usage",
        extra={
            "model": model,
            "finish_reason": finish_reason,
            "prompt_tokens": usage.get("prompt_tokens"),
            "cached_tokens": prompt_details.get("cached_tokens"),
            "cache_write_tokens": prompt_details.get("cache_write_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "reasoning_tokens": completion_details.get("reasoning_tokens"),
            "cost": usage.get("cost"),
        },
    )


async def request_chat_completion(
    *,
    model: str,
    messages: List[Dict[str, str]],
    system: Optional[str] = None,
    api_key: Optional[str] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    max_tokens: Optional[int] = None,
    base_url: str = OpenRouterBaseURL,
) -> Dict[str, Any]:
    """Request a chat completion and return the raw JSON payload."""

    payload: Dict[str, object] = {
        "model": model,
        "messages": _build_messages(messages, system),
        "stream": False,
        "max_tokens": max_tokens or get_settings().llm_max_tokens,
    }
    if tools:
        payload["tools"] = tools
    if model.startswith("anthropic/"):
        cache_control = _cache_control()
        if cache_control:
            payload["cache_control"] = cache_control

    url = f"{base_url.rstrip('/')}/chat/completions"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                headers=_headers(api_key=api_key),
                json=payload,
                timeout=60.0,  # Set reasonable timeout instead of None
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                _handle_response_error(exc)
            data = response.json()
            _log_completion(model, data)
            return data
        except httpx.HTTPStatusError as exc:  # pragma: no cover - handled above
            _handle_response_error(exc)
        except httpx.HTTPError as exc:
            raise OpenRouterError(f"OpenRouter request failed: {exc}") from exc

    raise OpenRouterError("OpenRouter request failed: unknown error")


__all__ = ["OpenRouterError", "request_chat_completion", "OpenRouterBaseURL"]
