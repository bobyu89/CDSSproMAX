"use client";

import { useEffect, useState } from "react";
import { CheckCircle, FileDown, FileText, Loader2 } from "lucide-react";
import { toast } from "sonner";
import type { DuatScore, SessionRecord } from "@ticdss/shared-types";
import { completeSession, fetchSessionDetail } from "@/lib/api";
import { dimensionLabel } from "@/lib/mock";

interface Props {
  sessionId: string;
  onSessionCompleted?: () => void;
}

function arbiterPill(d: DuatScore["arbiterDecision"]) {
  if (d === "accept")
    return { cls: "bg-emerald-50 text-emerald-700", label: "通過" };
  if (d === "flag") return { cls: "bg-amber-50 text-amber-700", label: "標記" };
  if (d === "force_human")
    return { cls: "bg-rose-50 text-rose-700", label: "人工裁決" };
  return { cls: "bg-slate-100 text-slate-600", label: "未裁決" };
}

export function SessionDetail({ sessionId, onSessionCompleted }: Props) {
  const [data, setData] = useState<{
    session: SessionRecord;
    scores: DuatScore[];
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);

  const handleComplete = async () => {
    setCompleting(true);
    try {
      await completeSession(sessionId);
      toast.success("session 已標記完成");
      // Update local state optimistically
      setData((d) =>
        d
          ? {
              ...d,
              session: { ...d.session, endedAt: new Date().toISOString() },
            }
          : d,
      );
      onSessionCompleted?.();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "標記失敗";
      toast.error(msg);
    } finally {
      setCompleting(false);
    }
  };

  useEffect(() => {
    let active = true;
    setLoading(true);
    fetchSessionDetail(sessionId)
      .then((d) => {
        if (active) setData(d);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [sessionId]);

  if (loading) {
    return (
      <div className="space-y-3 animate-pulse">
        <div className="h-4 w-32 bg-bg-muted rounded" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-20 bg-bg-muted rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (!data) return null;

  const scores = data.scores;
  const finalScores = scores
    .map((s) => s.finalScore ?? s.sScore)
    .filter((n): n is number => n !== null);
  const mean =
    finalScores.length > 0
      ? finalScores.reduce((a, b) => a + b, 0) / finalScores.length
      : 0;
  const max = finalScores.length > 0 ? Math.max(...finalScores) : 0;
  const min = finalScores.length > 0 ? Math.min(...finalScores) : 0;

  return (
    <div className="space-y-6">
      {/* DUAT scores */}
      <div>
        <h4 className="text-xs uppercase tracking-widest font-bold text-ink-muted mb-3">
          DUAT 評分結果
        </h4>
        {scores.length === 0 ? (
          <div className="text-sm text-ink-muted">尚無評分資料。</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {scores.map((s) => {
              const pill = arbiterPill(s.arbiterDecision);
              const conf = s.eConfidence ?? 0;
              return (
                <div
                  key={s.id}
                  className="bg-white border border-faint rounded-lg p-3"
                >
                  <div className="text-[11px] font-semibold text-ink-soft truncate mb-1">
                    {dimensionLabel(s.rubricItemId)}
                  </div>
                  <div className="flex items-baseline gap-2 mb-2">
                    <span className="text-2xl font-extrabold text-ink">
                      {s.sScore ?? "—"}
                    </span>
                    <span className="text-[10px] text-ink-muted">/ 5</span>
                  </div>
                  <span
                    className={
                      "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium mb-2 " +
                      pill.cls
                    }
                  >
                    {pill.label}
                  </span>
                  <div className="mt-1">
                    <div className="flex justify-between text-[10px] text-ink-muted mb-0.5">
                      <span>E 信心</span>
                      <span>{(conf * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-1 bg-bg-muted rounded overflow-hidden">
                      <div
                        className="h-full bg-brand-500"
                        style={{ width: `${conf * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 統計 */}
      {scores.length > 0 && (
        <div>
          <h4 className="text-xs uppercase tracking-widest font-bold text-ink-muted mb-3">
            總體統計
          </h4>
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "平均分", value: mean.toFixed(2) },
              { label: "最高分", value: max.toString() },
              { label: "最低分", value: min.toString() },
            ].map((stat) => (
              <div
                key={stat.label}
                className="bg-white border border-faint rounded-lg p-3 text-center"
              >
                <div className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-1">
                  {stat.label}
                </div>
                <div className="text-xl font-extrabold text-ink">
                  {stat.value}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex flex-wrap gap-3 pt-2">
        {data.session.endedAt === null && (
          <button
            type="button"
            onClick={handleComplete}
            disabled={completing}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-semibold hover:opacity-90 active:scale-[0.97] transition-all disabled:opacity-60"
          >
            {completing ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <CheckCircle size={16} />
            )}
            標記為已完成
          </button>
        )}
        <button
          type="button"
          onClick={() => toast("PDF 匯出尚未實作")}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-500 text-white text-sm font-semibold hover:opacity-90 active:scale-[0.97] transition-all"
        >
          <FileDown size={16} />
          下載評分報告 (PDF)
        </button>
        <button
          type="button"
          onClick={() => toast("逐字稿檢視尚未實作")}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white border border-subtle text-ink text-sm font-semibold hover:bg-bg-surface active:scale-[0.97] transition-all"
        >
          <FileText size={16} />
          查看完整逐字稿
        </button>
      </div>
    </div>
  );
}
