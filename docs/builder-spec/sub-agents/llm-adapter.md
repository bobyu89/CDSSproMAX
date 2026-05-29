# Sub-Agent: llm-adapter — LLM 熱插拔層

> **權重:高(僅次於 core)。** 所有需要 LLM 的模組都透過本層呼叫,
> 不直接綁定任何模型。換模型 = 改設定一行。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | llm-adapter |
| 模組版本 | v1.0 |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core(contract) |
| 被依賴模組 | inquiry / vision / diagnosis / scoring(DUAT)/ rag-note |

> GitHub 路徑:`ticdss/llm/`。Notion 設計紀錄頁:「TICDSS / llm-adapter / v1.0」。

---

## 職責

1. 定義 `LLMProvider` 統一介面(文字生成 + 影像生成)。
2. 實作 `GeminiAdapter`、`ClaudeAdapter`。
3. 任務導向的模型對應(`LLM_CONFIG`)。
4. **備援機制**:主力掛掉自動切備援。
5. **成本追蹤**:每次呼叫記錄 token 與估算成本。

---

## 三大設計決策

| 決策 | 採用方案 |
|------|---------|
| 切換顆粒度 | 任務導向:每個任務(vision/dialog/diagnosis/duat)各自指定主力與備援模型 |
| 備援機制 | 主力呼叫失敗自動切備援,並記錄 fallback 事件 |
| 成本追蹤 | 每次呼叫記錄 token 數與估算成本,累加至 session |

---

## 產出檔案

### 1. `llm/interface.py` — 統一介面與資料格式

```python
"""
LLM 統一介面
============
所有 Agent 透過此介面呼叫 LLM,不直接依賴任何 SDK。
換模型只改 config,Agent 程式碼完全不動。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMUsage:
    """單次呼叫的用量與成本。"""
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    used_fallback: bool = False    # 是否觸發了備援


@dataclass
class LLMResponse:
    text: str
    usage: LLMUsage
    raw: dict = None


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def generate(self, prompt: str, system: str = "",
                       temperature: float = 0.7) -> LLMResponse:
        """純文字生成。"""
        ...

    @abstractmethod
    async def generate_with_image(self, prompt: str, image_b64: str,
                                  system: str = "") -> LLMResponse:
        """帶影像生成(身評視覺評核用)。"""
        ...
```

### 2. `llm/pricing.py` — 成本估算表

```python
"""
成本估算 — 個人戶開發必備
==========================
每百萬 token 的美元價格。實際數字依各服務公告調整。
"""

# (input 價格, output 價格) per 1M tokens, USD
PRICING = {
    "gemini-flash-live": (0.75, 3.00),
    "gemini-flash":      (0.30, 2.50),
    "claude-opus-4-8":   (5.00, 25.00),
}


def estimate_cost(model: str, in_tok: int, out_tok: int) -> float:
    p_in, p_out = PRICING.get(model, (0, 0))
    return (in_tok / 1e6) * p_in + (out_tok / 1e6) * p_out
```

### 3. `llm/adapters.py` — 各模型實作

```python
"""Gemini 與 Claude 的具體實作。"""

from llm.interface import LLMProvider, LLMResponse, LLMUsage
from llm.pricing import estimate_cost


class GeminiAdapter(LLMProvider):
    name = "gemini"
    def __init__(self, model="gemini-flash-live"):
        self.model = model
        # init Gemini client

    async def generate(self, prompt, system="", temperature=0.7):
        # resp = await gemini_client.generate(...)
        # 解析 token 用量,計算成本
        raise NotImplementedError("串接 Gemini SDK 時實作")

    async def generate_with_image(self, prompt, image_b64, system=""):
        raise NotImplementedError("串接 Gemini SDK 時實作")


class ClaudeAdapter(LLMProvider):
    name = "claude"
    def __init__(self, model="claude-opus-4-8"):
        self.model = model

    async def generate(self, prompt, system="", temperature=0.7):
        raise NotImplementedError("串接 Anthropic SDK 時實作")

    async def generate_with_image(self, prompt, image_b64, system=""):
        raise NotImplementedError("串接 Anthropic SDK 時實作")
```

