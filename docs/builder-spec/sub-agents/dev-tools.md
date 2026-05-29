# Sub-Agent: dev-tools — 開發者除錯工具層

> **權重:基礎設施層(獨立除錯工具,非角色)。**
> 給開發者用的上帝視角 + 工具箱。雙重安全開關:開發者帳號 AND 非正式環境。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | dev-tools |
| 模組版本 | v1.0 |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core、roles-access、所有需除錯的模組 |
| 被依賴模組 | 開發/測試流程 |

> GitHub 路徑:`ticdss/dev/`。Notion:「TICDSS / dev-tools / v1.0」。

---

## 為什麼是工具層而非角色

| | 三種角色 | 開發者模式 |
|--|---------|-----------|
| 管什麼 | 能存取什麼資料(who sees what) | 能不能用除錯工具(can use dev tools) |
| 性質 | 權限分級 | 功能開關 |

> 開發者要測學員流程,但他不是學員角色——硬塞成第四角色會權限打架。
> 故做成獨立工具層:在原本角色之上額外解鎖除錯工具,不影響角色權限。
> 可「管理者身分 + 開發者工具」測後台,或「測試學員帳號 + 開發者工具」測訓練。

---

## 雙重安全開關

```
開發者工具可用 = 帳號為開發者  AND  非正式環境(env != production)
```

> 雙保險:即使開發者帳號登進正式環境,除錯工具(跳計時、關成本、注入假資料)
> 也自動失效。帳號外洩也不能在正式環境動學員的考試。

---

## 五大除錯能力(使用者所選)

| 能力 | 用途 |
|------|------|
| 看內部狀態 | 即時檢視 session、signals、評分過程 |
| 成本/API 監控 | 看每步燒多少 token/錢、哪些走了 fallback |
| 模組單測 | 單獨跑某一個 sub-agent,不啟動整個流程 |
| 跳過流程 | 直接跳到某階段測(免從頭跑) |
| 關閉限制 | 跳過計時、跳過成本上限 |

---

## 產出檔案

### 1. `dev/gate.py` — 雙重安全開關

```python
"""
開發者工具開關
==============
雙重檢查:開發者帳號 AND 非正式環境。任一不符,工具全部失效。
"""

import os


def dev_tools_enabled(user) -> bool:
    """除錯工具是否可用。雙保險。"""
    is_developer = getattr(user, "is_developer", False)
    not_production = os.getenv("TICDSS_ENV", "dev") != "production"
    return is_developer and not_production


def require_dev(user):
    """守門:非開發者或正式環境則拒絕。"""
    if not dev_tools_enabled(user):
        raise PermissionError("開發者工具不可用(需開發者帳號且非正式環境)")
```

### 2. `dev/inspector.py` — 看內部狀態 + 成本監控

```python
"""
狀態檢視器
==========
即時檢視 session 內部、訊號、評分過程、成本。
"""

from dev.gate import require_dev


def inspect_session(user, session) -> dict:
    """傾印 session 完整內部狀態(除錯用)。"""
    require_dev(user)
    return {
        "phase": session.phase.value,
        "mode": session.mode,
        "difficulty": session.difficulty,
        "anxiety": session.anxiety,
        "phase_scores": {k: vars(v) for k, v in session.phase_scores.items()},
        "signals": session.signals,
        "scratch_keys": list(session.scratch.keys()),
        "llm_cost": session.scratch.get("llm_cost", 0),
        "tts_chars": session.scratch.get("tts_chars", 0),
    }


def cost_breakdown(user, session) -> dict:
    """逐次 LLM 呼叫的成本明細,看每步燒多少、哪些走 fallback。"""
    require_dev(user)
    calls = session.scratch.get("llm_calls", [])
    return {
        "total_usd": session.scratch.get("llm_cost", 0),
        "calls": [{"model": c.model, "cost": c.cost_usd,
                   "fallback": c.used_fallback} for c in calls],
        "fallback_count": sum(1 for c in calls if c.used_fallback),
    }
```

### 3. `dev/harness.py` — 模組單測 + 跳過流程

