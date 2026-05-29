# Sub-Agent: concurrency-manager — 併發與資源管理(設計預留)

> **權重:基礎設施層(橫跨全系統,非訓練流程的一環)。**
> **狀態:設計預留 — 定義接口,prototype 不實作,上線前再實作。**
> 處理多使用者併發的技術過載與成本過載。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | concurrency-manager |
| 模組版本 | v0.1(設計預留,未實作) |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core、llm-adapter、voice-output、vision |
| 被依賴模組 | 所有呼叫外部 API 的模組(上線後) |
| 實作時機 | prototype 後、給班級/多人使用前 |

> GitHub 路徑:`ticdss/infra/concurrency.py`(預留)。Notion:「TICDSS / concurrency-manager / v0.1」。

---

## 為什麼設計預留而非現在實作

- **prototype 階段**:一人或少數測試者,無過載問題。現在實作併發控制 =
  過度設計,拖慢開發。
- **但要留接口**:上線給一個班(同時 10-30 人)時,過載會立刻發生。
  接口先留好,屆時直接實作,不打掉重練。

---

## 兩個要解的問題(性質不同)

| 問題 | 是什麼 | 對個人戶/小團隊的嚴重性 |
|------|--------|------------------------|
| A 技術過載 | 太多人同時呼叫 LLM/TTS/Vision,撞 API 速率限制,請求失敗或排隊 | 系統會掛 |
| B 成本過載 | 多人同時訓練,API 費用快速累積 | 可能更致命:系統沒掛,但帳單爆 |

> 很多設計只想到 A,但對你而言 B 可能更該防。本模組兩者都管。

---

## 系統負載盤點

```
🔴 最吃資源(每使用者持續佔用)
   vision 連續追蹤   每人一條串流,持續 OpenCV + 偶爾 Gemini
   即時 LLM 對話     問診每輪呼叫 LLM
   TTS 語音串流      每句合成
🟡 中等(短暫尖峰)
   DUAT 五代理       迴圈結束五次 LLM 一次湧上
   case-generator    批次生成大量呼叫
🟢 輕量
   ArUco 本地偵測 / 評分計算 / SQL 讀寫
```

> 瓶頸幾乎都在外部 API 呼叫(LLM/TTS/Vision),非伺服器算力。
> 關鍵負載 = 「同時訓練的人數」,非總註冊人數。

---

## 設計接口(預留,待實作)

### 1. `infra/concurrency.py` — 併發控制接口

```python
"""
併發與資源管理(設計預留)
==========================
定義接口,prototype 不實作。上線前實作佇列、限流、成本守門。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


# ── 併發控制 ──
class ConcurrencyGate(ABC):
    """資源閘門:控制同時進行的重資源操作數量。"""

    @abstractmethod
    async def acquire(self, resource: str, user_id: str):
        """
        請求一個資源額度(如 vision 串流、LLM 呼叫)。
        超過上限則排隊等待。resource: 'vision'|'llm'|'tts'。
        """
        ...

    @abstractmethod
    async def release(self, resource: str, user_id: str):
        """釋放資源額度。"""
        ...


# ── 成本守門 ──
@dataclass
class CostBudget:
    """成本上限設定。"""
    per_user_session: float = 1.0      # 每人每次訓練上限(美元)
    per_user_daily: float = 5.0        # 每人每日上限
    system_daily: float = 100.0        # 全系統每日上限


class CostGuard(ABC):
    """成本守門員:超過上限時阻擋或降級。"""

    @abstractmethod
    async def check(self, user_id: str, estimated_cost: float) -> dict:
        """
        呼叫前檢查是否超出預算。
        回傳 {"allow": bool, "action": "proceed"|"degrade"|"block"}。
        """
        ...

    @abstractmethod
    async def record(self, user_id: str, actual_cost: float):
        """記錄實際花費,累加至使用者與系統總額。"""
        ...
```

### 2. 與 llm-adapter 的整合點(預留)

```python
"""
llm-adapter 的 call_llm 上線後加入守門:
- 呼叫前:CostGuard.check + ConcurrencyGate.acquire
- 呼叫後:CostGuard.record + ConcurrencyGate.release
prototype 階段這層為 no-op(直接放行)。
"""

# call_llm 內(上線後):
# gate = get_concurrency_gate()
# guard = get_cost_guard()
# decision = await guard.check(user_id, est_cost)
# if decision["action"] == "block": raise BudgetExceeded
# if decision["action"] == "degrade": task = _downgrade(task)
# await gate.acquire("llm", user_id)
# try: resp = await provider.generate(...)
# finally: await gate.release("llm", user_id)
# await guard.record(user_id, resp.usage.cost_usd)
```

---

## 過載降級策略(預留)

> 過載或超預算時,優雅降級而非直接失敗,延續系統各處的降級思路:

| 資源 | 正常 | 降級 |
|------|------|------|
| TTS | ElevenLabs 串流 | 改非串流 / 改字幕為主 |
| Avatar | 對嘴影片 | 降為靜態頭像(avatar-presenter v1) |
| LLM | 主力模型 | 改用較便宜的備援模型 |
| Vision 手法 | Gemini 抽幀 | 暫停手法判讀,只保留本地位置追蹤 |
| 即時評分 | 60%+40% 語義 | 暫時只給 60% 確定性分數 |

> 降級接口與既有模組對接:avatar-presenter 已三段式可降、llm-adapter 已有備援、
> vision 位置追蹤本就本地——降級基礎已在,本模組只是統一調度。

---

## 資源分級與排隊(預留)

```
重資源(需排隊):vision 串流、即時 LLM 對話、TTS
輕資源(直接過):ArUco 本地、評分計算、SQL

排隊原則(上線後):
- OSCE 模式 > 練習模式(考試不能等)
- 進行中的 session > 新進入的(避免半途被卡)
- 全系統達上限 → 新 session 進入等候,告知預估等待
```

---

## 設計重點

- **設計預留,不拖慢 prototype**:接口為抽象類,prototype 階段可用 no-op
  實作(直接放行),完全不影響單人開發。
- **兩道守門**:ConcurrencyGate 管「同時幾個」(防技術過載),
  CostGuard 管「花多少錢」(防成本過載)。個人戶尤須後者。
- **降級而非失敗**:過載時走降級(TTS 非串流、Avatar 靜態、LLM 換便宜),
  而非直接報錯。降級基礎已散在各模組,本模組統一調度。
- **整合點明確**:主要掛在 llm-adapter 的 call_llm 與 voice/vision 的
  外部呼叫處,上線時在這些點插入 acquire/check,不需改業務邏輯。
- **負載看「同時訓練數」**:設計圍繞併發 session 數,非總用戶數。

---

## 設計紀錄

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v0.1 | 設計預留:併發閘門 + 成本守門 + 降級策略接口 | 多使用者上線前預留,prototype 不實作 |

---

## 實作時機與檢核

**何時實作:** 當「同時訓練人數」可能 > 5,或要給一個班使用時。

**實作優先順序(屆時):**
1. CostGuard(先防破產,個人戶最痛)
2. ConcurrencyGate 的 LLM 限流(最常撞速率限制)
3. 降級策略串接(過載時不失敗)
4. 排隊與優先級(規模再大時)

**驗證方式(實作後):**
1. 模擬 N 個併發 session,確認超過上限者進入排隊而非失敗。
2. 單一使用者花費達 per_user_session 上限,確認觸發降級或阻擋。
3. 全系統達 system_daily,確認新 session 進入等候並告知。
4. 過載時確認 TTS/Avatar/LLM 正確降級,訓練仍可完成。
5. OSCE session 確認優先於練習 session。
```
