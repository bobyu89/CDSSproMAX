"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Target, Send } from "lucide-react";
import type { ConfidenceCalibrationResponse } from "@ticdss/shared-types";

interface Props {
  data: ConfidenceCalibrationResponse;
  onSubmit: (predictedScore: number) => Promise<void>;
}

function gapBadge(gap: number): { color: string; label: string } {
  const abs = Math.abs(gap);
  if (abs <= 1) return { color: "bg-emerald-100 text-emerald-700", label: "良好校準" };
  if (abs <= 2) return { color: "bg-amber-100 text-amber-700", label: "中等偏差" };
  return { color: "bg-rose-100 text-rose-700", label: "明顯偏差" };
}

export function ConfidenceCalibrationCard({ data, onSubmit }: Props) {
  const [predicted, setPredicted] = useState<number>(3);
  const [submitting, setSubmitting] = useState(false);

  const hasPrediction = data.predictedScore != null && data.gap != null;

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await onSubmit(predicted);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="bg-white border border-subtle rounded-xl p-6 shadow-sm">
      <h2 className="text-lg font-bold text-ink mb-1 flex items-center gap-2">
        <Target size={18} className="text-brand-500" /> 信心校準
      </h2>
      <p className="text-xs text-ink-muted mb-5">
        先預測自己會拿幾分，再揭曉實際得分 — 校準你的自我評估能力。
      </p>

      {!hasPrediction ? (
        <div className="bg-bg-surface rounded-lg p-5">
          <p className="text-sm text-ink mb-1 font-semibold">
            你預測自己這次拿幾分？
          </p>
          <p className="text-xs text-ink-muted mb-4">
            完成預測後才會揭曉實際分數（避免後見之明偏誤）
          </p>
          <div className="flex items-center gap-4 mb-4">
            <input
              type="range"
              min={0}
              max={5}
              step={0.1}
              value={predicted}
              onChange={(e) => setPredicted(parseFloat(e.target.value))}
              className="flex-1 accent-brand-500"
            />
            <div className="w-20 text-center">
              <p className="text-3xl font-extrabold text-brand-500 leading-none">
                {predicted.toFixed(1)}
              </p>
              <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mt-1">
                /5
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting}
            className="w-full px-4 py-2.5 rounded-lg bg-brand-500 text-white font-bold text-sm hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Send size={14} /> 提交預測並揭曉
          </button>
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-3 gap-3"
        >
          <div className="bg-bg-surface rounded-lg p-4 text-center">
            <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-1">
              預測
            </p>
            <p className="text-3xl font-extrabold text-ink-soft">
              {data.predictedScore!.toFixed(2)}
            </p>
          </div>
          <div className="bg-bg-surface rounded-lg p-4 text-center">
            <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-1">
              實際
            </p>
            <p className="text-3xl font-extrabold text-brand-600">
              {data.actualScore.toFixed(2)}
            </p>
          </div>
          <div className="bg-bg-surface rounded-lg p-4 text-center">
            <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-1">
              差距
            </p>
            <p className="text-3xl font-extrabold text-ink">
              {data.gap! > 0 ? "+" : ""}
              {data.gap!.toFixed(2)}
            </p>
            <span
              className={
                "inline-block mt-2 px-2 py-0.5 rounded-full text-[10px] font-bold " +
                gapBadge(data.gap!).color
              }
            >
              {gapBadge(data.gap!).label}
            </span>
          </div>
        </motion.div>
      )}
    </section>
  );
}

export default ConfidenceCalibrationCard;
