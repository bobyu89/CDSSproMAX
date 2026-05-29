# Sub-Agent: avatar-presenter — 虛擬病人形象

> **權重:標準(共用輸出能力,可熱插拔)。** 負責螢幕上的病人形象。
> 設計成三段式可替換:先用最簡單的版本跑通,之後無痛升級。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | avatar-presenter |
| 模組版本 | v1.0(靜態頭像版) |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core(session)、voice-output(音訊來源) |
| 被依賴模組 | 前端 UI |
| 外部服務 | 第一版無;升級版 HeyGen / D-ID |

> GitHub 路徑:`ticdss/avatar/`。Notion:「TICDSS / avatar-presenter / v1.0」。

---

## 三段式可替換設計

> 核心理念:臉不是系統靈魂,先用最簡單版本跑通流程,留好升級接口。

| 版本 | 內容 | 成本 | 何時用 |
|------|------|------|--------|
| **v1 靜態頭像** | 病人頭像 + 講話時聲波動畫 | 免費 | 現在,先跑通流程 |
| v2 對嘴影片 | HeyGen / D-ID 對嘴 | 月費 | 正式 demo / 參賽 |
| v3 即時虛擬人 | 即時表情互動 | 高 | 商業化階段 |

三個版本遵守同一介面,升級只換實作,前端與其他模組不動。

---

## 職責

1. 提供統一的 `AvatarPresenter` 介面。
2. 接收 voice-output 的音訊,呈現對應的病人形象。
3. 第一版:顯示靜態頭像 + 講話時的聲波動畫。
4. 預留 anxiety → 表情的接口(v2/v3 用)。

---

## 產出檔案

### 1. `avatar/presenter.py` — 統一介面 + 第一版實作

```python
"""
虛擬病人形象 — 三段式可替換
============================
v1 靜態頭像版:免費、能跑通。
升級時只換實作類別,前端呼叫方式完全不變。
"""

from abc import ABC, abstractmethod


class AvatarPresenter(ABC):
    """所有 Avatar 版本的統一介面。升級 = 換實作,不改介面。"""

    version: str = "base"

    @abstractmethod
    def render_payload(self, session, text: str, audio_ref: str) -> dict:
        """
        回傳給前端的呈現指令。
        text:      病人台詞(字幕用)
        audio_ref: voice-output 的音訊參照
        """
        ...


class StaticAvatarV1(AvatarPresenter):
    """
    第一版:靜態頭像 + 聲波動畫。
    病人講話時,前端顯示頭像並播放聲波動畫 + 字幕,嘴巴不動。
    免費、零外部服務,足以跑通完整流程。
    """
    version = "static-v1"

    def render_payload(self, session, text, audio_ref):
        return {
            "mode": "static",
            "avatar_image": self._pick_avatar(session),  # 病人頭像
            "subtitle": text,                              # 字幕
            "audio_ref": audio_ref,                        # 播放的語音
            "animation": "waveform",                       # 聲波動畫
            # 預留:anxiety 之後可驅動表情,v1 先不用
            "anxiety_hint": session.anxiety,
        }

    def _pick_avatar(self, session):
        # 依情境挑頭像(中年男性/女性等)
        return f"avatars/{session.scenario_id}.png"


# 升級範例(未來):
# class HeyGenAvatarV2(AvatarPresenter):
#     version = "heygen-v2"
#     def render_payload(self, session, text, audio_ref):
#         # 呼叫 HeyGen API,回傳對嘴影片串流參照
#         ...
```

### 2. `avatar/registry.py` — Avatar 版本切換

```python
"""
Avatar 版本切換 — 升級的開關
=============================
要從靜態頭像升級到 HeyGen?改這一行。
"""

from avatar.presenter import StaticAvatarV1

# 當前使用的 Avatar 版本
ACTIVE_AVATAR = StaticAvatarV1
# 升級:ACTIVE_AVATAR = HeyGenAvatarV2


def get_avatar():
    return ACTIVE_AVATAR()
```

---

## 各 Agent 怎麼用

問診生成台詞、voice-output 合成語音後,呼叫 Avatar 呈現:

```python
from avatar.registry import get_avatar

avatar = get_avatar()
payload = avatar.render_payload(session, text=reply, audio_ref=audio_id)
# payload 送給前端,前端依 mode 呈現
```

---

## 設計重點

- **臉不是靈魂,先跑通最重要**:第一版用靜態頭像 + 聲波 + 字幕,
  完全免費、零外部服務,足以做出完整流程的 demo。
- **升級無痛**:三個版本遵守 `AvatarPresenter` 同一介面,升級只改
  `registry.py` 一行,前端與其他模組完全不動。
- **anxiety 接口先留著**:`render_payload` 已帶 `anxiety_hint`,
  v1 用不到,但 v2/v3 要做表情變化時直接接,不用回頭改介面。
- **前端只認 payload**:前端不在乎背後是靜態圖還是 HeyGen 影片,
  只依 `mode` 欄位決定怎麼呈現,因此後端升級不影響前端。

---

## 設計紀錄(同步 Notion / GitHub)

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:靜態頭像 + 聲波,三段式可替換設計 | 第一版先跑通,留好 HeyGen 升級接口 |

---

## 驗證方式

1. `get_avatar()` 回傳 StaticAvatarV1。
2. `render_payload` 回傳含 avatar_image、subtitle、audio_ref、animation 的字典。
3. 確認 payload 帶 anxiety_hint(即使 v1 沒用到)。
4. 模擬升級:把 ACTIVE_AVATAR 換成假的 V2 類別,確認前端呼叫方式不需改。
```
