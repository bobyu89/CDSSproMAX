"""Training-flow 流程 API — 把 builder 熱插拔引擎接進 HTTP。

驅動 core.registry 的三軌 StageAgent + scoring.realtime + scoring.duat.deep_verify
+ output。前端逐階段呼叫(REST 版的 run_phase),而非 server 端 streaming。

流程:
  POST /training/sessions                建立 TrainingSession(in-memory)
  GET  /training/registry                列出已熱插拔的 stage agents(證明可插拔)
  GET  /training/sessions/{tid}/state     當前 phase + 已完成階段分數
  POST /training/sessions/{tid}/advance   推進到下一 phase,回該 phase 的 on_enter
  POST /training/sessions/{tid}/input     送 payload 給當前 phase 的 agent.handle_input
  POST /training/sessions/{tid}/score     當前 phase agent.score → 存 phase_scores(+ 練習模式即時分)
  POST /training/sessions/{tid}/finalize  跑 DUAT 深度驗證 + 六輸出 + 雙卡

註:TrainingSession 為執行期 in-memory 狀態;持久化(寫 sessions 表/JSONL)為 follow-up。
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.agents.stage_registry import register_stage_agents
from src.core.contract import CONTRACT_VERSION
from src.core.registry import registry
from src.core.session_state import Phase, TrainingSession
from src.routers.auth import get_current_participant
from src.db.models import Participant

router = APIRouter(prefix="/training", tags=["training"])

# 執行期 session 暫存(Wave 後續可移到 Redis / 持久化)
_SESSIONS: dict[str, TrainingSession] = {}


def _get(tid: str) -> TrainingSession:
    sess = _SESSIONS.get(tid)
    if sess is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="training session not found")
    return sess


# ─── Schemas ───────────────────────────────────────────────────────────────


class CreateTrainingRequest(BaseModel):
    mode: str = "practice"  # practice | exam
    scenario_id: str
    standard_sequence: list[str] | None = None  # 身評標準順序(供 vision 順序評分)
    stress_monitoring: bool = False


class CreateTrainingResponse(BaseModel):
    training_id: str
    phase: str
    mode: str
    registered_stages: list[str]


class InputRequest(BaseModel):
    payload: dict


# ─── Routes ──────────────────────────────────────────────────────────────────


@router.get("/registry")
async def list_registry() -> dict:
    """列出已熱插拔的 stage agents — 證明 builder 套件確實插進引擎。"""
    register_stage_agents()  # idempotent
    return {
        "contract_version": CONTRACT_VERSION,
        "registered_stages": registry.registered_stages(),
    }


@router.post("/sessions", response_model=CreateTrainingResponse)
async def create_training_session(
    payload: CreateTrainingRequest,
    _: Participant = Depends(get_current_participant),
) -> CreateTrainingResponse:
    register_stage_agents()
    tid = str(uuid.uuid4())
    sess = TrainingSession(mode=payload.mode, scenario_id=payload.scenario_id)
    if payload.standard_sequence:
        sess.scratch["standard_sequence"] = payload.standard_sequence
    sess.scratch["stress_monitoring_enabled"] = payload.stress_monitoring
    _SESSIONS[tid] = sess
    return CreateTrainingResponse(
        training_id=tid,
        phase=sess.phase.value,
        mode=sess.mode,
        registered_stages=registry.registered_stages(),
    )


@router.get("/sessions/{tid}/state")
async def get_state(tid: str, _: Participant = Depends(get_current_participant)) -> dict:
    sess = _get(tid)
    return {
        "phase": sess.phase.value,
        "mode": sess.mode,
        "difficulty": sess.difficulty,
        "anxiety": sess.anxiety,
        "phase_scores": {
            k: getattr(v, "raw_score", None) for k, v in sess.phase_scores.items()
        },
        "llm_cost": sess.scratch.get("llm_cost", 0.0),
    }


@router.post("/sessions/{tid}/advance")
async def advance(tid: str, _: Participant = Depends(get_current_participant)) -> dict:
    sess = _get(tid)
    new_phase = sess.advance()
    agent = registry.get_agent(new_phase.value)
    enter_state = agent.on_enter(sess) if agent else None
    return {
        "phase": new_phase.value,
        "time_limit_s": sess.time_limit(),
        "enter": enter_state,
        "has_agent": agent is not None,
    }


@router.post("/sessions/{tid}/input")
async def submit_input(
    tid: str,
    body: InputRequest,
    _: Participant = Depends(get_current_participant),
) -> dict:
    sess = _get(tid)
    agent = registry.get_agent(sess.phase.value)
    if agent is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"phase '{sess.phase.value}' has no registered agent",
        )
    resp = await agent.handle_input(sess, body.payload)
    return {"phase": sess.phase.value, "response": resp}


@router.post("/sessions/{tid}/score")
async def score_phase(
    tid: str,
    _: Participant = Depends(get_current_participant),
) -> dict:
    """當前 phase 評分 → 存 phase_scores;練習模式附即時分(60%規則+40%語義)。"""
    from src.scoring.realtime import realtime_score

    sess = _get(tid)
    agent = registry.get_agent(sess.phase.value)
    if agent is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"phase '{sess.phase.value}' has no registered agent",
        )
    stage_score = agent.score(sess)
    sess.phase_scores[sess.phase.value] = stage_score
    summary = agent.on_exit(sess)

    realtime = None
    rt = await realtime_score(sess, stage_score, context=str(summary))
    if rt is not None:
        realtime = rt.payload

    return {
        "phase": sess.phase.value,
        "stage_score": {
            "stage": stage_score.stage,
            "raw_score": stage_score.raw_score,
            "sub_items": stage_score.sub_items,
            "weak_points": stage_score.weak_points,
        },
        "summary": summary,
        "realtime": realtime,  # 考試模式為 None
    }


@router.post("/sessions/{tid}/finalize")
async def finalize(
    tid: str,
    _: Participant = Depends(get_current_participant),
) -> dict:
    """整場結束:DUAT 深度驗證(O→E‖S→A→M + 驗證層)→ 六輸出 → 雙卡。"""
    from src.output import build_all_outputs, build_cornell_report
    from src.rag.note import generate_cards
    from src.scoring.duat import deep_verify

    sess = _get(tid)
    if not sess.phase_scores:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="no phase scored yet — finalize aborted"
        )

    duat = await deep_verify(sess, student_id=None)
    outputs = await build_all_outputs(sess, duat)
    cards = await generate_cards(sess, outputs["weakness"], duat)
    report = build_cornell_report(outputs, cards)

    return {
        "outputs": outputs,
        "rag_cards": cards,
        "cornell_report": report,
        "verification": duat["verification"].payload,  # 研究亮點:對抗+Arbiter
        "audit_events": sess.scratch.get("audit_events", []),
        "llm_cost": sess.scratch.get("llm_cost", 0.0),
    }