```python
"""
測試夾具
========
單獨跑某 sub-agent、直接跳到某階段,免從頭跑整個流程。
"""

from dev.gate import require_dev
from core.session import TrainingSession, Phase


def make_test_session(user, mode="practice", scenario_id="test",
                      phase=None, **overrides):
    """
    建一個測試用 session,可直接指定起始階段(跳過流程)。
    """
    require_dev(user)
    s = TrainingSession(mode=mode, scenario_id=scenario_id)
    if phase:
        s.phase = Phase(phase)        # 直接跳到指定階段測
    for k, v in overrides.items():
        setattr(s, k, v)
    return s


async def run_single_agent(user, stage: str, session, payload):
    """
    單獨跑一個階段 Agent,不啟動整個流程引擎。
    """
    require_dev(user)
    from core.flow import registry
    agent = registry.get_agent(stage)
    agent.on_enter(session)
    result = await agent.handle_input(session, payload)
    score = agent.score(session)
    return {"result": result, "score": vars(score)}
```

### 4. `dev/overrides.py` — 關閉限制 + 假資料注入

```python
"""
限制覆寫與假資料
================
跳過計時、跳過成本上限、注入假 HRV/假評分,加速測試。
"""

from dev.gate import require_dev


def disable_limits(user, session):
    """關閉計時與成本上限(僅開發環境)。"""
    require_dev(user)
    session.scratch["_dev_no_timer"] = True       # 流程引擎檢查此旗標
    session.scratch["_dev_no_cost_cap"] = True     # CostGuard 檢查此旗標


def inject_signal(user, session, signal_type, label, **kw):
    """注入假訊號(如假 HRV='drop'),測 fusion 不需真感測器。"""
    require_dev(user)
    import time
    session.signals.append({
        "type": signal_type, "label": label,
        "timestamp": time.time(), "phase": session.phase.value,
        "_dev_injected": True, **kw})


def inject_stage_score(user, session, stage, raw_score, **kw):
    """注入假階段分數,測下游(評分/輸出/卡片)不需真跑前面階段。"""
    require_dev(user)
    from core.contract import StageScore
    session.phase_scores[stage] = StageScore(
        stage=stage, raw_score=raw_score, **kw)
```

---

## 各模組的配合點

```
流程引擎      檢查 session.scratch["_dev_no_timer"] → 跳過計時
CostGuard     檢查 session.scratch["_dev_no_cost_cap"] → 跳過成本上限
所有模組       假資料帶 _dev_injected 標記,正式統計時可濾除
帳號          accounts 表加 is_developer 欄位
```

---

## 設計重點

- **獨立工具層,不污染角色**:除錯工具疊加在原本角色之上,開發者可用任何
  角色身分測試,權限不打架。三種角色定義完全不動。
- **雙重安全開關**:開發者帳號 AND 非正式環境,缺一即失效。正式環境永遠
  關閉,即使帳號外洩也動不了學員考試。
- **假資料可溯**:注入的假訊號/假分數都帶 `_dev_injected`,正式研究統計
  時可濾除,避免污染真實資料。
- **加速開發**:模組單測(不跑全流程)、跳階段、關計時、假資料,讓你開發
  vision、測 fusion、demo 時都不必每次從頭跑完整訓練。
- **接 roles-access**:is_developer 是 accounts 表的獨立欄位,與 role 正交
  (任何角色都可標記為開發者),呼應「工具層非角色」。

---

## 設計紀錄

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:獨立除錯工具層 + 雙重安全開關 + 五大能力 | 加速開發/除錯/demo;與角色正交不打架;正式環境安全 |

---

## 驗證方式

1. 開發者帳號 + dev 環境,確認 dev_tools_enabled 為 True。
2. 開發者帳號 + production 環境,確認工具全部失效(雙保險)。
3. 非開發者帳號,確認 require_dev 拒絕。
4. make_test_session 指定 phase="diagnosis",確認直接從診斷階段起。
5. inject_signal 注入假 HRV='drop',確認 fusion 可據此分類,且帶 _dev_injected。
6. disable_limits 後,確認流程引擎跳過計時、CostGuard 跳過上限。
7. cost_breakdown 確認列出每次呼叫成本與 fallback 次數。
```
