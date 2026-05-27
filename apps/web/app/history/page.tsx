"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import type { SessionMode, SessionRecord } from "@ticdss/shared-types";
import { fetchSessions } from "@/lib/api";
import { SessionRow } from "@/components/history/SessionRow";
import { SessionDetail } from "@/components/history/SessionDetail";

type Filter = "all" | SessionMode;

const FILTERS: { key: Filter; label: string }[] = [
  { key: "all", label: "全部" },
  { key: "practice", label: "練習" },
  { key: "exam", label: "OSCE" },
];

export default function HistoryPage() {
  const [sessions, setSessions] = useState<SessionRecord[] | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    fetchSessions().then(setSessions);
  }, []);

  const filtered = useMemo(() => {
    if (!sessions) return [];
    if (filter === "all") return sessions;
    return sessions.filter((s) => s.mode === filter);
  }, [sessions, filter]);

  return (
    <div className="max-w-6xl mx-auto py-8 lg:py-12 px-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold tracking-tight text-ink mb-2">
          歷史記錄
        </h1>
        <p className="text-ink-muted text-base">追蹤你的訓練歷程</p>
      </div>

      {/* Filter bar */}
      <div className="inline-flex gap-1 rounded-lg bg-bg-surface p-1 mb-6 border border-faint">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            type="button"
            onClick={() => setFilter(f.key)}
            className={
              "rounded-md px-4 py-1.5 text-sm font-semibold transition-colors " +
              (filter === f.key
                ? "bg-white text-brand-600 shadow-sm"
                : "text-ink-muted hover:text-brand-500")
            }
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Loading skeleton */}
      {sessions === null && (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="h-20 rounded-xl bg-bg-surface border border-faint animate-pulse"
            />
          ))}
        </div>
      )}

      {/* Empty state */}
      {sessions !== null && filtered.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center py-16 px-6 bg-white border border-subtle rounded-xl"
        >
          <p className="text-ink-muted mb-6">
            您尚未進行任何訓練，立刻開始第一次練習吧。
          </p>
          <Link
            href="/practice"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-brand-500 text-white font-bold text-sm hover:opacity-90 active:scale-[0.97] transition-all"
          >
            開始練習
            <ArrowRight size={16} />
          </Link>
        </motion.div>
      )}

      {/* Sessions list */}
      {sessions !== null && filtered.length > 0 && (
        <div className="space-y-3">
          {filtered.map((s, i) => (
            <motion.div
              key={s.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
            >
              <SessionRow
                session={s}
                expanded={expandedId === s.id}
                onToggle={() =>
                  setExpandedId(expandedId === s.id ? null : s.id)
                }
              >
                {expandedId === s.id && (
                <SessionDetail
                  sessionId={s.id}
                  onSessionCompleted={() => {
                    fetchSessions().then(setSessions);
                  }}
                />
              )}
              </SessionRow>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
