// Mirrors apps/api/src/vision/anatomy_map.py + routers/vision.py

export type AnatomyRegion =
  | "pmi"
  | "aortic_area"
  | "pulmonic_area"
  | "erbs_point"
  | "tricuspid_area"
  | "mitral_area"
  | "jvp"
  | "carotid_right"
  | "carotid_left"
  | "right_upper_lung"
  | "left_upper_lung"
  | "right_lower_lung"
  | "left_lower_lung"
  | "abdomen_ruq"
  | "abdomen_luq"
  | "abdomen_rlq"
  | "abdomen_llq";

export interface AnatomyMarker {
  arucoId: number;
  region: AnatomyRegion;
  labelZh: string;
  printHint: string;
}

export interface MarkerDetection {
  arucoId: number;
  region: AnatomyRegion | null;
  centerX: number;
  centerY: number;
  corners: [number, number][];
}

export interface FrameDetectResult {
  detections: MarkerDetection[];
  frameW: number;
  frameH: number;
  backend: "opencv" | "stub";
}

export interface TrackSampleResult {
  touchedRegions: AnatomyRegion[];
  lastSeen: Record<number, number>;
}

export interface VAgentResult {
  rubricItemId: string;
  actionCorrect: boolean;
  techniqueScore: number; // 0-1
  durationAdequate: boolean;
  evidenceFrames: number[];
  notes: string;
  modelVersion: string;
}