### 4. `llm/router.py` — 任務路由 + 備援 + 成本累加

```python
"""
LLM 路由器 — 熱插拔的切換中樞
==============================
1. 任務導向:依任務取得主力模型
2. 備援機制:主力失敗自動切備援
3. 成本追蹤:每次呼叫累加成本至 session
"""

from llm.adapters import GeminiAdapter, ClaudeAdapter

# 任務 → (主力, 備援)
# 換模型只改這張表,所有 Agent 不動
LLM_CONFIG = {
    "vision":    [("gemini", "gemini-flash-live"), ("gemini", "gemini-flash")],
    "dialog":    [("gemini", "gemini-flash"),      ("claude", "claude-opus-4-8")],
    "diagnosis": [("claude", "claude-opus-4-8"),   ("gemini", "gemini-flash")],
    "duat":      [("claude", "claude-opus-4-8"),   ("gemini", "gemini-flash")],
}

_PROVIDERS = {"gemini": GeminiAdapter, "claude": ClaudeAdapter}


def _build(provider_name, model):
    return _PROVIDERS[provider_name](model=model)


async def call_llm(task: str, prompt: str, session=None,
                   image_b64=None, system="", temperature=0.7):
    """
    依任務呼叫 LLM。主力失敗自動切備援。成本累加至 session。
    """
    chain = LLM_CONFIG[task]         # [(主力), (備援)]
    last_error = None

    for i, (pname, model) in enumerate(chain):
        provider = _build(pname, model)
        try:
            if image_b64:
                resp = await provider.generate_with_image(
                    prompt, image_b64, system)
            else:
                resp = await provider.generate(prompt, system, temperature)

            # 標記是否用了備援
            resp.usage.used_fallback = (i > 0)

            # 成本累加至 session
            if session is not None:
                session.scratch.setdefault("llm_cost", 0.0)
                session.scratch["llm_cost"] += resp.usage.cost_usd
                session.scratch.setdefault("llm_calls", [])
                session.scratch["llm_calls"].append(resp.usage)
            return resp

        except Exception as e:
            last_error = e
            continue                  # 主力失敗,試備援

    raise RuntimeError(f"任務 {task} 所有模型皆失敗:{last_error}")
```

---

## Agent 怎麼用

各 Agent 不自己建 LLM,統一呼叫 `call_llm`:

```python
from llm.router import call_llm

# 問診對話(主力 Gemini,失敗自動切 Claude)
resp = await call_llm("dialog", prompt, session=session)

# 身評視覺評核
resp = await call_llm("vision", prompt, session=session, image_b64=frame)
```

---

## 設計重點

- **任務導向 + 備援**:`LLM_CONFIG` 每個任務是一個清單,第一個是主力,
  後面是備援。主力失敗自動往後試,完全自動。
- **成本透明**:每次呼叫的 token 與成本累加到 `session.scratch["llm_cost"]`,
  訓練結束就能看到「這次花了多少美元」。
- **換模型零痛苦**:要把問診換成 Claude?改 `LLM_CONFIG["dialog"]` 第一項即可。
- **視覺鎖定 Gemini**:vision 任務主力與備援都是 Gemini 系列,因即時影像是其強項。

---

## 設計紀錄(同步 Notion / GitHub 用)

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:任務路由 + 備援 + 成本追蹤 | 確立 LLM 熱插拔層,三大決策定稿 |

---

## 驗證方式

1. `call_llm("dialog", ...)` 與 `call_llm("vision", ...)` 應使用不同主力模型。
2. 模擬主力拋例外,確認自動切備援且 `used_fallback=True`。
3. 連續呼叫數次,確認 `session.scratch["llm_cost"]` 正確累加。
4. 改 `LLM_CONFIG["dialog"]` 主力,確認 Agent 程式碼不需改動即生效。
