"""
Gemini 與 Claude 的具體實作 (Builder llm-adapter.md)
====================================================
真接 SDK(google-genai / anthropic),回傳 text + token 用量 + 估算成本。
SDK 初始化邏輯與 services/llm_clients.py 一致,但本層回傳通用 LLMResponse,
而非強制 JSON dict —— 讓 router 成為所有任務(含非 JSON)的統一入口。
"""

from __future__ import annotations

import base64

from src.config import get_settings
from src.llm.interface import LLMProvider, LLMResponse, LLMUsage
from src.llm.pricing import estimate_cost


def _image_part(b64: str):
    """把 base64 / data-URL 轉成 Gemini Part。"""
    from google.genai import types

    mime = "image/jpeg"
    data = b64
    if data.startswith("data:") and "," in data:
        header, data = data.split(",", 1)
        try:
            mime = header.split(":", 1)[1].split(";", 1)[0] or "image/jpeg"
        except IndexError:
            pass
    raw = base64.b64decode(data)
    return types.Part.from_bytes(data=raw, mime_type=mime)


class GeminiAdapter(LLMProvider):
    name = "gemini"

    def __init__(self, model: str = "gemini-3.5-flash") -> None:
        self.model = model

    def _client(self):
        from google import genai

        settings = get_settings()
        if not settings.google_api_key:
            raise RuntimeError("GOOGLE_API_KEY not configured")
        return genai.Client(api_key=settings.google_api_key)

    def _config(self, system: str, json_mode: bool, temperature: float):
        from google.genai import types

        return types.GenerateContentConfig(
            system_instruction=system or None,
            response_mime_type="application/json" if json_mode else None,
            temperature=temperature,
        )

    def _to_response(self, response) -> LLMResponse:
        text = response.text or ""
        um = getattr(response, "usage_metadata", None)
        in_tok = getattr(um, "prompt_token_count", 0) or 0
        out_tok = getattr(um, "candidates_token_count", 0) or 0
        return LLMResponse(
            text=text,
            usage=LLMUsage(
                provider=self.name,
                model=self.model,
                input_tokens=in_tok,
                output_tokens=out_tok,
                cost_usd=estimate_cost(self.model, in_tok, out_tok),
            ),
        )

    async def generate(
        self, prompt: str, system: str = "", temperature: float = 0.7,
        json_mode: bool = False,
    ) -> LLMResponse:
        client = self._client()
        response = await client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=self._config(system, json_mode, temperature),
        )
        return self._to_response(response)

    async def generate_with_image(
        self, prompt: str, image_b64, system: str = "", json_mode: bool = False,
    ) -> LLMResponse:
        client = self._client()
        images = image_b64 if isinstance(image_b64, list) else [image_b64]
        parts = [prompt, *[_image_part(b) for b in images]]
        response = await client.aio.models.generate_content(
            model=self.model,
            contents=parts,
            config=self._config(system, json_mode, 0.2),
        )
        return self._to_response(response)


class ClaudeAdapter(LLMProvider):
    name = "claude"

    def __init__(self, model: str = "claude-opus-4-7") -> None:
        self.model = model

    def _client(self):
        from anthropic import AsyncAnthropic

        settings = get_settings()
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not configured")
        return AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def generate(
        self, prompt: str, system: str = "", temperature: float = 0.7,
        json_mode: bool = False,
    ) -> LLMResponse:
        client = self._client()
        user = prompt
        if json_mode:
            user = (
                f"{prompt}\n\nReply with a single JSON object and nothing else. "
                "No prose, no markdown fences."
            )
        response = await client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system or "",
            messages=[{"role": "user", "content": user}],
            temperature=temperature,
        )
        text = "".join(
            b.text for b in response.content if getattr(b, "type", None) == "text"
        )
        in_tok = getattr(response.usage, "input_tokens", 0) or 0
        out_tok = getattr(response.usage, "output_tokens", 0) or 0
        return LLMResponse(
            text=text,
            usage=LLMUsage(
                provider=self.name,
                model=self.model,
                input_tokens=in_tok,
                output_tokens=out_tok,
                cost_usd=estimate_cost(self.model, in_tok, out_tok),
            ),
        )

    async def generate_with_image(
        self, prompt: str, image_b64, system: str = "", json_mode: bool = False,
    ) -> LLMResponse:
        # vision 任務 canonical 鎖定 Gemini(即時影像是其強項)。
        # Claude 雖支援影像,但本系統不走此路徑,避免雙路徑分歧。
        raise NotImplementedError(
            "ClaudeAdapter 不支援影像路徑 — vision 任務 canonical 用 Gemini"
        )
