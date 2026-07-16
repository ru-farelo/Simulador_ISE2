"""Thin wrapper around a local Ollama model, mirroring the
structured_completion() contract of anthropic_client.py so callers can
switch between them by changing one import.

Used only for high-volume, low-risk generation (NGSL vocab
translations/examples, generic grammar/filler practice prompts) — never
for Reading/Writing/Speaking correction, where output quality directly
affects the feedback the candidate trusts. See anthropic_client.py for
that path; the two are deliberately kept separate rather than merged
behind a single "AI client" abstraction, so it's always obvious from the
import alone which model a given call uses.

Ollama's `format` parameter (a JSON schema) is the equivalent of
Anthropic's forced tool-use here — both exist purely to get reliable
structured JSON out of the model, not for genuine multi-turn tool calling,
so `tool_name`/`tool_description` are accepted for signature
compatibility but only `tool_description` is folded into the prompt.
"""

import json
from typing import Any

import httpx

from app.core.config import get_settings
from app.services.anthropic_client import AIServiceError

settings = get_settings()

_TIMEOUT = httpx.Timeout(120.0, connect=10.0)


def structured_completion(
    system: str,
    user_content: str,
    tool_name: str,
    tool_description: str,
    input_schema: dict[str, Any],
    max_tokens: int = 2000,
) -> dict[str, Any]:
    """Same contract as anthropic_client.structured_completion(): forces
    JSON matching `input_schema` out of the local model and returns it as
    a dict, raising AIServiceError (with a clear message, not a bare
    KeyError downstream) if the call fails or gets cut off.
    """
    payload = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": f"{system}\n\nTask: {tool_description}"},
            {"role": "user", "content": user_content},
        ],
        "format": input_schema,
        "stream": False,
        "think": False,  # we want direct structured output, not a reasoning trace
        "options": {"num_predict": max_tokens},
    }

    try:
        response = httpx.post(
            f"{settings.ollama_base_url}/api/chat", json=payload, timeout=_TIMEOUT
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise AIServiceError(
            f"Llamada al modelo local ({settings.ollama_model} via Ollama) fallo: {exc}. "
            "Comprueba que Ollama esta corriendo (`ollama serve`) y que el modelo esta "
            f"descargado (`ollama pull {settings.ollama_model}`)."
        ) from exc

    data = response.json()

    # Ollama's equivalent of Anthropic's stop_reason == "max_tokens": the
    # response was cut off by num_predict before the model finished, so
    # `content` is a truncated (often invalid) JSON fragment.
    if data.get("done_reason") == "length":
        raise AIServiceError(
            f"La respuesta del modelo local se cortó por num_predict ({max_tokens}) antes de "
            f"completar la llamada a '{tool_name}' — sube max_tokens o reduce el tamaño del lote."
        )

    content = data.get("message", {}).get("content", "")
    if not content.strip():
        raise AIServiceError(f"El modelo local devolvió una respuesta vacía para '{tool_name}'")

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise AIServiceError(
            f"El modelo local devolvió JSON invalido para '{tool_name}': {exc}. "
            f"Primeros 200 caracteres: {content[:200]!r}"
        ) from exc
