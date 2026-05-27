"use client";

import { create } from "zustand";

export type CdssMode = "practice" | "osce";
export type CdssStep =
  | "symptom"
  | "system"
  | "interview"
  | "pe"
  | "diagnosis"
  | "summary";

export interface InterviewTurn {
  speaker: "student" | "patient";
  text: string;
  createdAt: string;
}

interface CdssState {
  mode: CdssMode;
  caseId: string | null;
  sessionId: string | null;
  participantId: string | null;
  scenario: string | null;
  caseImageUrl: string | null;

  currentStep: CdssStep;
  systemOptions: string[];
  selectedSystem: string | null;
  interviewTurns: InterviewTurn[];
  peSelections: string[];
  diagnosis: string | null;

  timerActive: boolean;
  totalTime: number; // seconds
  timeRemaining: number;

  error: string | null;

  // setters
  setMode: (m: CdssMode) => void;
  setCaseId: (id: string | null) => void;
  setParticipantId: (id: string) => void;
  setStep: (s: CdssStep) => void;
  setScenario: (s: string | null) => void;
  setSystemOptions: (opts: string[]) => void;
  setSelectedSystem: (s: string | null) => void;
  appendTurn: (t: InterviewTurn) => void;
  setPeSelections: (ps: string[]) => void;
  setDiagnosis: (d: string | null) => void;
  setError: (e: string | null) => void;

  setTimerActive: (a: boolean) => void;
  setTotalTime: (t: number) => void;
  setTimeRemaining: (t: number) => void;
  tickTimer: () => void;

  startSession: (sessionId: string, scenario: string | null, imageUrl: string | null) => void;
  resetSteps: () => void;
  reset: () => void;
}

const INITIAL_STEPS = {
  currentStep: "symptom" as CdssStep,
  systemOptions: [] as string[],
  selectedSystem: null as string | null,
  interviewTurns: [] as InterviewTurn[],
  peSelections: [] as string[],
  diagnosis: null as string | null,
};

const INITIAL_TIMER = {
  timerActive: false,
  totalTime: 0,
  timeRemaining: 0,
};

export const useCdssStore = create<CdssState>((set) => ({
  mode: "practice",
  caseId: null,
  sessionId: null,
  participantId: null,
  scenario: null,
  caseImageUrl: null,
  ...INITIAL_STEPS,
  ...INITIAL_TIMER,
  error: null,

  setMode: (m) => set({ mode: m }),
  setCaseId: (id) => set({ caseId: id }),
  setParticipantId: (id) => set({ participantId: id }),
  setStep: (s) => set({ currentStep: s }),
  setScenario: (s) => set({ scenario: s }),
  setSystemOptions: (opts) => set({ systemOptions: opts }),
  setSelectedSystem: (s) => set({ selectedSystem: s }),
  appendTurn: (t) => set((state) => ({ interviewTurns: [...state.interviewTurns, t] })),
  setPeSelections: (ps) => set({ peSelections: ps }),
  setDiagnosis: (d) => set({ diagnosis: d }),
  setError: (e) => set({ error: e }),

  setTimerActive: (a) => set({ timerActive: a }),
  setTotalTime: (t) => set({ totalTime: t }),
  setTimeRemaining: (t) => set({ timeRemaining: t }),
  tickTimer: () =>
    set((s) => ({
      timeRemaining: s.timeRemaining > 0 ? s.timeRemaining - 1 : 0,
    })),

  startSession: (sessionId, scenario, imageUrl) =>
    set({ sessionId, scenario, caseImageUrl: imageUrl, currentStep: "system" }),

  resetSteps: () => set({ ...INITIAL_STEPS, ...INITIAL_TIMER, error: null }),
  reset: () =>
    set({
      mode: "practice",
      caseId: null,
      sessionId: null,
      participantId: null,
      scenario: null,
      caseImageUrl: null,
      ...INITIAL_STEPS,
      ...INITIAL_TIMER,
      error: null,
    }),
}));
