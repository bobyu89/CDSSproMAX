"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Quote, FileText, Loader2 } from "lucide-react";
import type { DuatScore, Transcript } from "@ticdss/shared-types";
import { fetchSessionDetail, fetchTranscripts } from "@/lib/api";

interface Props {
  sessionId: string;
}

interface AnnotatedTurn {
  turn: Transcript;
  matchedItems: { rubricItemId: string; relevance: number }[];
}

// Find the strongest rubric-item match for each transcript turn by
// fuzzy-matching the turn text against `evidence_segments[*].text` in
// every DuatScore.e_evidence_json. Substring match keeps the algorithm
// dependency-free and good enough for highlight UX.
function annotateTurns(
  turns: Transcript[],
  scores: DuatScore[],
): AnnotatedTurn[] {
  return turns.map((turn) => {
    const matches: { rubricItemId: string; relevance: number }[] = [];
    for (const s of scores) {
      const ev = s.eEvidenceJson as unknown as
        | { evidence_segments?: { text: string; relevance_score?: number }[] }
        | null;
      if (!ev?.evidence_segments?.length) continue;
      for (const seg of ev.evidence_segments) {
        if (!seg.text) continue;
        const a = turn.text.replace(/\s+/g, "");
        const b = seg.text.replace(/\s+/g, "");
        if (!a || !b) continue;
        const longer = a.length >= b.length ? a : b;
        const shorter = a.length >= b.length ? b : a;
        if (longer.includes(shorter) && shorter.length >= 4) {
          matches.push({
            rubricItemId: s.rubricItemId,
            relevance: seg.relevance_score ?? 0.5,
          });
          break;
        }
      }
    }
    return { turn, matchedItems: matches };
  });
}

function dimensionFromRubricId(id: string): string {
  if (id.startsWith("lqqopera.")) {
    const map: Record<string, string> = {
      "lqqopera.location": "Location 位置",
      "lqqopera.quality": "Quality 性質",
      "lqqopera.quantity": "Quantity 程度",
      "lqqopera.onset": "Onset 發作",
      "lqqopera.precipitating": "Precipitating 誘發",
      "lqqopera.extension": "Extension 延伸",
      "lqqopera.relieving": "Relieving 緩解",
      "lqqopera.associated_symptoms": "Associated 伴隨",
    };
    return map[id] ?? id;
  }
  if (id.startsWith("pe.")) return id.replace("pe.", "PE / ");
  return id;
}

/**
 * Annotated transcript — student/patient turns rendered with rubric-item
 * pills next to lines that became Evidence Bundle segments. Lets the
 * student see WHICH questions counted for which LQQOPERA dimension.
 *
 * Falls back to plain transcript if the session has no scores yet or
 * the evidence_segments are missing.
 */
export function AnnotatedTranscriptCard({ sessionId }: Props) {
  const [loading, setLoading] = useState(true);
  const [turns, setTurns] = useState<Transcript[]>([]);
  const [scores, setScores] = useState<DuatScore[]>([]);
  const [filter, setFilter] = useState<"all" | "matched">("all");

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [t, detail] = await Promise.all([
          fetchTranscripts(sessionId),
          fetchSessionDetail(sessionId),
        ]);
        if (!alive) return;
        setTurns(t);
        setScores(detail.scores);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [sessionId]);

  const annotated = useMemo(() => annotateTurns(turns, scores), [turns, scores]);
  const matchedCount = annotated.filter((a) => a.matchedItems.length > 0).length;

  if (loading) {
    return (
      <div className="rounded-xl border border-subtle bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2 text-ink-muted text-sm">
          <Loader2 size={14} className="animate-spin" />
          載入逐字稿…
        </div>
      </div>
    );
  }

  if (turns.length === 0) {
    return (
      <div className="rounded-xl border border-subtle bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-1">
          <FileText size={16} className="text-brand-500" />
          <h3 className="text-sm font-semibold text-ink">逐字稿標註</h3>
        </div>
        <p className="text-sm text-ink-muted">本次 session 沒有對話紀錄。</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="rounded-xl border border-subtle bg-white p-6 shadow-sm print:shadow-none"
    >
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Quote size={16} className="text-brand-500" />
            <h3 className="text-base font-semibold text-ink">逐字稿標註</h3>
          </div>
          <p className="text-xs text-ink-muted">
            共 {turns.length} 句 · 命中 rubric 維度 {matchedCount} 句
          </p>
        </div>
        <div
          className="inline-flex rounded-lg bg-bg-surface p-0.5 text-xs print:hidden"
          role="tablist"
          aria-label="篩選逐字稿"
        >
          {(["all", "matched"] as const).map((k) => (
            <button
              key={k}
              type="button"
              onClick={() => setFilter(k)}
              className={[
                "px-3 py-1.5 rounded-md font-semibold transition-colors",
                filter === k
                  ? "bg-white text-brand-600 shadow-sm"
                  : "text-ink-muted hover:text-ink",
              ].join(" ")}
            >
              {k === "all" ? "全部" : "僅顯示命中"}
            </button>
          ))}
        </div>
      </div>

      <ul className="space-y-2 max-h-[600px] overflow-y-auto pr-2 print:max-h-none print:overflow-visible">
        {annotated.map(({ turn, matchedItems }, i) => {
          if (filter === "matched" && matchedItems.length === 0) return null;
          const isStudent = turn.speaker === "student";
          return (
            <li
              key={turn.id || i}
              className={[
                "rounded-lg px-3 py-2 border-l-4",
                isStudent
                  ? "bg-bg-surface border-brand-500"
                  : "bg-white border-brand-200",
                matchedItems.length > 0 ? "ring-1 ring-emerald-300" : "",
              ].join(" ")}
            >
              <div className="flex items-baseline gap-2 mb-0.5">
                <span className="text-[10px] uppercase tracking-widest font-bold text-ink-muted">
                  {isStudent ? "學員" : "病人"}
                </span>
                <span className="text-[10px] text-ink-muted">
                  {new Date(turn.createdAt).toLocaleTimeString("zh-TW", {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                  })}
                </span>
              </div>
              <p className="text-sm text-ink leading-relaxed">{turn.text}</p>
              {matchedItems.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {matchedItems.map((m, j) => (
                    <span
                      key={j}
                      className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700"
                    >
                      命中
                      <span className="opacity-80">
                        {dimensionFromRubricId(m.rubricItemId)}
                      </span>
                      <span className="opacity-60">
                        · {(m.relevance * 100).toFixed(0)}%
                      </span>
                    </span>
                  ))}
                </div>
              )}
            </li>
          );
        })}
      </ul>

      <p className="text-[11px] text-ink-muted mt-3 leading-relaxed print:hidden">
        💡 「命中」= 該句被 E-Agent 萃取為 Evidence Bundle 的證據片段，並影響該維度的最終評分。
        把這段逐字稿帶去問督導，能聚焦在「哪些句子是有效問診」。
      </p>
    </motion.div>
  );
}
