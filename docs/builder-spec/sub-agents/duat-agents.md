# Sub-Agent: DUAT 五代理(observe / evaluate / synthesize / analyze / memory)

> **權重:標準(各為獨立評分代理,遵守 core 契約,可熱插拔)。**
> 五個代理串接成深度驗證。皆用 LLM,輸出 EvalResult。
> 本檔含五個代理規格,實作時各自為獨立檔案。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組群 | duat-observe / duat-evaluate / duat-synthesize / duat-analyze / duat-memory |
| 模組版本 | v1.0 |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core(contract, session)、llm-adapter、duat-flow |

> GitHub 路徑:`ticdss/scoring/duat/`。Notion:各代理一頁,如「TICDSS / duat-observe / v1.0」。

---

## 五代理職責一覽

| 代理 | 角色 | 輸入 | 輸出重點 |
|------|------|------|---------|
| O 觀察 | 彙整全程客觀資料 | session | 三軌分數、軌跡、訊號的結構化彙整 |
| E 評估 | 依 Rubric 逐項打分 | O | 各項目的評分與依據 |
| S 綜整 | 三軌整合成整體評價 | O | 跨軌的整體表現敘述 |
| A 分析 | 找弱點與錯誤模式 | E + S | 弱點清單、錯誤模式、原因 |
| M 記憶 | 比對歷程、個人化敘事 | A + 歷程 | 進步/退步、老問題、鼓勵 |

---

## 設計理念:為什麼拆五個,不用一個

可以叫一個 LLM「看完訓練給評分和建議」,但**一次做太多事,每件都做不好**。
就像不會要一個人同時當記錄員、考官、總評老師、診斷專家、班導師。
拆開後每個代理只專心一件事,品質才高,且各自思考角度不同,合起來才周全。
這對應 Kahneman System 2——慢、分步驟、刻意的深度思考。

五個代理模仿一個好臨床教師的完整評核思路:
**客觀記錄 → 逐項評 → 退一步看整體 → 挖出根源 → 結合成長軌跡。**

### O — 觀察(中立地基)
把整場訓練整理成「事實清單」,不評價、不打分。
價值:讓後面每個代理拿到同一份中立資料,避免先入為主、帶情緒看後面。
輸出範例:「問診涵蓋 6/8,遺漏誘發因子;身評依序視→聽→叩→觸,
左下肺位置偏移;第 4 分鐘 HRV 驟降持續 40 秒。」(全是事實,無好壞judgment)

### E — 評估(細部裁判)
拿 Rubric 對每一項逐條打分 + 依據。只管「每項對照標準做得如何」,粒度細。
輸出範例:「問診 75(涵蓋夠但未追問誘發因子);身評 70(順序對但位置偏移);
診斷 85(第一診斷正確抓到最危急)。」

### S — 綜整(全局視角,與 E 互補並行)
退一步看三軌是否「連貫的一個故事」。E 看每項分數,S 看整體連不連貫。
範例:學員問到胸痛、身評卻沒聽心音、診斷又跳回心臟——每項單看及格(E 不低分),
但整體推理斷裂——這「斷裂」只有 S 看得到。因都只依賴 O,故與 E 並行省時。

### A — 分析(找根源,最有教學價值)
不只「哪裡錯」,而是「為什麼錯、什麼類型的錯」。是反事實回饋與個人化講義的素材。
範例:「弱點:問診未追問誘發因子,可能不熟 LQQOPERA 的 P 維度;
錯誤模式:傾向跳過動態問題;此模式在身評也出現——只做靜態檢查。」
價值:找到橫跨問診與身評的共同模式,這是深度所在。

### M — 記憶(個人化成長敘事,沒歷程也能跑)
比對過去,產出成長敘事,讓系統「記得你」。
- 第一次:「這是你第一次訓練,診斷排序表現亮眼,未來多注意問診完整性,
我會記住,下次告訴你進步多少。」
- 第二次起:「問診涵蓋率從 6/8 進步到 8/8,很好!但『誘發因子』老問題又出現,
這是第三次了,建議專門練習。」
讓 M 從第一天可用,隨資料累積越有價值。

### 完整串接範例(胸痛案例)
```
O:記錄「問診6/8、身評左下肺偏移、診斷心肌梗塞排第一、第4分鐘HRV驟降」(事實)
  ↓
E:問診75、身評70、診斷85(逐項)    S:「推理鏈完整,但漏了冷汗線索的檢查」(全局)
  └────────────── 並行 ──────────────┘
  ↓
A:「弱點:跳過動態問題;此模式同時出現在問診和身評」(根源)
  ↓
M:「這個『跳過動態評估』問題你上次也有,建議專門練習」(成長)
  ↓
交給 output → 評語、雷達圖、弱點、重點、壓力曲線
```
層層遞進:**事實 → 打分 → 全局 → 根源 → 成長。**

---

## 1. `scoring/duat/observe.py` — O-Agent 觀察

```python
"""
O-Agent 觀察
============
彙整全程客觀資料(不評價,只整理),作為後續代理的共同輸入。
"""

from core.contract import EvalResult
from llm.router import call_llm


async def run_observe(session):
    # 收集三軌分數、軌跡、訊號、fusion 狀態
    raw = {
        "phase_scores": {k: vars(v) for k, v in session.phase_scores.items()},
        "signals": session.signals,
        "fusion_states": [s for s in session.signals
                          if s["type"] == "fusion_state"],
    }
    resp = await call_llm(
        "duat",
        prompt=f"以下是學員一次完整訓練的原始資料:\n{raw}\n"
               f"請客觀彙整為結構化觀察摘要(不評價),回傳JSON。",
        session=session)
    return EvalResult(source="duat-observe",
                      payload={"observation": resp.text, "raw": raw})
```

