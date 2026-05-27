"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Award, RotateCw, Home, CheckCircle2 } from "lucide-react";
import type { DuatScore, SessionRecord } from "@ticdss/shared-types";

export interface StationResult {
  stationIdx: number; // 0-based
  title: string;
  caseId?: string | null;
  summary: { session: SessionRecord; scores: DuatScore[] } | null;
  durationS?: number | null;
}

interface Props {
  stations: StationResult[];
  totalDurationS?: number | null;
  onRestart: () => void;
}

function meanFinalScore(scores: DuatScore[]): number | null {
  const vals = scores
    .map((s) => s.finalScore ?? s.sScore)
    .filter((v): v is number => typeof v === "number");
  if (vals.length === 0) return null;
  return vals.reduce((a, b) => a + b, 0) / vals.length;
}

function arbiterBreakdown(scores: DuatScore[]): {
  accept: number;
  flag: number;
  force_human: number;
} {
  const out = { accept: 0, flag: 0, force_human: 0 } as Record<string, number>;
  for (const s of scores) {
    const a = s.arbiterDecision as unknown as string | null;
    if (a && a in out) out[a]++;
  }
  return out as { accept: number; flag: number; force_human: number };
}

function fmtScore(v: number | null): string {
  if (v === null || Number.isNaN(v)) return "—";
  return v.toFixed(2);
}

function fmtDuration(s: number | null | undefined): string {
  if (s == null) return "—";
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m}m ${r}s`;
}

export function OsceSummary({ stations, totalDurationS, onRestart }: Props) {
  const router = useRouter();

  const stationScores = stations.map((st) =>
    st.summary ? meanFinalScore(st.summary.scores) : null,
  );
  const validScores = stationScores.filter(
    (v): v is number => typeof v === "number",
  );
  const overall =
    validScores.length > 0
      ? validScores.reduce((a, b) => a + b, 0) / validScores.length
      : null;
  const completionRate =
    stations.length > 0
      ? (stations.filter((s) => s.summary !== null).length / stations.length) * 100
      : 0;

  return (
    <div className="p-8 lg:p-12 max-w-6xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-10"
      >
        <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-2">
          OSCE 考試完成
        </p>
        <h1 className="text-4xl font-extrabold text-ink tracking-tight mb-3 flex items-center gap-3">
          <Award className="text-brand-600" size={32} /> 綜合成績報告
        </h1>
        <p className="text-ink-muted text-sm leading-relaxed max-w-xl">
          以下為本次 OSCE 全部站別的綜合評分。點擊「查看詳細評分」可檢視各 LQQOPERA 維度的證據與審查紀錄。
        </p>
      </motion.div>

      {/* Station cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-10">
        {stations.map((st, i) => {
          const mean = stationScores[i];
          const ab = st.summary ? arbiterBreakdown(st.summary.scores) : null;
          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + i * 0.08 }}
              className="rounded-xl bg-white border border-faint shadow-sm p-6 flex flex-col"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] uppercase tracking-widest font-bold text-ink-muted">
                  第 {i + 1} 站
                </span>
                {st.summary && (
                  <CheckCircle2 size={14} className="text-brand-500" />
                )}
              </div>
              <h3 className="text-base font-bold text-ink mb-4 leading-snug min-h-[2.5em]">
                {st.title}
              </h3>

              <div className="rounded-lg bg-bg-surface px-3 py-3 mb-4">
                <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-1">
                  平均分數
                </p>
                <p className="text-3xl font-extrabold text-brand-600 tabular-nums">
                  {fmtScore(mean)}
                </p>
              </div>

              {ab && (
                <div className="grid grid-cols-3 gap-1.5 mb-4 text-center">
                  <div className="rounded-md bg-brand-50/50 px-2 py-1.5">
                    <p className="text-[9px] uppercase tracking-wider font-bold text-ink-muted">
                      Accept
                    </p>
                    <p className="text-sm font-bold text-ink">{ab.accept}</p>
                  </div>
                  <div className="rounded-md bg-amber-50 px-2 py-1.5">
                    <p className="text-[9px] uppercase tracking-wider font-bold text-ink-muted">
                      Flag
                    </p>
                    <p className="text-sm font-bold text-ink">{ab.flag}</p>
                  </div>
                  <div className="rounded-md bg-danger/5 px-2 py-1.5">
                    <p className="text-[9px] uppercase tracking-wider font-bold text-ink-muted">
                      Human
                    </p>
                    <p className="text-sm font-bold text-ink">
                      {ab.force_human}
                    </p>
                  </div>
                </div>
              )}

              {st.summary?.session?.id ? (
                <Link
                  href={`/sessions/${st.summary.session.id}`}
                  className="mt-auto text-xs font-bold text-brand-600 hover:text-brand-500 transition-colors"
                >
                  查看詳細評分 →
                </Link>
              ) : (
                <p className="mt-auto text-xs text-ink-muted">尚無評分資料</p>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Overall stats panel */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="rounded-xl bg-bg-surface border border-faint p-6 mb-8"
      >
        <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-4">
          全體統計
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-xs text-ink-muted mb-1">綜合平均分</p>
            <p className="text-2xl font-extrabold text-ink tabular-nums">
              {fmtScore(overall)}
            </p>
          </div>
          <div>
            <p className="text-xs text-ink-muted mb-1">完成率</p>
            <p className="text-2xl font-extrabold text-ink tabular-nums">
              {completionRate.toFixed(0)}%
            </p>
          </div>
          <div>
            <p className="text-xs text-ink-muted mb-1">總時長</p>
            <p className="text-2xl font-extrabold text-ink tabular-nums">
              {fmtDuration(totalDurationS)}
            </p>
          </div>
        </div>
      </motion.div>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button
          type="button"
          onClick={() => router.push("/home")}
          className="flex-1 px-6 py-3.5 rounded-lg font-bold text-sm text-ink flex items-center justify-center gap-2 transition-all hover:bg-bg-muted active:scale-[0.98] bg-white border border-subtle"
        >
          <Home size={16} /> 返回首頁
        </button>
        <button
          type="button"
          onClick={onRestart}
          className="flex-1 px-6 py-3.5 rounded-lg font-bold text-sm text-white flex items-center justify-center gap-2 transition-all hover:opacity-90 active:scale-[0.98] bg-brand-600"
        >
          <RotateCw size={16} /> 再考一次
        </button>
      </div>
    </div>
  );
}

export default OsceSummary;
