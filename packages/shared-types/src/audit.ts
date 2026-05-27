// Mirrors apps/api/src/audit/schema.py.

export type AuditEventType =
  | "session.started"
  | "transcript.appended"
  | "duat.e_extracted"
  | "duat.s_scored"
  | "duat.a_reviewed"
  | "duat.arbiter_decided"
  | "duat.score_computed"
  | "grader.action"
  | "mdrift.alert";

export interface AuditPayload {
  eventId: string;
  sessionId: string;
  eventType: AuditEventType;
  timestamp: string;
  payload: Record<string, unknown>;
  promptHash: string | null;
  modelVersion: string | null;
  rubricItemId: string | null;
}
