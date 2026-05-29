# Sub-Agent: voice-output — TTS 語音輸出

> **權重:標準(共用輸出能力)。** 任何階段要讓虛擬病人「說話」,都呼叫本模組。
> 非 StageAgent,是被各 Agent 呼叫的共用服務。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | voice-output |
| 模組版本 | v1.0 |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core(session) |
| 被依賴模組 | inquiry / diagnosis / avatar-presenter |
| 外部服務 | ElevenLabs |

> GitHub 路徑:`ticdss/voice/`。Notion:「TICDSS / voice-output / v1.0」。

---

## 三大設計決策

| 決策 | 採用方案 |
|------|---------|
| TTS 引擎 | ElevenLabs(自然、台灣口音) |
| 語氣調整 | 受 anxiety 影響:高 anxiety → 語速快、聲音抖、停頓多 |
| 播放方式 | 串流(邊生成邊播,降低延遲) |

---

## 職責

1. 接收文字 + anxiety,呼叫 ElevenLabs 串流合成語音。
2. 依 anxiety 調整語音參數(語速、穩定度)。
3. 回傳音訊串流給前端;同時供 avatar-presenter 做口型同步。
4. 記錄 TTS 用量(字元數)供成本追蹤。

---

## 產出檔案

### 1. `voice/voice_output.py`

```python
"""
TTS 語音輸出
============
把病人台詞變成串流語音。語氣受 anxiety 影響,
讓「緊張的病人聽起來真的緊張」。
"""

from dataclasses import dataclass


@dataclass
class VoiceSettings:
    """ElevenLabs 語音參數。依 anxiety 動態調整。"""
    stability: float          # 穩定度:低 = 情緒起伏大(緊張)
    speed: float              # 語速:1.0 = 正常
    similarity: float = 0.75  # 音色相似度


def settings_from_anxiety(anxiety: float) -> VoiceSettings:
    """
    anxiety 0.0–1.0 → 語音參數。
    anxiety 高 → 語速快、穩定度低(聲音抖、情緒外露)。
    """
    return VoiceSettings(
        stability=max(0.2, 0.8 - anxiety * 0.5),   # 越焦慮越不穩
        speed=min(1.3, 1.0 + anxiety * 0.3),        # 越焦慮越快
        similarity=0.75,
    )


async def synthesize_stream(text: str, session, voice_id: str = "tw_patient_01"):
    """
    串流合成。yield 音訊片段,前端邊收邊播。
    """
    settings = settings_from_anxiety(session.anxiety)

    # 記錄用量(字元數)供成本追蹤
    session.scratch.setdefault("tts_chars", 0)
    session.scratch["tts_chars"] += len(text)

    # ElevenLabs 串流 API(實際串接時實作)
    # async for chunk in elevenlabs.stream(
    #         text=text, voice_id=voice_id,
    #         stability=settings.stability,
    #         speed=settings.speed):
    #     yield chunk
    raise NotImplementedError("串接 ElevenLabs streaming API 時實作")
```

### 2. `voice/pricing.py` — TTS 成本

```python
"""ElevenLabs 依字元計費,記錄供成本透明。"""

# 美元 / 1000 字元(依方案調整)
TTS_PRICE_PER_1K_CHARS = 0.30


def tts_cost(chars: int) -> float:
    return (chars / 1000) * TTS_PRICE_PER_1K_CHARS
```

---

## 各 Agent 怎麼用

inquiry 生成病人台詞後,呼叫本模組轉語音:

```python
from voice.voice_output import synthesize_stream

# 在 inquiry_agent.handle_input 裡,生成 reply 後:
async for audio_chunk in synthesize_stream(resp.text, session):
    yield {"type": "audio", "chunk": audio_chunk}
```

---

## 設計重點

- **anxiety → 語音參數的映射是核心**:`settings_from_anxiety` 把抽象的
  焦慮指數變成可聽見的語音變化。這是沉浸感的關鍵——病人不只說緊張的話,
  聲音也真的緊張。
- **串流降低延遲**:不等整句合成完才播,邊生成邊播,對話更即時。
- **音訊同時餵給 avatar-presenter**:口型同步需要音訊,本模組的輸出
  同時供語音播放與 Avatar 對嘴,兩者共用一份合成結果。
- **字元數計入成本**:`session.scratch["tts_chars"]` 累加,訓練結束
  可算出 TTS 花費,與 LLM 成本一起呈現。

---

## 設計紀錄(同步 Notion / GitHub)

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:ElevenLabs 串流 + anxiety 語氣調整 + 成本追蹤 | 三大決策定稿 |

---

## 驗證方式

1. 餵入高 anxiety(0.8),確認 `settings_from_anxiety` 回傳高語速、低穩定度。
2. 餵入低 anxiety(0.2),確認語速正常、穩定度高。
3. 確認 `synthesize_stream` 為串流(yield 多個片段),非一次回傳。
4. 連續合成數句,確認 `session.scratch["tts_chars"]` 正確累加。
```
