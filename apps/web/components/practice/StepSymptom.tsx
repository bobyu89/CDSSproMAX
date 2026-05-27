"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Loader2, Stethoscope, ArrowRight } from "lucide-react";
import { toast } from "sonner";
import { useCdssStore } from "@/lib/cdssStore";
import { useAuthStore } from "@/lib/authStore";
import { createSession, fetchCases, type CaseSummary } from "@/lib/api";

const DIFFICULTY_HINTS: Record<string, string> = {
  "1": "入門",
  "2": "中等",
  "3": "進階",
};

function guessDifficulty(c: CaseSummary): string {
  // No difficulty field on CaseSummary; derive a hint from code suffix if possible.
  const m = c.code?.match(/(\d+)/);
  if (!m) return "中等";
  const n = parseInt(m[1], 10);
  if (n <= 10) return "入門";
  if (n <= 25) return "中等";
  return "進階";
}

export function StepSymptom() {
  const [cases, setCases] = useState<CaseSummary[] | null>(null);
  const [pickingId, setPickingId] = useState<string | null>(null);
  const setCaseId = useCdssStore((s) => s.setCaseId);
  const startSession = useCdssStore((s) => s.startSession);
  const setParticipantId = useCdssStore((s) => s.setParticipantId);
  const participantId = useAuthStore((s) => s.participantId);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const list = await fetchCases();
        if (alive) setCases(list);
      } catch {
        if (alive) setCases([]);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const handlePick = async (c: CaseSummary) => {
    if (pickingId) return;
    setPickingId(c.id);
    if (participantId) setParticipantId(participantId);
    try {
      const sess = await createSession(c.id, "practice");
      setCaseId(c.id);
      startSession(sess.id, c.chief_complaint, null);
      // startSession sets currentStep to "system" — done.
      toast.success(`已開始案例：${c.title}`);
    } catch {
      // Fallback: pretend session started locally so the user can keep going.
      const mockSessId = `local-${Date.now()}`;
      setCaseId(c.id);
      startSession(mockSessId, c.chief_complaint, null);
      toast.message("使用本地練習模式（後端未連線）");
    } finally {
      setPickingId(null);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="max-w-5xl mx-auto"
    >
      <div className="mb-8">
        <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-2">
          Step 1 / 6
        </p>
        <h2 className="text-3xl font-extrabold text-ink mb-3">
          請選擇本次練習想處理的主訴
        </h2>
        <p className="text-ink-muted text-sm">
          挑選一個臨床情境後，系統會立即建立練習會談並進入下一階段。
        </p>
      </div>

      {cases === null ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-44 rounded-xl bg-bg-surface animate-pulse border border-brand-100/40"
            />
          ))}
        </div>
      ) : cases.length === 0 ? (
        <div className="rounded-xl bg-bg-surface border border-brand-100 p-10 text-center">
          <p className="text-ink-muted text-sm">目前沒有可用案例</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {cases.map((c, i) => {
            const busy = pickingId === c.id;
            const diff = guessDifficulty(c);
            return (
              <motion.button
                key={c.id}
                type="button"
                onClick={() => handlePick(c)}
                disabled={!!pickingId}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 * i, duration: 0.25 }}
                className="group text-left rounded-xl p-6 bg-white border border-brand-100 hover:border-brand-400 hover:shadow-card transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-bg-surface text-brand-500">
                    <Stethoscope size={18} />
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-widest text-ink-muted">
                    {DIFFICULTY_HINTS[diff] ?? diff}
                  </span>
                </div>
                <p className="text-[10px] uppercase tracking-widest font-bold text-brand-600 mb-1">
                  {c.code}
                </p>
                <h3 className="text-base font-bold text-ink mb-2 leading-snug">
                  {c.title}
                </h3>
                <p className="text-xs text-ink-muted leading-relaxed line-clamp-3">
                  {c.chief_complaint}
                </p>
                <div className="mt-5 flex items-center gap-1.5 text-xs font-bold text-brand-500 group-hover:text-brand-600">
                  {busy ? (
                    <>
                      <Loader2 size={14} className="animate-spin" />
                      建立中…
                    </>
                  ) : (
                    <>
                      開始此案例
                      <ArrowRight
                        size={14}
                        className="transition-transform group-hover:translate-x-0.5"
                      />
                    </>
                  )}
                </div>
              </motion.button>
            );
          })}
        </div>
      )}
    </motion.div>
  );
}

export default StepSymptom;
