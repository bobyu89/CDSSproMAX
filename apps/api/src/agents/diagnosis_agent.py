"""
診斷 Agent (Builder diagnosis.md / contract-v1.0)
==================================================
評核三個診斷的危急度排序、第一診斷正確性、推理是否善用前面線索。
評分由 LLM 依結構化標準產出,本模組負責組裝上下文與計算權重。
"""

from __future__ import annotations

import json

from src.core.contract import StageAgent, StageScore
from src.llm.router import call_llm

WEIGHTS = {
    "dx1": 0.40,  # 第一診斷(最危急)
    "dx2": 0.15,
    "dx3": 0.15,
    "triage": 0.15,  # 危急度排序
    "reasoning": 0.15,  # 推理運用線索
}


class DiagnosisAgentV1(StageAgent):
    stage_name = "diagnosis"
    rubric_version = "v1.0"

    def on_enter(self, session):
        session.scratch["diagnosis"] = {}
        return {"hint": "請給出三個診斷,從最危急排到最不危急,每個說明原因與可能結果"}

    async def handle_input(self, session, payload):
        diagnoses = payload["diagnoses"]  # 三個診斷
        context = self._build_context(session)
        resp = await call_llm(
            "diagnosis",
            prompt=self._eval_prompt(session, diagnoses, context),
            system="你是臨床推理評核專家。依危急度排序原則評分,"
            "回傳JSON,含各維度分數(0–1)與評語。",
            session=session,
            json_mode=True,
        )
        session.scratch["diagnosis"]["eval"] = resp.text
        session.scratch["diagnosis"]["diagnoses"] = diagnoses
        return {"feedback": "診斷已記錄"}

    def score(self, session):
        ev = self._parse(session.scratch.get("diagnosis", {}).get("eval"))
        raw = sum(ev.get(k, 0) * w for k, w in WEIGHTS.items()) * 100

        weak = []
        if ev.get("dx1", 0) < 0.6:
            weak.append("第一診斷(最危急)判斷有誤,未抓住最致命可能")
        if ev.get("triage", 0) < 0.6:
            weak.append("危急度排序不當,未優先考慮致命診斷")
        if ev.get("reasoning", 0) < 0.6:
            weak.append("診斷推理未充分運用問診/身評取得的線索")
        extra = ev.get("extra_weak", [])
        if isinstance(extra, list):
            weak.extend(str(x) for x in extra)

        return StageScore(
            stage="diagnosis",
            raw_score=round(raw, 1),
            sub_items={
                "dx1": round(ev.get("dx1", 0) * 100, 1),
                "dx2": round(ev.get("dx2", 0) * 100, 1),
                "dx3": round(ev.get("dx3", 0) * 100, 1),
                "triage": round(ev.get("triage", 0) * 100, 1),
                "reasoning": round(ev.get("reasoning", 0) * 100, 1),
                "eval_detail": ev,  # 保留 LLM 評語,供 output 反事實回饋
            },
            weak_points=weak,
            signals=[],
        )

    def on_exit(self, session):
        return {"summary": "診斷推理評核完成"}

    # ── 內部方法 ──
    def _build_context(self, session):
        inquiry = session.phase_scores.get("inquiry")
        exam = session.phase_scores.get("examination")
        return {
            "inquiry_coverage": inquiry.sub_items if inquiry else {},
            "exam_trajectory": (exam.sub_items.get("trajectory") if exam else []),
        }

    def _eval_prompt(self, session, diagnoses, context):
        return (
            f"情境:{session.scenario_id}\n"
            f"學員問診涵蓋:{context['inquiry_coverage']}\n"
            f"學員身評軌跡:{context['exam_trajectory']}\n"
            f"學員三個診斷(已按其宣稱的危急度排序):\n{diagnoses}\n\n"
            f"請評核:\n"
            f"1. dx1/dx2/dx3:各診斷的正確性(0–1)\n"
            f"2. triage:危急度排序是否正確(最致命的有無擺第一)\n"
            f"3. reasoning:推理是否善用上述問診/身評線索\n"
            f"4. extra_weak:其他需改進處(陣列)\n"
            f"以JSON回傳。"
        )

    def _parse(self, txt):
        if not txt:
            return {}
        try:
            return json.loads(txt)
        except Exception:  # noqa: BLE001
            return {}
