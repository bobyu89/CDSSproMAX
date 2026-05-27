"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { AlertCircle, Loader2, X } from "lucide-react";
import { toast } from "sonner";

import {
  createSession,
  fetchCases,
  fetchSessionDetail,
  type CaseSummary,
} from "@/lib/api";
import { useCdssStore, type CdssStep } from "@/lib/cdssStore";
import { useAuthStore } from "@/lib/authStore";

import { Timer } from "@/components/osce/Timer";
import { StationIndicator } from "@/components/osce/StationIndicator";
import { PreExamCard } from "@/components/osce/PreExamCard";
import {
  OsceSummary,
  type StationResult,
} from "@/components/osce/OsceSummary";
// Reuse the Practice mode step components — the OSCE flow only differs in
// timing/feedback semantics, not in the step UIs themselves.
import { StepSystem } from "@/components/practice/StepSystem";
import { StepInterview } from "@/components/practice/StepInterview";
import { StepPE } from "@/components/practice/StepPE";
import { StepDiagnosis } from "@/components/practice/StepDiagnosis";

// ── Constants ────────────────────────────────────────────────────────────────

const STEP_TIMES: Partial<Record<CdssStep, number>> = {
  interview: 360,
  pe: 360,
  diagnosis: 120,
};
const TIMED_STEPS = new Set<CdssStep>(["interview", "pe", "diagnosis"]);

const STATION_COUNT = 3;

// ── Component ────────────────────────────────────────────────────────────────

