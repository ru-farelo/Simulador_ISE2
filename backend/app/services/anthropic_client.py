"""Thin wrapper around the Anthropic SDK.

This is the ONLY module in the codebase allowed to import `anthropic` or
touch `settings.anthropic_api_key`. Routers and other services must go
through the functions below, never construct a client themselves — that
keeps the API key contained to one place and makes it easy to add
retries/logging/model-swaps in one spot later.
"""

from typing import Any

import anthropic

from app.core.config import get_settings

settings = get_settings()
_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


class AIServiceError(RuntimeError):
    """Raised when the Anthropic API call fails or returns an unexpected shape."""


def text_completion(system: str, user_content: str, max_tokens: int = 2000) -> str:
    try:
        response = _client.messages.create(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_content}],
        )
    except anthropic.APIError as exc:
        raise AIServiceError(f"Anthropic API call failed: {exc}") from exc

    text_blocks = [block.text for block in response.content if block.type == "text"]
    if not text_blocks:
        raise AIServiceError("Anthropic response contained no text content")
    return "\n".join(text_blocks)


def structured_completion(
    system: str,
    user_content: str,
    tool_name: str,
    tool_description: str,
    input_schema: dict[str, Any],
    max_tokens: int = 2000,
) -> dict[str, Any]:
    """Force the model to answer via a single tool call and return its input.

    Using tool-use with a forced tool_choice is the reliable way to get
    well-formed JSON out of Claude, rather than asking it to "reply in
    JSON" in prose and hoping it doesn't wrap it in markdown fences.
    """
    tool = {
        "name": tool_name,
        "description": tool_description,
        "input_schema": input_schema,
    }
    try:
        response = _client.messages.create(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_content}],
            tools=[tool],
            tool_choice={"type": "tool", "name": tool_name},
        )
    except anthropic.APIError as exc:
        raise AIServiceError(f"Anthropic API call failed: {exc}") from exc

    # A response cut off by the token limit still contains a tool_use
    # block, but block.input is a partial (sometimes empty {}) JSON
    # object that the SDK best-effort-parsed — silently returning it
    # produces a confusing KeyError several calls downstream instead of a
    # clear error here, where we actually know what went wrong.
    if response.stop_reason == "max_tokens":
        raise AIServiceError(
            f"La respuesta de Claude se cortó por max_tokens ({max_tokens}) antes de "
            f"completar la llamada a '{tool_name}' — sube max_tokens o reduce el tamaño del lote."
        )

    for block in response.content:
        if block.type == "tool_use" and block.name == tool_name:
            return block.input

    raise AIServiceError(f"Anthropic response did not include a '{tool_name}' tool call")
