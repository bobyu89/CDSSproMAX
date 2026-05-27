// Personal Handout (個人講義) — Wave 2 frontend types.
// Backend endpoints expected at /sessions/{id}/handout etc.

export interface RadarPoint {
  axis: string;          // e.g. "Location"
  label: string;         // 繁中標籤，例如 "位置"
  score: number;         // 0-5
  fullMark?: number;     // default 5
}

export interface HrvTimePoint {
  tMin: number;          // minutes since session start
  hr: number;            // bpm
  rmssd: number;         // ms
  phase?: string | null; // e.g. "Inquiry" / "PE"
}

export type FlowZone = "flow" | "anxiety" | "boredom" | "apathy";

export interface FlowPoint {
  tMin: number;
  challenge: number;     // 0-5
  skill: number;         // 0-5
  zone: FlowZone;
}

export type MindMapKind = "root" | "key_concept" | "weakness" | "action" | "reference";

export interface MindMapNode {
  id: string;
  label: string;
  kind: MindMapKind;
  description?: string;
  parentId: string | null;
}

export interface DiscussionPrompt {
  id: string;
  question: string;
  why: string;            // 為何督導應追問的理由
}

export interface StudyNoteSection {
  id: string;
  heading: string;
  body: string;           // Markdown-light plain text
  citations: string[];    // ["Smith 2024", "UpToDate 2025"]
}

export interface SpacedRepetitionItem {
  id: string;
  dimension: string;      // weak axis label
  reviewDates: string[];  // ISO yyyy-mm-dd, length 4
  rationale: string;
}

export interface SelfAssessmentResponse {
  likert: {
    confidence: number;       // 1-5
    clarity: number;
    empathy: number;
    safety: number;
    growth: number;
  };
  textGoodWhat: string;
  textGoodWhy: string;
  textNextStep: string;
}

export interface ConfidenceCalibrationResponse {
  predictedScore: number | null;  // 0-5 self-prediction before reveal
  actualScore: number;            // 0-5 averaged final
  gap: number | null;             // actual - predicted
}

export interface HandoutResponse {
  sessionId: string;
  caseTitle: string;
  caseCode: string;
  mode: "practice" | "exam";
  completedAt: string;            // ISO
  totalScore: number;             // 0-5 averaged
  radar: RadarPoint[];
  hrv: HrvTimePoint[];
  flow: FlowPoint[];
  mindmap: MindMapNode[];
  studyNotes: StudyNoteSection[];
  discussion: DiscussionPrompt[];
  spacedRepetition: SpacedRepetitionItem[];
  selfAssessment: SelfAssessmentResponse | null;
  confidence: ConfidenceCalibrationResponse;
  phaseBoundaries: { tMin: number; label: string }[];
}
