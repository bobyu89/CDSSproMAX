"use client";

import { motion } from "framer-motion";
import { ArrowRight, Clock, Lock, Layers, AlertTriangle } from "lucide-react";
import Link from "next/link";

interface Props {
  totalStations: number;
  onStart: () => void;
  disabled?: boolean;
}

export function PreExamCard({ totalStations, onStart, disabled }: Props) {
  const bullets = [
    {
      Icon: Layers,
      title: `${totalStations} 個臨床站別`,
      desc: "依序輪轉，完成後才會公佈所有成績。",
    },
    {
      Icon: Clock,
      title: "每站 14 分鐘",
      desc: "問診 6 分、身體評估 6 分、診斷 2 分；計時自動推進。",
    },
    {
      Icon: Lock,
      title: "不可暫停 / 回頭",
      desc: "進入考試後無法返回上一步，請預留完整時間作答。",
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="max-w-3xl mx-auto"
    >
      <div className="mb-8">
        <Link
          href="/home"
          className="text-xs uppercase tracking-widest font-bold text-ink-muted hover:text-ink-soft transition-colors"
        >
          ← 回到首頁
        </Link>
      </div>

      <div className="rounded-2xl bg-white border border-faint shadow-sm p-10 lg:p-12">
        <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-2">
          OSCE 模擬考試
        </p>
        <h1 className="text-3xl lg:text-4xl font-extrabold text-ink tracking-tight mb-4">
          開始 {totalStations} 站連續考試
        </h1>
        <p className="text-ink-muted text-sm leading-relaxed mb-8 max-w-xl">
          模擬客觀結構式臨床測驗（OSCE）情境，計時作答、自動推進，
          完成所有站別後 DUAT 五代理人會給出綜合評分報告。預估總時長約 45 分鐘。
        </p>

        <div className="mb-8 rounded-xl border border-danger/30 bg-danger/5 px-4 py-3 flex items-start gap-2.5">
          <AlertTriangle size={16} className="text-danger mt-0.5 shrink-0" />
          <p className="text-sm font-semibold text-danger">
            考試模式無法暫停或返回上一步，請確認環境安靜後再開始。
          </p>
        </div>

        <ul className="space-y-4 mb-10">
          {bullets.map(({ Icon, title, desc }, i) => (
            <motion.li
              key={title}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 + i * 0.06 }}
              className="flex items-start gap-3"
            >
              <div className="w-9 h-9 rounded-lg flex items-center justify-center bg-bg-surface text-brand-600 shrink-0">
                <Icon size={16} />
              </div>
              <div>
                <p className="text-sm font-bold text-ink">{title}</p>
                <p className="text-xs text-ink-muted leading-relaxed mt-0.5">
                  {desc}
                </p>
              </div>
            </motion.li>
          ))}
        </ul>

        <button
          type="button"
          onClick={onStart}
          disabled={disabled}
          className="w-full px-8 py-4 rounded-xl font-bold text-base text-white flex items-center justify-center gap-2 transition-all hover:opacity-90 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed bg-brand-600 shadow-sm"
        >
          我已了解，開始考試
          <ArrowRight size={18} />
        </button>
        <p className="text-center text-[10px] uppercase tracking-[0.2em] font-bold text-ink-muted mt-4">
          Official Assessment · 預估 45 分鐘
        </p>
      </div>
    </motion.div>
  );
}

export default PreExamCard;
