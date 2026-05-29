"use client";

/**
 * Training-flow API client — 驅動後端 builder 熱插拔引擎。
 *
 * 對應 apps/api/src/routers/training.py:
 *   建 session → advance(逐 phase) → input → score → finalize。
 *
 * 前端 UI/UX 沿用既有設計;這層只負責把畫面動作轉成 /training 呼叫。
 */

import { API_URL, ApiError } from "./api";
import { useAuthStore } from "./authStore";

function authHeader(): Record<string, string> {
  const token = useAuthStore.getState().token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const resp = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...authHeader(), ...(init.headers || {}) },
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

// ─── Types ───────────────────────────────────────────────────────────────

export type TrainingMode = "practice" | "exam";

export interface CreateTrainingResult {
  training_id: string;
  phase: string;
  mode: TrainingMode;
  registered_stages: string[];
}

export interface StageScoreOut {
  stage: string;
  raw_score: number;
  sub_items: Record<string, unknown>;
  weak_points: string[];
}

export interface ScorePhaseResult {
  phase: string;
  stage_score: StageScoreOut;
  summary: unknown;
  realtime: {
    stage: string;
    score: number;
    deterministic: number;
    semantic: number;
    feedback: string;
  } | null;
}

export interface FinalizeResult {
  outputs: {
    narrative: { type: string; text: string };
    radar: { type: string; dimensions: Record<string, number> };
    weakness: { type: string; items: string[]; duat_analysis: string };
    keyfocus: { type: string; focus: string; rationale: string };
    stress: { type: string; curve: unknown[]; hrv: unknown[]; peak: unknown };
  };
  rag_cards: { type: string; cards: { permanent: string; training: string; topic: string }[]; message?: string };
  cornell_report: unknown;
  verification: {
    advocate_score: number;
    e_confidence: number;
    challenged_points: string[];
    arbiter_action: "accept" | "flag" | "force_human";
    arbiter_confidence: string;
    thresholds_version: string;
  };
  audit_events: unknown[];
  llm_cost: number;
}

// ─── Calls ───────────────────────────────────────────────────────────────

export async function listRegistry(): Promise<{ contract_version: string; registered_stages: string[] }> {
  return req("/training/registry");
}

export async function createTraining(payload: {
  mode: TrainingMode;
  scenario_id: string;
  standard_sequence?: string[];
  stress_monitoring?: boolean;
}): Promise<CreateTrainingResult> {
  return req("/training/sessions", { method: "POST", body: JSON.stringify(payload) });
}

export async function getTrainingState(tid: string): Promise<{
  phase: string;
  mode: TrainingMode;
  difficulty: number;
  anxiety: number;
  phase_scores: Record<string, number | null>;
  llm_cost: number;
}> {
  return req(`/training/sessions/${tid}/state`);
}

export async function advancePhase(tid: string): Promise<{
  phase: string;
  time_limit_s: number | null;
  enter: { hint?: string } | null;
  has_agent: boolean;
}> {
  return req(`/training/sessions/${tid}/advance`, { method: "POST" });
}

export async function submitPhaseInput(
  tid: string,
  payload: Record<string, unknown>,
): Promise<{ phase: string; response: Record<string, unknown> }> {
  return req(`/training/sessions/${tid}/input`, {
    method: "POST",
    body: JSON.stringify({ payload }),
  });
}

export async function scorePhase(tid: string): Promise<ScorePhaseResult> {
  return req(`/training/sessions/${tid}/score`, { method: "POST" });
}

export async function finalizeTraining(tid: string): Promise<FinalizeResult> {
  return req(`/training/sessions/${tid}/finalize`, { method: "POST" });
}
