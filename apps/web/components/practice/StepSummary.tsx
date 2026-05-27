"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Loader2, RotateCcw, Home, AlertCircle, CheckCircle2, FileText } from "lucide-react";
import type { DuatScore } from "@ticdss/shared-types";
import { useCdssStore } from "@/lib/cdssStore";
import { scoreAllLqqopera } from "@/lib/api";
import { MOCK_DUAT_SCORES, dimensionLabel } from "@/lib/mock";
import { ArbiterPill } from "@/components/Pill";

interface ChallengePoint {
  text: string;
}

interface DisplayScore {
  rubricItemId: string;
  sScore: number | null;
  eConfidence: number | null;
  arbiterAction: "accept" | "flag" | "force_human" | null;
  challengedPoints: ChallengePoint[];
}

function toDisplay(d: DuatScore): DisplayScore {
  return {
    rubricItemId: d.rubricItemId,
    sScore: d.sScore,
    eConfidence: d.eConfidence,
    arbiterAction: d.arbiterDecision,
    challengedPoints:
      d.arbiterDecision === "accept"
        ? []
        : [{ text: d.arbiterDecision === "flag" ? "雙評分歧異中等，建議再次審視證據是否充分。" : "證據不足或雙評分高度衝突，需人工介入。" }],
  };
}

const FALLBACK = (MOCK_DUAT_SCORES["sess-001"] ?? []).map(toDisplay);

