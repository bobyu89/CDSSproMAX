"use client";

import type {
  ArbiterDecision,
  DuatScore,
  Rubric,
  SessionRecord,
  Transcript,
} from "@ticdss/shared-types";
import { useAuthStore } from "./authStore";
import {
  MOCK_DUAT_SCORES,
  MOCK_RUBRIC,
  MOCK_SESSIONS,
  MOCK_TRANSCRIPTS,
} from "./mock";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

// ─── HTTP helpers ────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

function authHeader(): Record<string, string> {
  const token = useAuthStore.getState().token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const resp = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
      ...(init.headers || {}),
    },
    cache: "no-store",
  });
  if (!resp.ok) {
    let detail = "";
    try {
      detail = (await resp.json())?.detail ?? "";
    } catch {
      detail = await resp.text();
    }
    throw new ApiError(resp.status, detail || `HTTP ${resp.status}`);
  }
  return (await resp.json()) as T;
}

// ─── Auth ────────────────────────────────────────────────────────────────

export interface LoginResult {
  token: string;
  expires_at: number;
  participant: {
    id: string;
    participant_code: string;
    role: "student" | "teacher" | "admin";
    name: string;
  };
}

export async function loginApi(code: string, password: string): Promise<LoginResult> {
  return request<LoginResult>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ code, password }),
  });
}

// ─── Sessions ────────────────────────────────────────────────────────────

export async function fetchSessions(): Promise<SessionRecord[]> {
  try {
    const rows = await request<Array<{
      id: string;
      participant_id: string;
      case_id: string;
      case_title?: string | null;
      mode: "practice" | "exam";
      phase: SessionRecord["phase"];
      started_at: string;
      ended_at: string | null;
    }>>("/sessions");
    return rows.map((r) => ({
      id: r.id,
      participantId: r.participant_id,
      caseId: r.case_id,
      mode: r.mode,
      phase: r.phase,
      startedAt: r.started_at,
      endedAt: r.ended_at,
    }));
  } catch {
    return MOCK_SESSIONS;
  }
}

export async function fetchSessionDetail(
  sessionId: string,
): Promise<{ session: SessionRecord; scores: DuatScore[] }> {
  try {
    const session = (await request<{
      id: string;
      participant_id: string;
      case_id: string;
      mode: SessionRecord["mode"];
      phase: SessionRecord["phase"];
      started_at: string;
      ended_at: string | null;
    }>(`/sessions/${sessionId}`));
    const scoresRaw = await request<Array<{
      id: string;
      rubric_item_id: string;
      e_confidence: number | null;
      s_score: number | null;
      a_advocate_score: number | null;
      arbiter_decision: string | null;
      arbiter_confidence: string | null;
      final_score: number | null;
      grader_action: string | null;
    }>>(`/sessions/${sessionId}/duat/scores`);
    return {
      session: {
        id: session.id,
        participantId: session.participant_id,
        caseId: session.case_id,
        mode: session.mode,
        phase: session.phase,
        startedAt: session.started_at,
        endedAt: session.ended_at,
      },
      scores: scoresRaw.map((s) => ({
        id: s.id,
        sessionId,
        rubricItemId: s.rubric_item_id,
        eConfidence: s.e_confidence,
        sScore: s.s_score,
        aAdvocateScore: s.a_advocate_score,
        arbiterDecision: (s.arbiter_decision as DuatScore["arbiterDecision"]) ?? null,
        arbiterConfidence: (s.arbiter_confidence as DuatScore["arbiterConfidence"]) ?? null,
        finalScore: s.final_score,
        graderAction: (s.grader_action as DuatScore["graderAction"]) ?? null,
        graderReason: null,
      })),
    };
  } catch {
    const session = MOCK_SESSIONS.find((s) => s.id === sessionId) ?? MOCK_SESSIONS[0];
    return { session, scores: MOCK_DUAT_SCORES[session.id] ?? [] };
  }
}

export async function createSession(caseId: string, mode: "practice" | "exam"): Promise<SessionRecord> {
  const r = await request<{
    id: string;
    participant_id: string;
    case_id: string;
    mode: "practice" | "exam";
    phase: SessionRecord["phase"];
    started_at: string;
    ended_at: string | null;
  }>("/sessions", {
    method: "POST",
    body: JSON.stringify({ case_id: caseId, mode }),
  });
  return {
    id: r.id,
    participantId: r.participant_id,
    caseId: r.case_id,
    mode: r.mode,
    phase: r.phase,
    startedAt: r.started_at,
    endedAt: r.ended_at,
  };
}

