// Mirrors apps/api/src/db/models.py PhysioSample + physio/hrv.py TimeDomainSummary.
// Wave 3 — HRV skeleton.

export type PhysioQualityFlag = "good" | "noisy" | "gap";

export interface PhysioSample {
  timestampMs: number;
  rToRMs: number;
  heartRate?: number | null;
  qualityFlag: PhysioQualityFlag;
}

export interface TimeDomainSummary {
  nSamples: number;
  durationS: number;
  meanHr: number;
  sdnn: number;
  rmssd: number;
  pnn50: number;
}

// Single-channel coarse state proxy. 'no_data' is surfaced when the
// backend window contained zero usable samples.
export type PhysioStateProxy =
  | "flow"
  | "anxious"
  | "low_engagement"
  | "ambiguous"
  | "no_data";

export interface HrvWindowResult {
  windowSeconds: number;
  endTimestampMs: number;
  summary: TimeDomainSummary | null;
  stateProxy: PhysioStateProxy;
}

export interface IngestSampleInput {
  timestampMs: number;
  rToRMs: number;
  heartRate?: number | null;
  qualityFlag?: PhysioQualityFlag;
}

export interface IngestResult {
  inserted: number;
  firstTimestampMs?: number | null;
  lastTimestampMs?: number | null;
}