export function StepSummary() {
  const router = useRouter();
  const sessionId = useCdssStore((s) => s.sessionId);
  const scenario = useCdssStore((s) => s.scenario);
  const reset = useCdssStore((s) => s.reset);

  const [loading, setLoading] = useState(true);
  const [scores, setScores] = useState<DisplayScore[]>([]);
  const [usedMock, setUsedMock] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      setLoading(true);
      if (!sessionId) {
        if (alive) {
          setScores(FALLBACK);
          setUsedMock(true);
          setLoading(false);
        }
        return;
      }
      try {
        const raw = await scoreAllLqqopera(sessionId, scenario ?? "");
        // Backend shape may vary across waves — best-effort coercion, otherwise mock.
        if (Array.isArray(raw) && raw.length > 0) {
          const mapped: DisplayScore[] = raw.map((r) => {
            const row = r as Partial<DuatScore> & Record<string, unknown>;
            return {
              rubricItemId:
                (row.rubricItemId as string) ??
                (row["rubric_item_id"] as string) ??
                "lqqopera.unknown",
              sScore: (row.sScore as number | null) ?? (row["s_score"] as number | null) ?? null,
              eConfidence:
                (row.eConfidence as number | null) ??
                (row["e_confidence"] as number | null) ??
                null,
              arbiterAction:
                ((row.arbiterDecision as DisplayScore["arbiterAction"]) ??
                  (row["arbiter_decision"] as DisplayScore["arbiterAction"]) ??
                  null),
              challengedPoints: Array.isArray(row["challenged_points"])
                ? (row["challenged_points"] as unknown[]).map((t) => ({
                    text: String(t),
                  }))
                : [],
            };
          });
          if (alive) {
            setScores(mapped);
            setUsedMock(false);
          }
        } else {
          if (alive) {
            setScores(FALLBACK);
            setUsedMock(true);
          }
        }
      } catch {
        if (alive) {
          setScores(FALLBACK);
          setUsedMock(true);
        }
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [sessionId, scenario]);

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="max-w-3xl mx-auto py-24 text-center"
      >
        <Loader2
          size={36}
          className="animate-spin text-brand-500 mx-auto mb-6"
        />
        <p className="text-base font-semibold text-ink mb-1">
          DUAT 五代理人正在評分中…
        </p>
        <p className="text-sm text-ink-muted">
          E-Agent 萃取證據 → S-Agent 評分 → A-Agent 對抗審查 → 仲裁
        </p>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="max-w-5xl mx-auto"
    >
      <div className="mb-8">
        <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-2">
          Step 6 / 6
        </p>
        <h2 className="text-3xl font-extrabold text-ink mb-2">
          DUAT 多代理人回饋
        </h2>
        <p className="text-ink-muted text-sm">
          以下為各 LQQOPERA 維度的 S-Agent 分數、E-Agent 信心與 A-Agent 對抗審查結果。
        </p>
        {usedMock && (
          <p className="mt-3 inline-flex items-center gap-1.5 text-[11px] text-brand-600 font-bold bg-brand-100 px-2.5 py-1 rounded-md">
            <AlertCircle size={12} /> 後端未連線，目前顯示示範資料
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-10">
        {scores.map((s, i) => {
          const confPct =
            s.eConfidence != null ? Math.round(s.eConfidence * 100) : null;
          return (
            <motion.div
              key={`${s.rubricItemId}-${i}`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04, duration: 0.25 }}
              className="rounded-xl bg-white border border-brand-100 p-5"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-[10px] uppercase tracking-widest font-bold text-brand-600 mb-1">
                    {s.rubricItemId.replace(/^lqqopera\./, "")}
                  </p>
                  <p className="text-sm font-bold text-ink">
                    {dimensionLabel(s.rubricItemId)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-3xl font-extrabold text-brand-500 leading-none">
                    {s.sScore ?? "—"}
                  </p>
                  <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mt-1">
                    S-Score / 5
                  </p>
                </div>
              </div>

              <div className="mb-3">
                <ArbiterPill action={s.arbiterAction} />
              </div>

              {confPct != null && (
                <div className="mb-3">
                  <div className="flex items-center justify-between text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-1">
                    <span>E-Agent 信心</span>
                    <span>{confPct}%</span>
                  </div>
                  <div className="h-1.5 bg-bg-surface rounded-full overflow-hidden">
                    <div
                      className={
                        confPct >= 75
                          ? "h-full bg-brand-500"
                          : confPct >= 50
                            ? "h-full bg-brand-400"
                            : "h-full bg-danger"
                      }
                      style={{ width: `${confPct}%` }}
                    />
                  </div>
                </div>
              )}

              {s.challengedPoints.length > 0 ? (
                <div className="mt-3 pt-3 border-t border-brand-100">
                  <p className="text-[10px] uppercase tracking-widest font-bold text-brand-600 mb-2 flex items-center gap-1">
                    <AlertCircle size={10} /> A-Agent 挑戰點
                  </p>
                  <ul className="space-y-1">
                    {s.challengedPoints.map((p, j) => (
                      <li
                        key={j}
                        className="text-xs text-ink-soft leading-relaxed"
                      >
                        • {p.text}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p className="mt-3 pt-3 border-t border-brand-100 text-[11px] text-ink-muted flex items-center gap-1.5">
                  <CheckCircle2 size={12} className="text-brand-500" />
                  A-Agent 無顯著挑戰
                </p>
              )}
            </motion.div>
          );
        })}
      </div>

      {sessionId && (
        <div className="mb-6 flex justify-center">
          <button
            type="button"
            onClick={() => router.push(`/handout/${sessionId}`)}
            className="px-8 py-4 rounded-xl font-bold text-base text-white flex items-center justify-center gap-2.5 transition-all hover:opacity-90 active:scale-[0.98] bg-brand-600 shadow-cta"
          >
            <FileText size={18} />
            查看完整講義
          </button>
        </div>
      )}

      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <button
          type="button"
          onClick={() => {
            reset();
            router.push("/practice");
          }}
          className="px-6 py-3 rounded-lg font-bold text-sm text-white flex items-center justify-center gap-2 transition-all hover:opacity-90 active:scale-[0.98] bg-brand-500"
        >
          <RotateCcw size={16} />
          再練習一次
        </button>
        <button
          type="button"
          onClick={() => {
            reset();
            router.push("/home");
          }}
          className="px-6 py-3 rounded-lg font-bold text-sm flex items-center justify-center gap-2 transition-all hover:bg-bg-muted active:scale-[0.98] bg-bg-surface text-ink border border-brand-100"
        >
          <Home size={16} />
          回首頁
        </button>
      </div>
    </motion.div>
  );
}

export default StepSummary;
