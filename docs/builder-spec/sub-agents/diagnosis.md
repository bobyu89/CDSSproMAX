# Sub-Agent: diagnosis — 診斷 Agent

> **權重:標準(單一功能,遵守 core 契約,可熱插拔)。**
> 評核診斷推理:三個診斷、危急度排序、是否善用前面線索。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | diagnosis |
| 模組版本 | v1.0 |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core(contract, session)、llm-adapter |
| 註冊鍵 | "diagnosis" |

> GitHub 路徑:`ticdss/agents/diagnosis_agent.py`。Notion:「TICDSS / diagnosis / v1.0」。

---

## 三大設計決策

| 決策 | 採用方案 |
|------|---------|
| 評核重點 | 推理過程:是否善用問診涵蓋與身評軌跡的線索 |
| 反事實回饋 | 不在本模組;留待 output(報告生成)統一處理 |
| 鑑別診斷 | 三個診斷,按危急度高→低排序,各需原因+結果 |

---

## 評分權重

對應臨床「先排除最致命(rule out worst first)」原則:

| 評核維度 | 權重 | 說明 |
|---------|------|------|
| 第一診斷(最危急) | 40% | 最重要:擺對位置且診斷正確 |
| 第二診斷 | 15% | 鑑別廣度 |
| 第三診斷 | 15% | 鑑別廣度 |
| 危急度排序 | 15% | 是否先想到最致命的可能 |
| 推理運用線索 | 15% | 是否善用問診/身評結果 |

---

## 學員輸入格式

學員給三個診斷,每個含:診斷名稱、原因、結果(預後/後果)。

```python
# DiagnosisPayload(於 contract 定義)
{
  "diagnoses": [
    {"name": "急性心肌梗塞", "reason": "...", "outcome": "..."},   # 最危急
    {"name": "不穩定型心絞痛", "reason": "...", "outcome": "..."},
    {"name": "胃食道逆流", "reason": "...", "outcome": "..."},      # 最不危急
  ]
}
```

---

## 產出檔案:`agents/diagnosis_agent.py`

