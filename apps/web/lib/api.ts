// Thin API client for the TICDSS backend.
// Falls back to mock data when the backend is unreachable or returns non-2xx.
import type {
  DuatScore,
  GraderAction,
  Rubric,
  SessionRecord,
  Transcript,
} from "@ticdss/shared-types";
import {
  MOCK_DUAT_SCORES,
  MOCK_RUBRIC,
  MOCK_SESSIONS,
  MOCK_TRANSCRIPTS,
} from "./mock";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

async function safeFetch<T>(
  path: string,
  init: RequestInit | undefined,
  fallback: T,
): Promise<T> {
  try {
    const res = await fetch(`${API_URL}${path}`, {
      cache: "no-store",
      ...init,
    });
    if (!res.ok) return fallback;
    return (await res.json()) as T;
  } catch {
    return fallback;
  }
}

export async function fetchSessions(): Promise<SessionRecord[]> {
  return safeFetch<SessionRecord[]>("/sessions", undefined, MOCK_SESSIONS);
}

export interface SessionDetail {
  session: SessionRecord;
  scores: DuatScore[];
}

export async function fetchSessionDetail(
  id: string,
): Promise<SessionDetail | null> {
  const fallbackSession =
    MOCK_SESSIONS.find((s) => s.id === id) ?? MOCK_SESSIONS[0];
  const fallback: SessionDetail = {
    session: fallbackSession,
    scores: MOCK_DUAT_SCORES[id] ?? MOCK_DUAT_SCORES["sess-001"] ?? [],
  };
  return safeFetch<SessionDetail>(`/sessions/${id}`, undefined, fallback);
}

export interface GradeItemPayload {
  action: GraderAction;
  finalScore: number | null;
  reason: string | null;
}

export async function gradeItem(
  sessionId: string,
  scoreId: string,
  action: GraderAction,
  finalScore: number | null,
  reason: string | null,
): Promise<{ ok: boolean }> {
  try {
    const res = await fetch(
      `${API_URL}/sessions/${sessionId}/grading`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scoreId, action, finalScore, reason }),
        cache: "no-store",
      },
    );
    return { ok: res.ok };
  } catch {
    return { ok: false };
  }
}

export async function fetchRubric(_rubricId: string): Promise<Rubric> {
  return safeFetch<Rubric>(
    `/rubrics/${_rubricId}`,
    undefined,
    MOCK_RUBRIC,
  );
}

// --- Transcripts ----------------------------------------------------------
// Backend `TranscriptOut` uses snake_case; shared `Transcript` is camelCase.
// Normalize at the boundary so UI components never see snake_case.

interface RawTranscript {
  id: string;
  session_id: string;
  speaker: "student" | "patient";
  text: string;
  audio_path: string | null;
  started_ms: number;
  ended_ms: number;
  created_at: string;
}

function normalizeTranscript(raw: RawTranscript): Transcript {
  return {
    id: raw.id,
    sessionId: raw.session_id,
    speaker: raw.speaker,
    text: raw.text,
    audioPath: raw.audio_path,
    startedMs: raw.started_ms,
    endedMs: raw.ended_ms,
    createdAt: raw.created_at,
  };
}

export async function fetchTranscripts(
  sessionId: string,
): Promise<Transcript[]> {
  const fallback = MOCK_TRANSCRIPTS[sessionId] ?? [];
  try {
    const res = await fetch(
      `${API_URL}/sessions/${sessionId}/transcripts`,
      { cache: "no-store" },
    );
    if (!res.ok) return fallback;
    const raw = (await res.json()) as RawTranscript[];
    return raw.map(normalizeTranscript);
  } catch {
    return fallback;
  }
}

export interface AppendTranscriptPayload {
  speaker: "student" | "patient";
  text: string;
  audio_path?: string | null;
  started_ms?: number;
  ended_ms?: number;
}

export async function appendTranscript(
  sessionId: string,
  payload: AppendTranscriptPayload,
): Promise<Transcript> {
  // Optimistic local-only transcript used when backend is unreachable.
  const localFallback: Transcript = {
    id: `local-${Date.now()}`,
    sessionId,
    speaker: payload.speaker,
    text: payload.text,
    audioPath: payload.audio_path ?? null,
    startedMs: payload.started_ms ?? 0,
    endedMs: payload.ended_ms ?? 0,
    createdAt: new Date().toISOString(),
  };

  try {
    const res = await fetch(
      `${API_URL}/sessions/${sessionId}/transcripts`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        cache: "no-store",
      },
    );
    if (!res.ok) return localFallback;
    const raw = (await res.json()) as RawTranscript;
    return normalizeTranscript(raw);
  } catch {
    return localFallback;
  }
}
