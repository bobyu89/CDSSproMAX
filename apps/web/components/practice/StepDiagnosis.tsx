"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight, ClipboardList, Save } from "lucide-react";
import { toast } from "sonner";
import { useCdssStore } from "@/lib/cdssStore";

type Severity = "critical" | "high" | "moderate" | "low";

interface DxRow {
  label: string;
  text: string;
  severity: Severity;
}

const SEVERITY_LABEL: Record<Severity, string> = {
  critical: "緊急",
  high: "高",
  moderate: "中",
  low: "低",
};

const ROW_LABELS = [
  { key: "primary", label: "#1 最可能" },
  { key: "secondary", label: "#2 次可能" },
  { key: "cannot_miss", label: "#3 不可遺漏" },
] as const;

export function StepDiagnosis() {
  const sessionId = useCdssStore((s) => s.sessionId);
  const draftKey = sessionId
    ? `ticdss-draft-${sessionId}-diagnosis`
    : null;

  const [rows, setRows] = useState<Record<string, DxRow>>({
    primary: { label: ROW_LABELS[0].label, text: "", severity: "high" },
    secondary: { label: ROW_LABELS[1].label, text: "", severity: "moderate" },
    cannot_miss: { label: ROW_LABELS[2].label, text: "", severity: "critical" },
  });
  const setDiagnosis = useCdssStore((s) => s.setDiagnosis);
  const setStep = useCdssStore((s) => s.setStep);

  const [savedBadge, setSavedBadge] = useState(false);
  const badgeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const restoredRef = useRef(false);

  // Restore from localStorage on mount
  useEffect(() => {
    if (!draftKey || restoredRef.current) return;
    try {
      const raw = localStorage.getItem(draftKey);
      if (raw) {
        const parsed = JSON.parse(raw) as Record<string, DxRow>;
        if (parsed && typeof parsed === "object") {
          setRows((cur) => ({ ...cur, ...parsed }));
        }
      }
    } catch {
      /* corrupt draft — ignore */
    }
    restoredRef.current = true;
  }, [draftKey]);

  const update = (k: string, patch: Partial<DxRow>) => {
    setRows((cur) => {
      const next = { ...cur, [k]: { ...cur[k], ...patch } };
      if (draftKey) {
        try {
          localStorage.setItem(draftKey, JSON.stringify(next));
          setSavedBadge(true);
          if (badgeTimerRef.current) clearTimeout(badgeTimerRef.current);
          badgeTimerRef.current = setTimeout(() => setSavedBadge(false), 1500);
        } catch {
          /* quota — ignore */
        }
      }
      return next;
    });
  };

  const submit = () => {
    const filled = Object.values(rows).filter((r) => r.text.trim().length > 0);
    if (filled.length === 0) {
      toast.error("請至少填寫一項鑑別診斷");
      return;
    }
    const serialized = ROW_LABELS.map(({ key }) => {
      const r = rows[key];
      return `${r.label}（${SEVERITY_LABEL[r.severity]}）：${r.text.trim() || "—"}`;
    }).join("\n");
    setDiagnosis(serialized);
    if (draftKey) {
      try {
        localStorage.removeItem(draftKey);
      } catch {
        /* ignore */
      }
    }
    setStep("summary");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="max-w-3xl mx-auto"
    >
      <div className="mb-8 relative">
        <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-2">
          Step 5 / 6
        </p>
        <h2 className="text-3xl font-extrabold text-ink mb-2">
          請寫下您的鑑別診斷
        </h2>
        <p className="text-ink-muted text-sm">
          依優先序填寫三項，並標註該診斷的嚴重度。
        </p>
        <AnimatePresence>
          {savedBadge && (
            <motion.div
              key="saved"
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.2 }}
              className="absolute right-0 top-0 inline-flex items-center gap-1 rounded-full bg-emerald-50 text-emerald-700 text-[11px] font-semibold px-2.5 py-1"
              aria-live="polite"
            >
              <Save size={11} />
              草稿已自動儲存
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="space-y-4 mb-8">
        {ROW_LABELS.map(({ key }, i) => {
          const r = rows[key];
          return (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05, duration: 0.25 }}
              className="rounded-xl bg-white border border-brand-100 p-5"
            >
              <div className="flex items-center gap-2 mb-3">
                <ClipboardList size={14} className="text-brand-500" />
                <p className="text-[10px] uppercase tracking-widest font-bold text-brand-600">
                  {r.label}
                </p>
              </div>
              <input
                type="text"
                value={r.text}
                onChange={(e) => update(key, { text: e.target.value })}
                placeholder="例如：急性冠心症（NSTEMI）"
                className="w-full px-4 py-3 mb-3 rounded-lg text-sm bg-bg-surface text-ink placeholder:text-ink-muted/60 focus:outline-none focus:ring-2 focus:ring-brand-500/30 border-0"
              />
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase tracking-widest font-bold text-ink-muted">
                  嚴重度
                </span>
                <select
                  value={r.severity}
                  onChange={(e) =>
                    update(key, { severity: e.target.value as Severity })
                  }
                  className="px-3 py-1.5 rounded-md text-xs font-semibold bg-bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-brand-500/30 border-0"
                >
                  {(Object.keys(SEVERITY_LABEL) as Severity[]).map((s) => (
                    <option key={s} value={s}>
                      {SEVERITY_LABEL[s]}
                    </option>
                  ))}
                </select>
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="flex justify-end">
        <button
          type="button"
          onClick={submit}
          className="px-6 py-3 rounded-lg font-bold text-sm text-white flex items-center gap-2 transition-all hover:opacity-90 active:scale-[0.98] bg-brand-500"
        >
          送出 → 查看回饋
          <ArrowRight size={16} />
        </button>
      </div>
    </motion.div>
  );
}

export default StepDiagnosis;
