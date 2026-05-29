# Sub-Agent: inquiry — 問診 Agent

> **權重:標準(單一功能,遵守 core 契約,可熱插拔)。**
> 問診階段的虛擬病人對話與 LQQOPERA 評核。

---

## 版本控管

| 欄位 | 內容 |
|------|------|
| 模組名稱 | inquiry |
| 模組版本 | v1.0 |
| 契約版本 | contract-v1.0 |
| 最後更新 | 2026-05-29 |
| 相依模組 | core(contract, session)、llm-adapter |
| 註冊鍵 | "inquiry" |

> GitHub 路徑:`ticdss/agents/inquiry_agent.py`。Notion:「TICDSS / inquiry / v1.0」。

---

## 三大設計決策

| 決策 | 採用方案 |
|------|---------|
| LQQOPERA 檢核 | 混合:關鍵字先行(約 80%),模糊時才呼叫 LLM 語義判斷(約 20%) |
| 評分維度 | 涵蓋率 + 問診品質(是否深入追問);不評順序 |
| anxiety 動態 | 第一版即做,虛擬病人語氣隨學員語速/音量變化(練習模式) |

---

## LQQOPERA 八維度

Location(位置)、Quality(性質)、Quantity(程度)、Onset(發作時間)、
Precipitating/Palliating(誘發/緩解因子)、Extension(擴散)、
Relieving(緩解方式)、Associated symptoms(伴隨症狀)。

---

## 產出檔案:`agents/inquiry_agent.py`

```python
"""
問診 Agent
==========
繼承 StageAgent,實作問診階段。
評分含兩個維度:LQQOPERA 涵蓋率 + 問診品質(深入追問程度)。
檢核採混合策略:關鍵字先行,模糊時才用 LLM。
"""

from core.contract import StageAgent, StageScore
from core.session import TrainingSession
from llm.router import call_llm

LQQOPERA = ["location", "quality", "quantity", "onset",
            "precipitating", "extension", "relieving", "associated"]

# 每個維度的關鍵字(約 80% 情況靠這個快速判斷)
DIMENSION_KEYWORDS = {
    "location":      ["哪裡", "位置", "部位", "哪個地方"],
    "quality":       ["怎麼樣的痛", "什麼感覺", "刺痛", "悶痛", "絞痛"],
    "quantity":      ["多痛", "幾分", "程度", "嚴重"],
    "onset":         ["什麼時候", "多久", "何時開始", "發作"],
    "precipitating": ["什麼情況", "誘發", "加重", "什麼時候會"],
    "extension":     ["會不會傳到", "擴散", "轉移", "延伸"],
    "relieving":     ["怎樣會比較好", "緩解", "休息", "吃藥"],
    "associated":    ["還有沒有", "伴隨", "其他症狀", "合併"],
}


class InquiryAgentV1(StageAgent):
    stage_name = "inquiry"
    rubric_version = "v1.0"

    # ── 生命週期 ──
    def on_enter(self, session: TrainingSession):
        # 用 scratch 暫存區存問診狀態,不污染 session 主結構
        session.scratch["inquiry"] = {
            "covered": set(),        # 已涵蓋的維度
            "depth": {},             # 各維度的追問深度(問了幾次)
            "turns": 0,              # 總問診回合數
        }
        return {"hint": "請開始問診,記得邊問邊說出你要評估的項目"}

    async def handle_input(self, session, payload):
        # payload 格式見 contract.InquiryPayload
        text = payload["text"]
        silence = payload.get("silence", 0)
        state = session.scratch["inquiry"]
        state["turns"] += 1

        # 1. 停頓訊號 → 寫入 signals(供 fusion 模組)
        if silence > 5:
            session.signals.append(
                {"phase": "inquiry", "type": "pause", "value": silence})

        # 2. anxiety 更新(僅練習模式)
        if session.mode == "practice":
            session.anxiety = self._update_anxiety(
                session.anxiety, payload.get("prosody"))

        # 3. 混合檢核:先關鍵字,模糊時才 LLM
        hit = await self._detect_dimensions(text, session)
        for dim in hit:
            state["covered"].add(dim)
            state["depth"][dim] = state["depth"].get(dim, 0) + 1

        # 4. 生成病人回應(語氣受 anxiety 影響)
        resp = await call_llm(
            "dialog",
            prompt=self._patient_prompt(session, text),
            system=self._persona(session),
            session=session)

        coverage = len(state["covered"]) / len(LQQOPERA)
        return {"reply": resp.text, "coverage": round(coverage, 2)}

    def score(self, session):
        state = session.scratch["inquiry"]
        covered = state["covered"]

        # 維度一:涵蓋率
        coverage = len(covered) / len(LQQOPERA)

        # 維度二:問診品質(深入追問)
        # 有追問(同維度問 >1 次)的維度比例
        deep = sum(1 for d in covered if state["depth"].get(d, 0) > 1)
        quality = deep / len(LQQOPERA)

        # 綜合:涵蓋率 70% + 品質 30%
        raw = (coverage * 0.7 + quality * 0.3) * 100

        weak = [f"問診遺漏:{d}" for d in LQQOPERA if d not in covered]
        shallow = [f"問診不夠深入:{d}" for d in covered
                   if state["depth"].get(d, 0) == 1]

        return StageScore(
            stage="inquiry",
            raw_score=round(raw, 1),
            sub_items={
                "coverage": round(coverage * 100, 1),
                "quality":  round(quality * 100, 1),
                "dimensions": {d: (d in covered) for d in LQQOPERA},
            },
            weak_points=weak + shallow,
            signals=[s for s in session.signals if s["phase"] == "inquiry"])

    def on_exit(self, session):
        state = session.scratch["inquiry"]
        return {"summary": f"問診涵蓋 {len(state['covered'])}/8 維度,"
                           f"共 {state['turns']} 個回合"}

    # ── 內部方法 ──
    async def _detect_dimensions(self, text, session):
        """混合檢核:關鍵字先行(80%),模糊時 LLM(20%)。"""
        hit = set()
        # 第一層:關鍵字快速比對
        for dim, kws in DIMENSION_KEYWORDS.items():
            if any(kw in text for kw in kws):
                hit.add(dim)

        # 第二層:若這句話沒命中任何關鍵字,但長度夠(像個問題),
        # 才動用 LLM 語義判斷,避免每句都呼叫 LLM
        if not hit and len(text) > 6:
            resp = await call_llm(
                "dialog",
                prompt=f"這句問診話語涵蓋 LQQOPERA 哪些維度(可多個或無)?"
                       f"只回維度英文代碼,逗號分隔:{text}",
                session=session)
            for d in resp.text.lower().replace(" ", "").split(","):
                if d in LQQOPERA:
                    hit.add(d)
        return hit

    def _update_anxiety(self, current, prosody):
        if prosody is None:
            return current
        delta = 0.1 if prosody.get("fast") else -0.05
        return max(0.0, min(1.0, current + delta))

    def _patient_prompt(self, session, student_text):
        return f"學員問:{student_text}\n請以病人身分,用一句話回應。"

    def _persona(self, session):
        if session.mode == "exam":
            tone = "標準化、語氣平穩、據實回答"
        else:
            tone = "緊張、回答簡短" if session.anxiety > 0.6 else "平穩、配合"
        return (f"你是標準化病人。情境:{session.scenario_id}。"
                f"當前情緒:{tone}。只回答被問到的,不主動爆料。")
```

