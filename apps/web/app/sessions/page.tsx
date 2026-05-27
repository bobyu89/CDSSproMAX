"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { SessionMode, SessionRecord } from "@ticdss/shared-types";
import { fetchSessions } from "@/lib/api";
import { MOCK_CASE_TITLES } from "@/lib/mock";

type Filter = "all" | SessionMode;

const PHASE_LABEL: Record<string, string> = {
  scenario: "情境準備",
  inquiry: "問診",
  transition: "轉換",
  examination: "身體評估",
  diagnosis: "診斷判讀",
  review: "回顧",
};

export default function SessionsPage() {
  const [sessions, setSessions] = useState<SessionRecord[] | null>(null);
  const [filter, setFilter] = useState<Filter>("all");

  useEffect(() => {
    fetchSessions().then(setSessions);
  }, []);

  const filtered = useMemo(() => {
    if (!sessions) return [];
    if (filter === "all") return sessions;
    return sessions.filter((s) => s.mode === filter);
  }, [sessions, filter]);

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <div className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Sessions</h1>
          <p className="mt-1 text-sm text-slate-500">
            所有 OSCE 評量場次，點擊任一列進入批改畫面。
          </p>
        </div>
        <div className="flex gap-1 rounded-md bg-slate-100 p-1">
          {(["all", "practice", "exam"] as Filter[]).map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFilter(f)}
              className={
                "rounded px-3 py-1 text-sm font-medium transition-colors " +
                (filter === f
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-600 hover:text-slate-900")
              }
            >
              {f === "all" ? "全部" : f === "practice" ? "練習" : "考試"}
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-slate-600">
                案例
              </th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">
                模式
              </th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">
                階段
              </th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">
                開始時間
              </th>
              <th className="px-4 py-3 text-right font-medium text-slate-600">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {sessions === null && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                  載入中…
                </td>
              </tr>
            )}
            {sessions !== null && filtered.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                  沒有符合的場次
                </td>
              </tr>
            )}
            {filtered.map((s) => (
              <tr key={s.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-900">
                  {MOCK_CASE_TITLES[s.caseId] ?? s.caseId}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={
                      "inline-flex rounded-full px-2 py-0.5 text-xs font-medium " +
                      (s.mode === "exam"
                        ? "bg-rose-50 text-rose-700"
                        : "bg-sky-50 text-sky-700")
                    }
                  >
                    {s.mode === "exam" ? "考試" : "練習"}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {PHASE_LABEL[s.phase] ?? s.phase}
                </td>
                <td className="px-4 py-3 text-slate-500">
                  {new Date(s.startedAt).toLocaleString("zh-TW")}
                </td>
                <td className="px-4 py-3 text-right">
                  <Link
                    href={`/sessions/${s.id}`}
                    className="rounded-md bg-slate-900 px-3 py-1 text-xs font-medium text-white hover:bg-slate-700"
                  >
                    批改 →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
