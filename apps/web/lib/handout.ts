"use client";

import type {
  ConfidenceCalibrationResponse,
  HandoutResponse,
  SelfAssessmentResponse,
} from "@ticdss/shared-types";
import { API_URL } from "./api";
import { useAuthStore } from "./authStore";
import { MOCK_HANDOUT } from "./mock";

function authHeader(): Record<string, string> {
  const token = useAuthStore.getState().token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const resp = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
      ...(init.headers || {}),
    },
    cache: "no-store",
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return (await resp.json()) as T;
}

export async function fetchHandout(sessionId: string): Promise<HandoutResponse> {
  try {
    return await req<HandoutResponse>(`/sessions/${sessionId}/handout`);
  } catch {
    return { ...MOCK_HANDOUT, sessionId };
  }
}

export async function submitSelfAssessment(
  sessionId: string,
  payload: SelfAssessmentResponse,
): Promise<SelfAssessmentResponse> {
  try {
    return await req<SelfAssessmentResponse>(
      `/sessions/${sessionId}/self-assessment`,
      { method: "POST", body: JSON.stringify(payload) },
    );
  } catch {
    // Mock success — store locally
    if (typeof window !== "undefined") {
      window.localStorage.setItem(
        `ticdss:self-assessment:${sessionId}`,
        JSON.stringify(payload),
      );
    }
    return payload;
  }
}

export async function submitConfidencePrediction(
  sessionId: string,
  predictedScore: number,
): Promise<ConfidenceCalibrationResponse> {
  try {
    return await req<ConfidenceCalibrationResponse>(
      `/sessions/${sessionId}/confidence-prediction`,
      { method: "POST", body: JSON.stringify({ predicted_score: predictedScore }) },
    );
  } catch {
    const actual = MOCK_HANDOUT.totalScore;
    return {
      predictedScore,
      actualScore: actual,
      gap: +(actual - predictedScore).toFixed(2),
    };
  }
}

export async function regenerateHandout(sessionId: string): Promise<void> {
  try {
    await req<unknown>(`/sessions/${sessionId}/handout/regenerate`, {
      method: "POST",
    });
  } catch {
    // ignore — mock no-op
  }
}
