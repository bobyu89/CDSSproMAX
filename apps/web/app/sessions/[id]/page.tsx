"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { fetchSessionDetail, type SessionDetail } from "@/lib/api";
import { MOCK_CASE_TITLES } from "@/lib/mock";
import { GradingCard } from "@/components/GradingCard";

function durationMinutes(started: string, ended: string | null): string {
  if (!ended) return "進行中";
  const ms = new Date(ended).getTime() - new Date(started).getTime();
  return `${Math.round(ms / 60000)} 分鐘`;
}

export default function SessionDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id ?? "";
  const [detail, setDetail] = useState<SessionDetail | null>(null);

  useEffect(() => {
    if (!id) return;
    fetchSessionDetail(id).then(setDetail);
  }, [id]);

  if (!detail) {
    return (
      <main className="mx-auto max-w-5xl px-6 py-10 text-slate-400">
        載入中…
      </main>
    );
  }

  const { session, scores } = detail;

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <div className="mb-2 text-sm">
        <Link
          href="/sessions"
          className="text-slate-500 hover:text-slate-900"
        >
          ← 返回 Sessions
        </Link>
      </div>

      <div className="mb-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-bold tracking-tight">
          {MOCK_CASE_TITLES[session.caseId] ?? session.caseId}
        </h1>
        <dl className="mt-4 grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
          <div>
            <dt className="text-slate-500">模式</dt>
            <dd className="font-medium text-slate-900">
              {session.mode === "exam" ? "考試" : "練習"}
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">學員</dt>
            <dd className="font-medium text-slate-900">
              {session.participantId}
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">階段</dt>
            <dd className="font-medium text-slate-900">{session.phase}</dd>
          </div>
          <div>
            <dt className="text-slate-500">總時長</dt>
            <dd className="font-medium text-slate-900">
              {durationMinutes(session.startedAt, session.endedAt)}
            </dd>
          </div>
        </dl>
      </div>

      <h2 className="mb-3 text-lg font-semibold text-slate-900">
        評分項目（{scores.length}）
      </h2>

      {scores.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 bg-white p-10 text-center text-slate-400">
          此場次尚無 DUAT 評分結果
        </div>
      ) : (
        <div className="space-y-4">
          {scores.map((s) => (
            <GradingCard key={s.id} score={s} />
          ))}
        </div>
      )}
    </main>
  );
}
