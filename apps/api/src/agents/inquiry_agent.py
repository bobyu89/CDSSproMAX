"""
問診 Agent (Builder inquiry.md / contract-v1.0)
================================================
繼承 StageAgent,實作問診階段。
評分含兩個維度:LQQOPERA 涵蓋率 + 問診品質(深入追問程度)。
檢核採混合策略:關鍵字先行(約 80%),模糊時才用 LLM(約 20%)。
停頓訊號改呼叫 signals.pause(正式化,取代直接 append)。
"""

from __future__ import annotations

from src.core.contract import StageAgent, StageScore
from src.llm.router import call_llm
from src.signals import pause as pause_signal

LQQOPERA = [
    "location", "quality", "quantity", "onset",
    "precipitating", "extension", "relieving", "associated",
]

# 每個維度的關鍵字(約 80% 情況靠這個快速判斷)
DIMENSION_KEYWORDS = {
    "location": ["哪裡", "位置", "部位", "哪個地方"],
    "quality": ["怎麼樣的痛", "什麼感覺", "刺痛", "悶痛", "絞痛"],
    "quantity": ["多痛", "幾分", "程度", "嚴重"],
    "onset": ["什麼時候", "多久", "何時開始", "發作"],
    "precipitating": ["什麼情況", "誘發", "加重", "什麼時候會"],
    "extension": ["會不會傳到", "擴散", "轉移", "延伸"],
    "relieving": ["怎樣會比較好", "緩解", "休息", "吃藥"],
    "associated": ["還有沒有", "伴隨", "其他症狀", "合併"],
}


class InquiryAgentV1(StageAgent):
    stage_name = "inquiry"
    rubric_version = "v1.0"

    def on_enter(self, session):
        session.scratch["inquiry"] = {"covered": set(), "depth": {}, "turns": 0}
        return {"hint": "請開始問診,記得邊問邊說出你要評估的項目"}

    async def handle_input(self, session, payload):
        text = payload["text"]
        silence = payload.get("silence", 0)
        state = session.scratch["inquiry"]
        state["turns"] += 1

        # 1. 停頓訊號 → 經 signals.pause 正式化採集
        if silence and silence > 0:
            ts = float(state["turns"])  # 以回合序當相對時間戳(無真實時鐘時)
            pause_signal.collect_and_classify(session, duration=silence, timestamp=ts)

        # 2. anxiety 更新(僅練習模式)
        if session.mode == "practice":
            session.anxiety = self._update_anxiety(session.anxiety, payload.get("prosody"))

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
            session=session,
        )
        coverage = len(state["covered"]) / len(LQQOPERA)
        return {"reply": resp.text, "coverage": round(coverage, 2)}

    def score(self, session):
        state = session.scratch["inquiry"]
        covered = state["covered"]

        coverage = len(covered) / len(LQQOPERA)
        deep = sum(1 for d in covered if state["depth"].get(d, 0) > 1)
        quality = deep / len(LQQOPERA)
        raw = (coverage * 0.7 + quality * 0.3) * 100

        weak = [f"問診遺漏:{d}" for d in LQQOPERA if d not in covered]
        shallow = [
            f"問診不夠深入:{d}" for d in covered if state["depth"].get(d, 0) == 1
        ]
        return StageScore(
            stage="inquiry",
            raw_score=round(raw, 1),
            sub_items={
                "coverage": round(coverage * 100, 1),
                "quality": round(quality * 100, 1),
                "dimensions": {d: (d in covered) for d in LQQOPERA},
            },
            weak_points=weak + shallow,
            signals=[s for s in session.signals if s.get("phase") == "inquiry"],
        )

    def on_exit(self, session):
        state = session.scratch["inquiry"]
        return {
            "summary": f"問診涵蓋 {len(state['covered'])}/8 維度,共 {state['turns']} 個回合"
        }

    # ── 內部方法 ──
    async def _detect_dimensions(self, text, session):
        """混合檢核:關鍵字先行(80%),模糊時 LLM(20%)。"""
        hit = set()
        for dim, kws in DIMENSION_KEYWORDS.items():
            if any(kw in text for kw in kws):
                hit.add(dim)

        if not hit and len(text) > 6:
            resp = await call_llm(
                "inquiry",
                prompt=f"這句問診話語涵蓋 LQQOPERA 哪些維度(可多個或無)?"
                f"只回維度英文代碼,逗號分隔:{text}",
                session=session,
            )
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
        return (
            f"你是標準化病人。情境:{session.scenario_id}。"
            f"當前情緒:{tone}。只回答被問到的,不主動爆料。"
        )
