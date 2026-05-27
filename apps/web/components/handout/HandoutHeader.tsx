"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft, Download, RefreshCw } from "lucide-react";

interface Props {
  caseTitle: string;
  caseCode: string;
  mode: "practice" | "exam";
  completedAt: string;
  totalScore: number;
  isAdmin: boolean;
  onRegenerate: () => void;
  onDownloadPdf: () => void;
}

export function HandoutHeader({
  caseTitle,
  caseCode,
  mode,
  completedAt,
  totalScore,
  isAdmin,
  onRegenerate,
  onDownloadPdf,
}: Props) {
  const dateStr = new Date(completedAt).toLocaleDateString("zh-TW", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white border border-subtle rounded-xl p-6 mb-6 shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4"
    >
      <div>
        <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-1">
          個人講義 · {caseCode}
        </p>
        <h1 className="text-2xl font-extrabold text-ink mb-2">{caseTitle}</h1>
        <div className="flex items-center gap-3 text-xs">
          <span
            className={
              "px-2 py-0.5 rounded-full font-bold uppercase tracking-widest text-[10px] " +
              (mode === "exam"
                ? "bg-brand-600 text-white"
                : "bg-brand-100 text-brand-600")
            }
          >
            {mode === "exam" ? "OSCE" : "練習"}
          </span>
          <span className="text-ink-muted">{dateStr}</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="text-right">
          <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted">
            總分
          </p>
          <p className="text-4xl font-extrabold text-brand-500 leading-none">
            {totalScore.toFixed(2)}
            <span className="text-base text-ink-muted font-bold ml-1">/5</span>
          </p>
        </div>
        <div className="print:hidden flex flex-col gap-2">
          {isAdmin && (
            <button
              type="button"
              onClick={onRegenerate}
              className="px-3 py-2 rounded-md text-xs font-semibold bg-bg-surface text-ink-soft hover:bg-brand-100 hover:text-brand-600 flex items-center gap-1.5 border border-faint"
            >
              <RefreshCw size={12} /> 重新生成講義
            </button>
          )}
          <button
            type="button"
            onClick={onDownloadPdf}
            className="px-3 py-2 rounded-md text-xs font-semibold bg-brand-500 text-white hover:opacity-90 flex items-center gap-1.5"
          >
            <Download size={12} /> 下載 PDF
          </button>
          <Link
            href="/history"
            className="px-3 py-2 rounded-md text-xs font-semibold bg-bg-surface text-ink-soft hover:bg-bg-muted flex items-center gap-1.5 border border-faint"
          >
            <ArrowLeft size={12} /> 回到歷史紀錄
          </Link>
        </div>
      </div>
    </motion.div>
  );
}

export default HandoutHeader;