```python
"""
診斷 Agent
==========
評核三個診斷的危急度排序、第一診斷正確性、推理是否善用前面線索。
評分由 LLM 依結構化標準產出,本模組負責組裝上下文與計算權重。
"""

from core.contract import StageAgent, StageScore
from llm.router import call_llm

WEIGHTS = {
    "dx1": 0.40,        # 第一診斷(最危急)
    "dx2": 0.15,        # 第二診斷
    "dx3": 0.15,        # 第三診斷
    "triage": 0.15,     # 危急度排序
    "reasoning": 0.15,  # 推理運用線索
}


class DiagnosisAgentV1(StageAgent):
    stage_name = "diagnosis"
    rubric_version = "v1.0"

    def on_enter(self, session):
        session.scratch["diagnosis"] = {}
        return {"hint": "請給出三個診斷,從最危急排到最不危急,"
                        "每個說明原因與可能結果"}

    async def handle_input(self, session, payload):
        diagnoses = payload["diagnoses"]    # 三個診斷

        # 組裝上下文:把前面問診、身評的結果交給 LLM,
        # 讓它評學員「有沒有善用這些線索」
        context = self._build_context(session)

        resp = await call_llm(
            "diagnosis",
            prompt=self._eval_prompt(session, diagnoses, context),
            system="你是臨床推理評核專家。依危急度排序原則評分,"
                   "回傳JSON,含各維度分數(0–1)與評語。",
            session=session)

        session.scratch["diagnosis"]["eval"] = resp.text
        return {"feedback": "診斷已記錄"}

    def score(self, session):
        ev = self._parse(session.scratch["diagnosis"].get("eval"))
        # ev 含各維度 0–1 分數
        raw = sum(ev.get(k, 0) * w for k, w in WEIGHTS.items()) * 100

        weak = []
        if ev.get("dx1", 0) < 0.6:
            weak.append("第一診斷(最危急)判斷有誤,未抓住最致命可能")
        if ev.get("triage", 0) < 0.6:
            weak.append("危急度排序不當,未優先考慮致命診斷")
        if ev.get("reasoning", 0) < 0.6:
            weak.append("診斷推理未充分運用問診/身評取得的線索")
        weak.extend(ev.get("extra_weak", []))   # LLM 補充的弱點

        return StageScore(
            stage="diagnosis",
            raw_score=round(raw, 1),
            sub_items={
                "dx1": round(ev.get("dx1", 0) * 100, 1),
                "dx2": round(ev.get("dx2", 0) * 100, 1),
                "dx3": round(ev.get("dx3", 0) * 100, 1),
                "triage": round(ev.get("triage", 0) * 100, 1),
                "reasoning": round(ev.get("reasoning", 0) * 100, 1),
                # 保留 LLM 評語,供 output 反事實回饋取用
                "eval_detail": ev,
            },
            weak_points=weak, signals=[])

    def on_exit(self, session):
        return {"summary": "診斷推理評核完成"}

    # ── 內部方法 ──
    def _build_context(self, session):
        """彙整前面階段結果,讓 LLM 評推理是否善用線索。"""
        inquiry = session.phase_scores.get("inquiry")
        exam = session.phase_scores.get("examination")
        return {
            "inquiry_coverage": inquiry.sub_items if inquiry else {},
            "exam_trajectory": (exam.sub_items.get("trajectory")
                                if exam else []),
        }

    def _eval_prompt(self, session, diagnoses, context):
        return (f"情境:{session.scenario_id}\n"
                f"學員問診涵蓋:{context['inquiry_coverage']}\n"
                f"學員身評軌跡:{context['exam_trajectory']}\n"
                f"學員三個診斷(已按其宣稱的危急度排序):\n{diagnoses}\n\n"
                f"請評核:\n"
                f"1. dx1/dx2/dx3:各診斷的正確性(0–1)\n"
                f"2. triage:危急度排序是否正確(最致命的有無擺第一)\n"
                f"3. reasoning:推理是否善用上述問診/身評線索\n"
                f"4. extra_weak:其他需改進處(陣列)\n"
                f"以JSON回傳。")

    def _parse(self, txt):
        import json
        try:
            return json.loads(txt)
        except Exception:
            return {}
```

---

## 註冊(熱插拔)

```python
from core.flow import registry
from agents.diagnosis_agent import DiagnosisAgentV1
registry.register("diagnosis", DiagnosisAgentV1)
```

---

## 設計重點

- **第一診斷權重最高(40%)**:體現臨床「先排除最致命」原則。學員必須
  先想到會死人的診斷,不能漏。
- **評推理而非只評答案**:`_build_context` 把問診涵蓋與身評軌跡交給 LLM,
  評學員「有沒有用這些線索推診斷」,而非孤立看答案對錯。
- **反事實素材留給 output**:`sub_items["eval_detail"]` 保留 LLM 完整評語,
  output 模組做反事實回饋(「若你當時問了敏史…」)時直接取用,
  本模組不重複處理,職責清晰。
- **三軌串接的終點**:診斷讀取 `session.phase_scores` 裡前兩軌的結果,
  是三軌評分串起來的收尾。

---

## 設計紀錄(同步 Notion / GitHub)

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:三診斷 + 危急度排序 + 推理運用線索評核 | 三大決策定稿,第一診斷 40% 權重 |

---

## 驗證方式

1. 給三個診斷,第一個是正確的最危急診斷,確認 dx1 高分。
2. 把最危急診斷擺第三位,確認 triage 分數下降、弱點標「排序不當」。
3. 診斷推理未用到問診線索,確認 reasoning 低分、對應弱點出現。
4. 確認 StageScore 含 dx1/dx2/dx3/triage/reasoning 五個 sub_items。
5. 確認 eval_detail 完整保留,供後續 output 反事實回饋取用。
```