---

## 註冊(熱插拔)

```python
from core.flow import registry
from agents.inquiry_agent import InquiryAgentV1
registry.register("inquiry", InquiryAgentV1)
# 升級:registry.register("inquiry", InquiryAgentV2)
```

---

## 設計重點

- **混合檢核省成本**:關鍵字先擋掉約 80% 情況,只有沒命中且像問題的句子
  才呼叫 LLM。避免每句問診都燒 token。
- **品質維度的定義**:同一維度問超過一次 = 有深入追問。這是簡化但可操作的
  「問診品質」量化方式,正式版可再精緻化。
- **anxiety 只在練習模式變化**:考試模式為標準化病人,語氣固定,確保公平。
- **停頓訊號寫入 session.signals**:供 fusion 模組取用,模組間靠 session 解耦。
- **狀態放 scratch**:問診的中間狀態(covered/depth/turns)放在
  `session.scratch["inquiry"]`,不污染 session 主結構。

---

## 設計紀錄(同步 Notion / GitHub)

| 日期 | 版本 | 變更 | 原因 |
|------|------|------|------|
| 2026-05-29 | v1.0 | 初版:混合檢核 + 涵蓋率/品質雙維度 + anxiety 動態 | 三大決策定稿 |

---

## 驗證方式

1. 餵入含「哪裡痛」的句子,確認關鍵字命中 location,不呼叫 LLM。
2. 餵入語義模糊但像問題的句子,確認觸發 LLM 第二層判斷。
3. 同一維度問兩次,確認 quality 分數上升。
4. 練習模式餵入快語速 prosody,確認 anxiety 上升、病人 persona 變緊張。
5. 確認 score() 回傳的 StageScore 含 coverage 與 quality 兩個 sub_items。
