"use client";

import { motion } from "framer-motion";
import { ChevronDown } from "lucide-react";
import type { SessionRecord } from "@ticdss/shared-types";
import { MOCK_CASE_TITLES } from "@/lib/mock";

const PHASE_LABEL: Record<string, string> = {
  scenario: "情境",
  inquiry: "問診",
  transition: "轉換",
  examination: "身體評估",
  diagnosis: "診斷",
  review: "回顧",
};

interface Props {
  session: SessionRecord;
  expanded: boolean;
  onToggle: () => void;
  children?: React.ReactNode;
}

export function SessionRow({ session, expanded, onToggle, children }: Props) {
  const title = MOCK_CASE_TITLES[session.caseId] ?? session.caseId;
  const isExam = session.mode === "exam";

  return (
    <div className="bg-white border border-subtle rounded-xl shadow-sm overflow-hidden transition-shadow hover:shadow-card">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center gap-4 py-4 px-6 text-left"
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-1.5 flex-wrap">
            <span className="font-semibold text-ink truncate">{title}</span>
            <span
              className={
                "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold " +
                (isExam
                  ? "bg-danger-soft text-danger"
                  : "bg-brand-100 text-brand-600")
              }
            >
              {isExam ? "OSCE" : "練習"}
            </span>
            <span className="inline-flex items-center rounded-full bg-bg-muted px-2 py-0.5 text-[11px] font-medium text-ink-soft">
              {PHASE_LABEL[session.phase] ?? session.phase}
            </span>
          </div>
          <div className="text-xs text-ink-muted">
            {new Date(session.startedAt).toLocaleString("zh-TW")}
          </div>
        </div>
        <motion.div
          animate={{ rotate: expanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="text-ink-muted flex-shrink-0"
        >
          <ChevronDown size={20} />
        </motion.div>
      </button>
      {expanded && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          transition={{ duration: 0.2 }}
          className="border-t border-faint"
        >
          <div className="px-6 py-5 bg-bg-surface/40">{children}</div>
        </motion.div>
      )}
    </div>
  );
}
