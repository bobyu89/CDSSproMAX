"use client";

import type {
  HrvWindowResult,
  IngestResult,
  IngestSampleInput,
  PhysioSample,
  PhysioStateProxy,
  TimeDomainSummary,
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

// ─── Ingest ──────────────────────────────────────────────────────────────

export async function ingestSamples(
  sessionId: string,
  deviceId: string,
  samples: IngestSampleInput[],
): Promise<IngestResult> {
  try {
    const r = await request<{
      inserted: number;
      first_timestamp_ms: number | null;
      last_timestamp_ms: number | null;
    }>(`/physio/sessions/${sessionId}/samples`, {
      method: "POST",
      body: JSON.stringify({
        device_id: deviceId,
        samples: samples.map((s) => ({
          timestamp_ms: s.timestampMs,
          r_to_r_ms: s.rToRMs,
          heart_rate: s.heartRate ?? null,
          quality_flag: s.qualityFlag ?? "good",
        })),
      }),
    });
    return {
      inserted: r.inserted,
      firstTimestampMs: r.first_timestamp_ms,
      lastTimestampMs: r.last_timestamp_ms,
    };
  } catch {
    // Mock fallback so the UI keeps moving when API is offline.
    return { inserted: samples.length };
  }
}

// ─── HRV window ──────────────────────────────────────────────────────────

function normalizeSummary(
  s: {
    n_samples: number;
    duration_s: number;
    mean_hr: number;
    sdnn: number;
    rmssd: number;
    pnn50: number;
  } | null,
): TimeDomainSummary | null {
  if (!s) return null;
  return {
    nSamples: s.n_samples,
    durationS: s.duration_s,
    meanHr: s.mean_hr,
    sdnn: s.sdnn,
    rmssd: s.rmssd,
    pnn50: s.pnn50,
  };
}

export async function fetchHrvSummary(
  sessionId: string,
  windowSeconds = 60,
): Promise<HrvWindowResult> {
  try {
    const r = await request<{
      window_seconds: number;
      end_timestamp_ms: number;
      summary: Parameters<typeof normalizeSummary>[0];
      state_proxy: string;
    }>(`/physio/sessions/${sessionId}/hrv?window_seconds=${windowSeconds}`);
    return {
      windowSeconds: r.window_seconds,
      endTimestampMs: r.end_timestamp_ms,
      summary: normalizeSummary(r.summary),
      stateProxy: (r.state_proxy as PhysioStateProxy) ?? "no_data",
    };
  } catch {
    return {
      windowSeconds,
      endTimestampMs: Date.now(),
      summary: null,
      stateProxy: "no_data",
    };
  }
}

// ─── Timeseries ──────────────────────────────────────────────────────────

export async function fetchTimeseries(
  sessionId: string,
  limit = 500,
): Promise<PhysioSample[]> {
  try {
    const rows = await request<
      Array<{
        timestamp_ms: number;
        r_to_r_ms: number;
        heart_rate: number | null;
        quality_flag: string;
      }>
    >(`/physio/sessions/${sessionId}/timeseries?limit=${limit}`);
    return rows.map((r) => ({
      timestampMs: r.timestamp_ms,
      rToRMs: r.r_to_r_ms,
      heartRate: r.heart_rate,
      qualityFlag: (r.quality_flag as PhysioSample["qualityFlag"]) ?? "good",
    }));
  } catch {
    return [];
  }
}
