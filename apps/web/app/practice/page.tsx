"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronLeft, HelpCircle, Home } from "lucide-react";
import { useCdssStore, type CdssStep } from "@/lib/cdssStore";
import { useAuthStore } from "@/lib/authStore";
import { StepIndicator, type StepDef } from "@/components/practice/StepIndicator";
import { StepSymptom } from "@/components/practice/StepSymptom";
import { StepSystem } from "@/components/practice/StepSystem";
import { StepInterview } from "@/components/practice/StepInterview";
import { StepPE } from "@/components/practice/StepPE";
import { StepDiagnosis } from "@/components/practice/StepDiagnosis";
import { StepSummary } from "@/components/practice/StepSummary";

const STEPS: StepDef[] = [
  { key: "symptom", label: "主訴" },
  { key: "system", label: "系統" },
  { key: "interview", label: "問診" },
  { key: "pe", label: "身體評估" },
  { key: "diagnosis", label: "鑑別診斷" },
  { key: "summary", label: "回饋" },
];

const PREV_STEP: Record<CdssStep, CdssStep | null> = {
  symptom: null,
  system: "symptom",
  interview: "system",
  pe: "interview",
  diagnosis: "pe",
  summary: "diagnosis",
};

const NEXT_STEP: Record<CdssStep, CdssStep | null> = {
  symptom: "system",
  system: "interview",
  interview: "pe",
  pe: "diagnosis",
  diagnosis: "summary",
  summary: null,
};

