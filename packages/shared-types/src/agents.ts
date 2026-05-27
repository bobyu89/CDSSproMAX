// Mirrors apps/api/src/agents/*.py output shapes.

export interface EvidenceSegment {
  transcriptId: string | null;
  startMs: number;
  endMs: number;
  speaker: "student" | "patient";
  text: string;
  relevanceScore: number;
}

export interface RagHit {
  chunkId: string;
  source: string;
  cosineSimilarity: number;
  rerankScore: number;
}

export interface EvidenceBundle {
  rubricItemId: string;
  evidenceSegments: EvidenceSegment[];
  ragHits: RagHit[];
  confidence: number;
  extractionNotes: string;
}

export interface SAgentOutput {
  rubricItemId: string;
  score: number; // 0-5
  cotReasoning: string;
  modelVersion: string;
}

export interface AAgentOutput {
  rubricItemId: string;
  advocateReport: string;
  advocateScore: number; // 0-1
  modelVersion: string;
}

export type ArbiterAction = "accept" | "flag" | "force_human";
export type ArbiterConfidence = "high" | "medium" | "low";

export interface ArbiterDecision {
  action: ArbiterAction;
  confidence: ArbiterConfidence;
  thresholdsVersion: string;
  flagReason: string | null;
}

export type GraderAction = "accept" | "modify" | "reject";

export interface DuatScore {
  id: string;
  sessionId: string;
  rubricItemId: string;
  eConfidence: number | null;
  sScore: number | null;
  aAdvocateScore: number | null;
  arbiterDecision: ArbiterAction | null;
  arbiterConfidence: ArbiterConfidence | null;
  finalScore: number | null;
  graderAction: GraderAction | null;
  graderReason: string | null;
}
