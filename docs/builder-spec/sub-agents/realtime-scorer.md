# Sub-Agent: realtime-scorer — 即時評分器

> **權重:標準(評分機制入口,被訓練迴圈在節點結束時呼叫)。**
> 練習模式中,每個操作節點結束後立即給分 + 一句回饋。60% 確定性 + 40% 語義。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | realtime-scorer |
| 模組版本 | v1.0 |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core(contract, session)、llm-adapter |
| 被依賴模組 | 訓練迴圈(練習模式) |
| 輸出格式 | EvalResult(非 StageScore) |

> GitHub 路徑:`ticdss/scoring/realtime.py`。Notion:「TICDSS / realtime-scorer / v1.0」。

---

## 三大設計決策

| 決策 | 採用方案 |
|------|---------|
| 回饋程度 | 分數 + 一句簡短回饋(求快,不拖慢流程) |
| 評分機制 | 60% 確定性規則 + 40% LLM 語義 |
| 模式區別 | 僅練習模式即時給分;考試模式不給(全程結束才由 DUAT 評) |

---

## 即時 vs 深度的分工

| | realtime-scorer(本模組) | DUAT(後續做) |
|--|--------------------------|----------------|
| 時機 | 每個節點結束,立即 | 整個迴圈結束 |
| 速度 | 快(數秒) | 慢(多代理人) |
| 深度 | 淺,給方向 | 深,交叉驗證 |
| 模式 | 僅練習 | 練習與考試皆有 |
| 輸出 | EvalResult | 完整報告 |

> 對應 Kahneman 雙歷程:realtime = System 1(快、直覺),DUAT = System 2(慢、分析)。

---

## 60% 確定性 + 40% 語義

- **確定性(60%)**:來自各 Agent 已算好的 `StageScore.raw_score`,
  是規則明確的部分(問診涵蓋率、身評位置正確率等),不需再呼叫 LLM。
- **語義(40%)**:LLM 評「規則抓不到的品質」——表達清晰度、臨床合理性等。

---

## 產出檔案

### `scoring/realtime.py`

```python
"""
即時評分器
==========
練習模式中,節點結束後立即給分 + 一句回饋。
60% 確定性(用既有 StageScore)+ 40% LLM 語義。
輸出 EvalResult(對「階段表現」的評估加工)。
"""

from core.contract import EvalResult
from llm.router import call_llm


async def realtime_score(session, stage_score, context: str = ""):
    """
    主入口:對剛結束的節點即時評分。
    stage_score: 該節點 Agent 算好的 StageScore(確定性部分)。
    context:     供 LLM 評語義的簡短情境描述。
    """
    # 考試模式不即時給分
    if session.mode == "exam":
        return None

    # ── 60% 確定性 ──
    deterministic = stage_score.raw_score        # 0–100,已算好

    # ── 40% LLM 語義 ──(只評規則抓不到的品質)
    resp = await call_llm(
        "dialog",
        prompt=(f"以下是學員在『{stage_score.stage}』階段的表現:\n{context}\n"
                f"請就『表達清晰度與臨床合理性』給 0–100 分,"
                f"並用一句話(20字內)回饋。"
                f'回傳JSON:{{"semantic":分數,"feedback":"一句話"}}'),
        session=session)
    parsed = _parse(resp.text)
    semantic = parsed.get("semantic", deterministic)   # 解析失敗則退回確定性
    feedback = parsed.get("feedback", "繼續保持")

    # ── 混合 ──
    final = round(deterministic * 0.6 + semantic * 0.4, 1)

    return EvalResult(
        source="realtime-scorer",
        payload={
            "stage": stage_score.stage,
            "score": final,
            "deterministic": deterministic,
            "semantic": semantic,
            "feedback": feedback,          # 一句簡短回饋
        })


def _parse(txt):
    import json
    try:
        return json.loads(txt)
    except Exception:
        return {}
```

---

## 訓練迴圈怎麼用

練習模式中,每個階段 Agent 的 `score()` 算完 StageScore 後:

```python
from scoring.realtime import realtime_score

stage_score = agent.score(session)
result = await realtime_score(session, stage_score, context=summary)
if result:                                   # 考試模式回 None
    send_to_frontend({"realtime": result.payload})   # 立即顯示分數+回饋
```

---

## 設計重點

- **確定性免費、語義才花錢**:60% 直接用 Agent 算好的 StageScore,
  不重複運算也不呼叫 LLM;只有 40% 語義部分動用一次 LLM,且要求 20 字內
  回饋,控制 token 與延遲。
- **求快**:回饋限一句、語義只問一個面向,確保節點間不卡頓。
- **考試模式直接回 None**:考試不即時給分,避免影響考生心理,
  全程結束才由 DUAT 評。對應你「考試模式不給」的決策。
- **輸出 EvalResult 而非 StageScore**:本模組是「對表現的評估加工」,
  用 EvalResult;StageScore 留給階段 Agent。符合 core 契約的格式分流。
- **語義解析失敗有退路**:LLM 回傳壞掉時退回確定性分數,不讓流程中斷。

---

## 設計紀錄(同步 Notion / GitHub)

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:60/40 混合 + 一句回饋,僅練習模式 | 三大決策定稿,確定性免費、語義控成本 |

---

## 驗證方式

1. 練習模式餵入 StageScore(raw=80),LLM 語義回 70,確認 final=76(80×0.6+70×0.4)。
2. 考試模式呼叫,確認回傳 None,不給即時分。
3. LLM 回傳壞 JSON,確認 semantic 退回確定性分數,不中斷。
4. 確認回饋為一句短句,EvalResult.source 為 "realtime-scorer"。
```