export default function PracticePage() {
  const router = useRouter();
  const mode = useCdssStore((s) => s.mode);
  const sessionId = useCdssStore((s) => s.sessionId);
  const currentStep = useCdssStore((s) => s.currentStep);
  const setMode = useCdssStore((s) => s.setMode);
  const setStep = useCdssStore((s) => s.setStep);
  const setParticipantId = useCdssStore((s) => s.setParticipantId);
  const reset = useCdssStore((s) => s.reset);
  const storeParticipant = useCdssStore((s) => s.participantId);

  const participantId = useAuthStore((s) => s.participantId);

  const selectedSystem = useCdssStore((s) => s.selectedSystem);
  const interviewTurns = useCdssStore((s) => s.interviewTurns);
  const peSelections = useCdssStore((s) => s.peSelections);
  const diagnosis = useCdssStore((s) => s.diagnosis);

  const [confirmLeave, setConfirmLeave] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);

  // Pragmatic step-complete check — used to gate Alt/Ctrl+→
  const isStepComplete = (step: CdssStep): boolean => {
    switch (step) {
      case "symptom":
        return !!sessionId;
      case "system":
        return !!selectedSystem;
      case "interview":
        return interviewTurns.length > 0;
      case "pe":
        return peSelections.length > 0;
      case "diagnosis":
        return !!diagnosis;
      default:
        return false;
    }
  };

  // Auto-init on mount.
  useEffect(() => {
    if (mode !== "practice") setMode("practice");
    if (participantId && !storeParticipant) setParticipantId(participantId);
    // Only force back to "symptom" if there is truly no session yet
    // *and* we aren't already mid-flow (defensive — store may persist later).
    if (!sessionId && currentStep !== "symptom") {
      setStep("symptom");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const isMidSession =
    !!sessionId && currentStep !== "symptom" && currentStep !== "summary";

  const handleBack = () => {
    const prev = PREV_STEP[currentStep];
    if (!prev) {
      // On the symptom step, just go home (no session yet).
      router.push("/home");
      return;
    }
    setStep(prev);
  };

  const handleHome = () => {
    if (isMidSession) {
      setConfirmLeave(true);
    } else {
      reset();
      router.push("/home");
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      // Skip when user is typing in inputs
      const tgt = e.target as HTMLElement | null;
      const tag = tgt?.tagName;
      const isEditable =
        tag === "INPUT" ||
        tag === "TEXTAREA" ||
        tag === "SELECT" ||
        tgt?.isContentEditable;

      if (e.key === "Escape") {
        if (showShortcuts) {
          setShowShortcuts(false);
          return;
        }
        if (isMidSession && !confirmLeave) {
          e.preventDefault();
          setConfirmLeave(true);
        }
        return;
      }

      const mod = e.altKey || e.ctrlKey;
      if (!mod) return;
      if (isEditable) return;

      if (e.key === "ArrowRight") {
        const next = NEXT_STEP[currentStep];
        if (next && isStepComplete(currentStep)) {
          e.preventDefault();
          setStep(next);
        }
      } else if (e.key === "ArrowLeft") {
        const prev = PREV_STEP[currentStep];
        if (prev) {
          e.preventDefault();
          setStep(prev);
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    currentStep,
    isMidSession,
    confirmLeave,
    showShortcuts,
    sessionId,
    selectedSystem,
    interviewTurns.length,
    peSelections.length,
    diagnosis,
  ]);

  const confirmLeaveAndGo = () => {
    setConfirmLeave(false);
    reset();
    router.push("/home");
  };

  const renderStep = () => {
    switch (currentStep) {
      case "symptom":
        return <StepSymptom key="symptom" />;
      case "system":
        return <StepSystem key="system" />;
      case "interview":
        return <StepInterview key="interview" />;
      case "pe":
        return <StepPE key="pe" />;
      case "diagnosis":
        return <StepDiagnosis key="diagnosis" />;
      case "summary":
        return <StepSummary key="summary" />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-bg">
      {/* Sticky header */}
      <header className="sticky top-14 z-30 bg-bg/95 backdrop-blur border-b border-brand-100">
        <div className="max-w-7xl mx-auto px-6 lg:px-10 py-3 flex items-center gap-4">
          <button
            type="button"
            onClick={handleBack}
            className="inline-flex items-center gap-1.5 text-xs font-bold text-ink-soft hover:text-brand-600 transition-colors px-2.5 py-1.5 rounded-md hover:bg-bg-surface"
          >
            <ChevronLeft size={14} />
            回到上一步
          </button>
          <div className="flex-1 min-w-0 overflow-x-auto">
            <StepIndicator steps={STEPS} current={currentStep} />
          </div>
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowShortcuts((v) => !v)}
              aria-label="鍵盤捷徑說明"
              aria-expanded={showShortcuts}
              className="inline-flex items-center justify-center text-xs font-bold text-ink-soft hover:text-brand-600 transition-colors p-1.5 rounded-md hover:bg-bg-surface"
            >
              <HelpCircle size={14} />
            </button>
            <AnimatePresence>
              {showShortcuts && (
                <motion.div
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  transition={{ duration: 0.15 }}
                  role="dialog"
                  aria-modal="false"
                  aria-label="鍵盤捷徑"
                  className="absolute right-0 top-full mt-2 w-64 z-40 rounded-lg bg-white border border-subtle shadow-lg p-3"
                >
                  <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-2">
                    鍵盤捷徑
                  </p>
                  <ul className="space-y-1.5 text-xs text-ink">
                    <li className="flex justify-between">
                      <span>下一步</span>
                      <kbd className="font-mono text-[10px] bg-bg-surface px-1.5 py-0.5 rounded">Alt / Ctrl + →</kbd>
                    </li>
                    <li className="flex justify-between">
                      <span>上一步</span>
                      <kbd className="font-mono text-[10px] bg-bg-surface px-1.5 py-0.5 rounded">Alt / Ctrl + ←</kbd>
                    </li>
                    <li className="flex justify-between">
                      <span>中止練習</span>
                      <kbd className="font-mono text-[10px] bg-bg-surface px-1.5 py-0.5 rounded">Esc</kbd>
                    </li>
                  </ul>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          <button
            type="button"
            onClick={handleHome}
            className="inline-flex items-center gap-1.5 text-xs font-bold text-ink-soft hover:text-brand-600 transition-colors px-2.5 py-1.5 rounded-md hover:bg-bg-surface"
          >
            <Home size={14} />
            回首頁
          </button>
        </div>
      </header>

      {/* Body */}
      <div className="px-6 lg:px-10 py-10">
        <AnimatePresence mode="wait" initial={false}>
          {renderStep()}
        </AnimatePresence>
      </div>

      {/* Abandon dialog */}
      <AnimatePresence>
        {confirmLeave && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
          >
            <div
              className="absolute inset-0 bg-ink/40"
              onClick={() => setConfirmLeave(false)}
            />
            <motion.div
              role="dialog"
              aria-modal="true"
              initial={{ opacity: 0, y: 12, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 6, scale: 0.98 }}
              transition={{ duration: 0.22, ease: "easeOut" }}
              className="relative w-full max-w-sm rounded-xl bg-white p-6 shadow-cta border border-brand-100"
            >
              <h3 className="text-lg font-extrabold text-ink mb-2">
                確定要離開？
              </h3>
              <p className="text-sm text-ink-soft leading-relaxed mb-6">
                目前的練習進度將會遺失，無法復原。
              </p>
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => setConfirmLeave(false)}
                  className="px-4 py-2.5 rounded-lg text-sm font-bold text-ink bg-bg-surface hover:bg-bg-muted transition-colors"
                >
                  繼續練習
                </button>
                <button
                  type="button"
                  onClick={confirmLeaveAndGo}
                  className="px-4 py-2.5 rounded-lg text-sm font-bold text-white bg-brand-600 hover:opacity-90 active:scale-[0.98] transition-all"
                >
                  確定離開
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
