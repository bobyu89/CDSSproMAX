"""Thin LLM SDK wrappers.

We expose two helpers used by Agents:

  - ``gemini_generate_json(model, prompt, system_instruction)``
        Calls Gemini with ``response_mime_type="application/json"`` and returns
        the parsed dict. Used by E-Agent and A-Agent.

  - ``claude_generate_json(model, system, messages)``
        Calls Claude and asks it to emit JSON (best-effort parse). Used by S-Agent.

Both helpers are async, raise on transport errors, and return parsed JSON.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from src.config import get_settings

logger = logging.getLogger(__name__)


def prompt_hash(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\x00")
    return f"sha256:{h.hexdigest()[:32]}"


# === Gemini ================================================================

async def gemini_generate_json_multimodal(
    *,
    model: str,
    prompt: str,
    images_b64: list[str],
    system_instruction: str | None = None,
) -> dict[str, Any]:
    """Call Gemini with one or more inline images + a text prompt → parsed JSON.

    Each entry of ``images_b64`` can be either a raw base64 string or a
    full data URL (``data:image/jpeg;base64,...``). MIME type defaults to
    image/jpeg unless inferred from a data URL.
    """
    import base64

    from google import genai
    from google.genai import types

    settings = get_settings()
    if not settings.google_api_key:
        raise RuntimeError("GOOGLE_API_KEY not configured")

    client = genai.Client(api_key=settings.google_api_key)

    parts: list[Any] = [prompt]
    for b64 in images_b64:
        mime = "image/jpeg"
        data = b64
        if data.startswith("data:") and "," in data:
            header, data = data.split(",", 1)
            try:
                mime = header.split(":", 1)[1].split(";", 1)[0] or "image/jpeg"
            except IndexError:
                pass
        try:
            raw = base64.b64decode(data)
        except Exception:
            continue
        parts.append(types.Part.from_bytes(data=raw, mime_type=mime))

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        temperature=0.2,
    )

    response = await client.aio.models.generate_content(
        model=model,
        contents=parts,
        config=config,
    )

    text = response.text or ""
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        logger.error("Gemini multimodal returned non-JSON: %s", text[:500])
        raise RuntimeError(f"Gemini multimodal JSON parse failed: {exc}") from exc


async def gemini_generate_json(
    *,
    model: str,
    prompt: str,
    system_instruction: str | None = None,
    response_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Call Gemini and parse the response as JSON.

    Uses the google-genai SDK (the new unified client, not google-generativeai).
    """
    from google import genai
    from google.genai import types

    settings = get_settings()
    if not settings.google_api_key:
        raise RuntimeError("GOOGLE_API_KEY not configured")

    client = genai.Client(api_key=settings.google_api_key)

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        response_schema=response_schema,
        temperature=0.2,
    )

    response = await client.aio.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )

    text = response.text or ""
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        logger.error("Gemini returned non-JSON output: %s", text[:500])
        raise RuntimeError(f"Gemini JSON parse failed: {exc}") from exc


# === Claude ================================================================

async def claude_generate_json(
    *,
    model: str,
    system: str,
    user_message: str,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    """Call Claude and best-effort parse the response as JSON.

    Claude doesn't have a strict JSON mode; we wrap the user message with a
    "Reply with valid JSON only" instruction and parse the first {…} blob.
    """
    from anthropic import AsyncAnthropic

    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    json_user = (
        f"{user_message}\n\n"
        "Reply with a single JSON object and nothing else. No prose, no markdown fences."
    )

    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": json_user}],
        temperature=0.2,
    )

    # Concatenate text blocks
    raw = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )
    return _parse_first_json_blob(raw)


def _parse_first_json_blob(text: str) -> dict[str, Any]:
    """Tolerant parser — strips optional ```json fences then takes the first {...}."""
    s = text.strip()
    if s.startswith("```"):
        # ```json\n{...}\n```  → drop fences
        s = s.split("```", 2)[1]
        if s.startswith("json"):
            s = s[4:]
        s = s.rsplit("```", 1)[0].strip()
    # Slice to outermost braces if there's stray prose
    if not s.startswith("{"):
        start = s.find("{")
        end = s.rfind("}")
        if start == -1 or end == -1:
            raise RuntimeError(f"No JSON object found in Claude response: {text[:200]}")
        s = s[start : end + 1]
    return json.loads(s)