export async function advancePhase(sessionId: string): Promise<{
  new_phase: SessionRecord["phase"];
  time_limit_s: number | null;
}> {
  return request(`/sessions/${sessionId}/advance`, { method: "POST" });
}

// ─── Transcripts ─────────────────────────────────────────────────────────

function normalizeTranscript(t: {
  id: string;
  session_id: string;
  speaker: string;
  text: string;
  audio_path: string | null;
  started_ms: number;
  ended_ms: number;
  created_at: string;
}): Transcript {
  return {
    id: t.id,
    sessionId: t.session_id,
    speaker: t.speaker as Transcript["speaker"],
    text: t.text,
    audioPath: t.audio_path,
    startedMs: t.started_ms,
    endedMs: t.ended_ms,
    createdAt: t.created_at,
  };
}

export async function fetchTranscripts(sessionId: string): Promise<Transcript[]> {
  try {
    const rows = await request<Parameters<typeof normalizeTranscript>[0][]>(
      `/sessions/${sessionId}/transcripts`,
    );
    return rows.map(normalizeTranscript);
  } catch {
    return MOCK_TRANSCRIPTS[sessionId] ?? [];
  }
}

export async function appendTranscript(
  sessionId: string,
  payload: {
    speaker: "student" | "patient";
    text: string;
    audio_path?: string | null;
    started_ms?: number;
    ended_ms?: number;
  },
): Promise<Transcript> {
  try {
    const row = await request<Parameters<typeof normalizeTranscript>[0]>(
      `/sessions/${sessionId}/transcripts`,
      { method: "POST", body: JSON.stringify(payload) },
    );
    return normalizeTranscript(row);
  } catch {
    return {
      id: `mock-${Date.now()}`,
      sessionId,
      speaker: payload.speaker,
      text: payload.text,
      audioPath: payload.audio_path ?? null,
      startedMs: payload.started_ms ?? 0,
      endedMs: payload.ended_ms ?? 0,
      createdAt: new Date().toISOString(),
    };
  }
}

// ─── Cases ───────────────────────────────────────────────────────────────

export interface CaseSummary {
  id: string;
  code: string;
  title: string;
  chief_complaint: string;
}

export async function fetchCases(): Promise<CaseSummary[]> {
  try {
    return await request<CaseSummary[]>("/cases");
  } catch {
    return [
      { id: "mock-1", code: "CASE-01", title: "急性胸痛 — 冠心症疑似", chief_complaint: "62 歲男性突發胸痛" },
      { id: "mock-2", code: "CASE-04", title: "右下腹痛 — 闌尾炎", chief_complaint: "28 歲女性右下腹痛" },
      { id: "mock-3", code: "CASE-22", title: "發燒解尿異常 — 腎盂腎炎", chief_complaint: "45 歲女性發燒合併解尿不適" },
    ];
  }
}

// ─── DUAT scoring + grading ──────────────────────────────────────────────

export async function scoreAllLqqopera(sessionId: string, caseContext = ""): Promise<unknown[]> {
  return request(`/sessions/${sessionId}/duat/score-all-lqqopera`, {
    method: "POST",
    body: JSON.stringify({ rubric_item_id: "lqqopera.location", case_context: caseContext }),
  });
}

export async function gradeItem(
  sessionId: string,
  scoreId: string,
  payload: { action: "accept" | "modify" | "reject"; final_score?: number; reason?: string },
): Promise<{ score_id: string; action: string; final_score: number | null; grader_id: string }> {
  return request(`/sessions/${sessionId}/scores/${scoreId}/grade`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ─── Rubric ──────────────────────────────────────────────────────────────

export async function fetchRubric(_rubricId: string): Promise<Rubric> {
  return MOCK_RUBRIC;
}

// ─── UI helper ───────────────────────────────────────────────────────────

export function deriveArbiterPillColor(d: ArbiterDecision | null): "emerald" | "amber" | "rose" | "slate" {
  if (!d) return "slate";
  if (d.action === "accept") return "emerald";
  if (d.action === "flag") return "amber";
  return "rose";
}
