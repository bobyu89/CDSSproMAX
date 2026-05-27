// Mirrors apps/api/src/db/models.py + agents/o_agent.py Phase enum.

export type SessionMode = "practice" | "exam";

export type Phase =
  | "scenario"
  | "inquiry"
  | "transition"
  | "examination"
  | "diagnosis"
  | "review";

export interface SessionRecord {
  id: string;
  participantId: string;
  caseId: string;
  mode: SessionMode;
  phase: Phase;
  startedAt: string; // ISO 8601
  endedAt: string | null;
}

export interface Transcript {
  id: string;
  sessionId: string;
  speaker: "student" | "patient";
  text: string;
  audioPath: string | null;
  startedMs: number;
  endedMs: number;
  createdAt: string;
}
