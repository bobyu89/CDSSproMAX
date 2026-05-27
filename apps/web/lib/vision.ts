"use client";

import type {
  AnatomyMarker,
  FrameDetectResult,
  MarkerDetection,
  TrackSampleResult,
  VAgentResult,
} from "@ticdss/shared-types";
import { API_URL, ApiError } from "./api";
import { useAuthStore } from "./authStore";

function authHeader(): Record<string, string> {
  const token = useAuthStore.getState().token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
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

// ─── Anatomy map ─────────────────────────────────────────────────────────

export async function fetchAnatomyMap(): Promise<AnatomyMarker[]> {
  try {
    const rows = await request<
      Array<{ aruco_id: number; region: string; label_zh: string; print_hint: string }>
    >("/vision/anatomy-map");
    return rows.map((r) => ({
      arucoId: r.aruco_id,
      region: r.region as AnatomyMarker["region"],
      labelZh: r.label_zh,
      printHint: r.print_hint,
    }));
  } catch {
    return MOCK_ANATOMY_MAP;
  }
}

// ─── Marker detection ────────────────────────────────────────────────────

function normalizeDetection(d: {
  aruco_id: number;
  region: string | null;
  center_x: number;
  center_y: number;
  corners: number[][];
}): MarkerDetection {
  return {
    arucoId: d.aruco_id,
    region: (d.region as MarkerDetection["region"]) ?? null,
    centerX: d.center_x,
    centerY: d.center_y,
    corners: d.corners.map(([x, y]) => [x, y] as [number, number]),
  };
}

export async function detectMarkers(frameB64: string): Promise<FrameDetectResult> {
  try {
    const r = await request<{
      detections: Parameters<typeof normalizeDetection>[0][];
      frame_w: number;
      frame_h: number;
      backend: string;
    }>("/vision/markers/detect", {
      method: "POST",
      body: JSON.stringify({ frame_b64: frameB64 }),
    });
    return {
      detections: r.detections.map(normalizeDetection),
      frameW: r.frame_w,
      frameH: r.frame_h,
      backend: (r.backend as FrameDetectResult["backend"]) ?? "stub",
    };
  } catch {
    return { detections: [], frameW: 0, frameH: 0, backend: "stub" };
  }
}

// ─── Tracker ────────────────────────────────────────────────────────────

export async function postTrackSample(
  sessionId: string,
  visibleMarkerIds: number[],
  timestamp?: number,
): Promise<TrackSampleResult> {
  try {
    const r = await request<{
      touched_regions: string[];
      last_seen: Record<number, number>;
    }>(`/vision/sessions/${sessionId}/track`, {
      method: "POST",
      body: JSON.stringify({
        visible_marker_ids: visibleMarkerIds,
        timestamp,
      }),
    });
    return {
      touchedRegions: r.touched_regions as TrackSampleResult["touchedRegions"],
      lastSeen: r.last_seen,
    };
  } catch {
    return { touchedRegions: [], lastSeen: {} };
  }
}

export async function resetTracker(sessionId: string): Promise<void> {
  try {
    await request(`/vision/sessions/${sessionId}/track`, { method: "DELETE" });
  } catch {
    // ignore — non-critical
  }
}

// ─── V-Agent ────────────────────────────────────────────────────────────

export async function runVAgent(
  sessionId: string,
  payload: {
    rubricItemId: string;
    targetAction: string;
    targetRegion: string;
    studentIntent?: string;
    detectedRegions?: string[];
    keyframesB64?: string[];
    durationSeconds?: number;
  },
): Promise<VAgentResult> {
  try {
    const r = await request<{
      rubric_item_id: string;
      action_correct: boolean;
      technique_score: number;
      duration_adequate: boolean;
      evidence_frames: number[];
      notes: string;
      model_version: string;
    }>(`/vision/sessions/${sessionId}/v-agent`, {
      method: "POST",
      body: JSON.stringify({
        rubric_item_id: payload.rubricItemId,
        target_action: payload.targetAction,
        target_region: payload.targetRegion,
        student_intent: payload.studentIntent ?? "",
        detected_regions: payload.detectedRegions ?? [],
        keyframes_b64: payload.keyframesB64 ?? [],
        duration_seconds: payload.durationSeconds ?? 0,
      }),
    });
    return {
      rubricItemId: r.rubric_item_id,
      actionCorrect: r.action_correct,
      techniqueScore: r.technique_score,
      durationAdequate: r.duration_adequate,
      evidenceFrames: r.evidence_frames,
      notes: r.notes,
      modelVersion: r.model_version,
    };
  } catch {
    // Graceful fallback — same pattern as the rest of api.ts. Lets the UI
    // surface a "V-Agent 未連線" hint instead of crashing the flow.
    return {
      rubricItemId: payload.rubricItemId,
      actionCorrect: (payload.detectedRegions ?? []).includes(payload.targetRegion),
      techniqueScore: 0,
      durationAdequate: (payload.durationSeconds ?? 0) >= 3,
      evidenceFrames: [],
      notes: "[fallback] V-Agent 服務未連線，無語意評核",
      modelVersion: "fallback",
    };
  }
}

// ─── Mock fallback ───────────────────────────────────────────────────────

const MOCK_ANATOMY_MAP: AnatomyMarker[] = [
  { arucoId: 1, region: "pmi", labelZh: "心尖搏動點", printHint: "左鎖骨中線 × 第五肋間" },
  { arucoId: 2, region: "aortic_area", labelZh: "主動脈瓣區", printHint: "右胸骨第二肋間" },
  { arucoId: 3, region: "pulmonic_area", labelZh: "肺動脈瓣區", printHint: "左胸骨第二肋間" },
  { arucoId: 4, region: "erbs_point", labelZh: "Erb's point", printHint: "左胸骨第三肋間" },
  { arucoId: 5, region: "tricuspid_area", labelZh: "三尖瓣區", printHint: "左胸骨下緣" },
  { arucoId: 6, region: "jvp", labelZh: "頸靜脈壓", printHint: "右側胸鎖乳突肌中段" },
  { arucoId: 9, region: "right_upper_lung", labelZh: "右上肺葉", printHint: "右鎖骨下方第二肋間" },
  { arucoId: 10, region: "left_upper_lung", labelZh: "左上肺葉", printHint: "左鎖骨下方第二肋間" },
  { arucoId: 11, region: "right_lower_lung", labelZh: "右下肺葉", printHint: "右側第八肋間腋中線" },
  { arucoId: 12, region: "left_lower_lung", labelZh: "左下肺葉", printHint: "左側第八肋間腋中線" },
  { arucoId: 13, region: "abdomen_ruq", labelZh: "腹部右上象限", printHint: "肋緣下右鎖骨中線" },
  { arucoId: 14, region: "abdomen_luq", labelZh: "腹部左上象限", printHint: "肋緣下左鎖骨中線" },
  { arucoId: 15, region: "abdomen_rlq", labelZh: "腹部右下象限", printHint: "McBurney point" },
  { arucoId: 16, region: "abdomen_llq", labelZh: "腹部左下象限", printHint: "左下腹" },
];