## 2. `scoring/duat/evaluate.py` — E-Agent 評估

```python
"""
E-Agent 評估
============
依 Rubric 對每一項逐條打分,給出分數與依據。
"""

from core.contract import EvalResult
from llm.router import call_llm


async def run_evaluate(session, observation):
    resp = await call_llm(
        "duat",
        prompt=f"根據觀察摘要:\n{observation.payload['observation']}\n"
               f"請依臨床技能 Rubric 對問診、身評、診斷逐項評分(0–100)"
               f"並附依據。回傳JSON。",
        session=session)
    return EvalResult(source="duat-evaluate",
                      payload={"evaluation": resp.text})
```

## 3. `scoring/duat/synthesize.py` — S-Agent 綜整

```python
"""
S-Agent 綜整
============
把問診/身評/診斷三軌整合成一個整體評價(與 E 並行,都只依賴 O)。
"""

from core.contract import EvalResult
from llm.router import call_llm


async def run_synthesize(session, observation):
    resp = await call_llm(
        "duat",
        prompt=f"根據觀察摘要:\n{observation.payload['observation']}\n"
               f"請將三軌表現整合成一段整體評價,"
               f"說明學員的臨床推理是否連貫(問診→身評→診斷是否一氣呵成)。"
               f"回傳JSON。",
        session=session)
    return EvalResult(source="duat-synthesize",
                      payload={"synthesis": resp.text})
```

## 4. `scoring/duat/analyze.py` — A-Agent 分析

```python
"""
A-Agent 分析
============
依 E + S 找出弱點、錯誤模式與原因(依賴評估與綜整)。
"""

from core.contract import EvalResult
from llm.router import call_llm


async def run_analyze(session, evaluation, synthesis):
    resp = await call_llm(
        "duat",
        prompt=f"評估結果:\n{evaluation.payload['evaluation']}\n"
               f"整體綜整:\n{synthesis.payload['synthesis']}\n"
               f"請找出:1)最關鍵的弱點(排序)2)錯誤模式 3)可能原因。"
               f"回傳JSON,含 weak_points 陣列。",
        session=session)
    return EvalResult(source="duat-analyze",
                      payload={"analysis": resp.text})
```

## 5. `scoring/duat/memory.py` — M-Agent 記憶

```python
"""
M-Agent 記憶
============
比對學員過去歷程,產出個人化敘事。
設計成「沒歷程也能跑」:首次訓練只描述本次,有歷程才比對。
"""

from core.contract import EvalResult
from llm.router import call_llm


def _load_history(student_id):
    """讀取學員過去的 A-Agent 分析紀錄。無則回空。"""
    if student_id is None:
        return []
    # return db.query_past_analyses(student_id, limit=3)
    return []          # 串接資料庫前先回空


async def run_memory(session, analysis, student_id=None):
    history = _load_history(student_id)

    if not history:
        # 首次:沒歷程,只描述本次
        prompt = (f"本次分析:\n{analysis.payload['analysis']}\n"
                  f"這是學員第一次訓練。請用鼓勵語氣描述本次表現重點,"
                  f"並標示未來可追蹤的指標。回傳JSON。")
    else:
        # 有歷程:比對進步/退步/老問題
        prompt = (f"本次分析:\n{analysis.payload['analysis']}\n"
                  f"過去紀錄:\n{history}\n"
                  f"請比對:1)有無進步 2)是否重犯老問題 3)個人化建議。"
                  f"回傳JSON。")

    resp = await call_llm("duat", prompt=prompt, session=session)

    # 本次分析存入歷程,供未來比對
    # db.save_analysis(student_id, analysis.payload)

    return EvalResult(source="duat-memory",
                      payload={"memory": resp.text,
                               "has_history": bool(history)})
```

---

## 註冊與使用

五代理由 duat-flow 串接呼叫,不需註冊進 AgentRegistry
(它們不是階段 Agent,是評分代理)。

---

## 設計重點

- **O 只觀察不評價**:確保 E、S 拿到的是中立資料,評價的事留給後面,
  避免觀察階段就帶偏見。
- **E 與 S 並行、視角不同**:E 逐項打分(細),S 看整體連貫性(粗),
  兩者互補,都只依賴 O,故可並行。
- **A 找原因不只找錯**:不只列弱點,還要錯誤模式與原因,
  這是反事實回饋與個人化講義的素材來源。
- **M 沒歷程也能跑**:首次訓練只描述本次,有歷程才比對。讓 M 從第一天可用,
  隨資料累積越有價值。
- **全部輸出 EvalResult**:五代理皆遵守 core 契約的評分輸出格式,
  output 模組統一取用。

---

## 設計紀錄

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:五代理 O/E/S/A/M,皆 LLM,M 支援無歷程 | DUAT 整體決策定稿 |

---

## 驗證方式

1. O 輸出含三軌分數、訊號、fusion 狀態的彙整。
2. E 與 S 皆只依賴 O,可並行;E 出逐項分數,S 出整體評價。
3. A 依 E+S 產出 weak_points 陣列與錯誤模式。
4. M 首次訓練(無歷程)只描述本次;模擬有歷程則輸出比對敘事。
5. 五代理輸出皆為 EvalResult,source 正確。
```