export default function OscePage() {
  const router = useRouter();
  const store = useCdssStore();
  const participantId = useAuthStore((s) => s.participantId);

  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [loadingCases, setLoadingCases] = useState(true);
  const [phase, setPhase] = useState<"pre" | "active" | "done">("pre");

  const [stationIdx, setStationIdx] = useState(0);
  const [stationResults, setStationResults] = useState<StationResult[]>([]);
  const [abandonOpen, setAbandonOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [startingStation, setStartingStation] = useState(false);

  const examStartRef = useRef<number | null>(null);
  const examEndRef = useRef<number | null>(null);

  const storeRef = useRef(store);
  storeRef.current = store;

  // Load cases (pick first N as stations)
  useEffect(() => {
    let alive = true;
    fetchCases()
      .then((all) => {
        if (!alive) return;
        setCases(all.slice(0, STATION_COUNT));
      })
      .catch(() => alive && setCases([]))
      .finally(() => alive && setLoadingCases(false));
    return () => {
      alive = false;
    };
  }, []);

  const currentCase = cases[stationIdx];

  // ── Station lifecycle ──────────────────────────────────────────────────────

  const startStation = useCallback(
    async (c: CaseSummary) => {
      setError(null);
      setStartingStation(true);
      const s = storeRef.current;
      s.resetSteps();
      s.setMode("osce");
      s.setCaseId(c.id);
      if (participantId) s.setParticipantId(participantId);
      try {
        const session = await createSession(c.id, "exam");
        s.startSession(session.id, null, null);
        s.setStep("system");
      } catch (e) {
        const msg = e instanceof Error ? e.message : "無法啟動考試站別";
        setError(msg);
      } finally {
        setStartingStation(false);
      }
    },
    [participantId],
  );

  const handleStartExam = useCallback(() => {
    if (cases.length === 0) {
      toast.error("尚無可用案例");
      return;
    }
    examStartRef.current = Date.now();
    examEndRef.current = null;
    setStationIdx(0);
    setStationResults([]);
    setPhase("active");
    startStation(cases[0]);
  }, [cases, startStation]);

  const finishCurrentStation = useCallback(async () => {
    const s = storeRef.current;
    s.setTimerActive(false);
    const sid = s.sessionId;
    const title = cases[stationIdx]?.title ?? `第 ${stationIdx + 1} 站`;
    const caseId = cases[stationIdx]?.id ?? null;

    let summary: StationResult["summary"] = null;
    if (sid) {
      summary = await fetchSessionDetail(sid).catch(() => null);
    }

    setStationResults((prev) => [
      ...prev,
      { stationIdx, title, caseId, summary },
    ]);

    const next = stationIdx + 1;
    if (next < cases.length) {
      setStationIdx(next);
      startStation(cases[next]);
    } else {
      examEndRef.current = Date.now();
      setPhase("done");
    }
  }, [cases, stationIdx, startStation]);

  // Auto-finish when step reaches "summary" (e.g. user clicked through diagnosis)
  useEffect(() => {
    if (phase === "active" && store.currentStep === "summary") {
      finishCurrentStation();
    }
  }, [phase, store.currentStep, finishCurrentStation]);

  // ── Timer hookup ───────────────────────────────────────────────────────────

  const timerTotal = useMemo(() => {
    return STEP_TIMES[store.currentStep] ?? 0;
  }, [store.currentStep]);

  const timerActive =
    phase === "active" && TIMED_STEPS.has(store.currentStep);

  const handleTimeUp = useCallback(() => {
    const cur = storeRef.current.currentStep;
    if (cur === "interview") {
      toast("問診時間到，自動進入身體評估");
      storeRef.current.setStep("pe");
    } else if (cur === "pe") {
      toast("身體評估時間到，自動進入診斷");
      storeRef.current.setStep("diagnosis");
    } else if (cur === "diagnosis") {
      toast("診斷時間到，提交本站答案");
      finishCurrentStation();
    }
  }, [finishCurrentStation]);

  // ── Abandon ────────────────────────────────────────────────────────────────

  const handleAbandonConfirm = useCallback(() => {
    setAbandonOpen(false);
    storeRef.current.reset();
    setPhase("pre");
    setStationIdx(0);
    setStationResults([]);
    examStartRef.current = null;
    examEndRef.current = null;
    router.push("/home");
  }, [router]);

  const handleRestart = useCallback(() => {
    storeRef.current.reset();
    setPhase("pre");
    setStationIdx(0);
    setStationResults([]);
    examStartRef.current = null;
    examEndRef.current = null;
  }, []);

  // ── Render ─────────────────────────────────────────────────────────────────

  if (phase === "done") {
    const totalDuration =
      examStartRef.current && examEndRef.current
        ? Math.round((examEndRef.current - examStartRef.current) / 1000)
        : null;
    return (
      <OsceSummary
        stations={stationResults}
        totalDurationS={totalDuration}
        onRestart={handleRestart}
      />
    );
  }

  if (phase === "pre") {
    return (
      <div className="p-8 lg:p-12">
        {loadingCases ? (
          <div className="flex items-center justify-center py-32">
            <Loader2 className="animate-spin text-brand-500" size={28} />
          </div>
        ) : (
          <PreExamCard
            totalStations={Math.min(STATION_COUNT, cases.length || STATION_COUNT)}
            onStart={handleStartExam}
            disabled={cases.length === 0}
          />
        )}
      </div>
    );
  }

  // ── Active phase ───────────────────────────────────────────────────────────

  return (
    <div className="p-6 lg:p-10 max-w-5xl mx-auto">
      {/* Top bar: station progress + abandon */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
        <div>
          <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-1">
            OSCE 進行中
          </p>
          <StationIndicator total={cases.length} currentIdx={stationIdx} />
        </div>
        <button
          type="button"
          onClick={() => setAbandonOpen(true)}
          className="self-start sm:self-auto text-xs font-bold text-ink-muted hover:text-danger transition-colors inline-flex items-center gap-1.5"
        >
          <X size={14} /> 中止考試
        </button>
      </div>

      {/* Case header */}
      <div className="mb-6 rounded-xl bg-bg-surface border border-faint px-5 py-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-1">
              第 {stationIdx + 1} / {cases.length} 站
            </p>
            <h1 className="text-lg lg:text-xl font-bold text-ink">
              {currentCase?.title ?? "載入中..."}
            </h1>
            {currentCase?.chief_complaint && (
              <p className="text-xs text-ink-muted mt-1">
                主訴：{currentCase.chief_complaint}
              </p>
            )}
          </div>
          {timerActive && (
            <div className="w-44 shrink-0">
              <Timer
                totalSeconds={timerTotal}
                onTimeUp={handleTimeUp}
                active={timerActive}
              />
            </div>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 rounded-lg border border-danger/30 bg-danger/5 px-4 py-3 flex items-start gap-2 text-sm text-danger">
          <AlertCircle size={16} className="mt-0.5 shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {/* Step content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={store.currentStep}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.18 }}
        >
          {startingStation ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="animate-spin text-brand-500" size={24} />
            </div>
          ) : (
            <>
              {store.currentStep === "system" && <StepSystem />}
              {store.currentStep === "interview" && <StepInterview />}
              {store.currentStep === "pe" && <StepPE />}
              {store.currentStep === "diagnosis" && <StepDiagnosis />}
            </>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Abandon dialog */}
      <AnimatePresence>
        {abandonOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 backdrop-blur-sm p-4"
            onClick={() => setAbandonOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.96, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.96, opacity: 0 }}
              transition={{ duration: 0.18 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl border border-faint shadow-xl max-w-md w-full p-6"
            >
              <h3 className="text-lg font-bold text-ink mb-2">
                確定要中止考試？
              </h3>
              <p className="text-sm text-ink-muted leading-relaxed mb-6">
                已作答的內容將被記錄，但本次考試不會列入正式成績。
              </p>
              <div className="flex flex-col-reverse sm:flex-row gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setAbandonOpen(false)}
                  className="px-5 py-2.5 rounded-lg text-sm font-semibold text-ink-soft bg-bg-surface hover:bg-bg-muted transition-colors"
                >
                  繼續考試
                </button>
                <button
                  type="button"
                  onClick={handleAbandonConfirm}
                  className="px-5 py-2.5 rounded-lg text-sm font-bold text-white bg-danger hover:opacity-90 active:scale-[0.98] transition-all"
                >
                  中止考試
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
