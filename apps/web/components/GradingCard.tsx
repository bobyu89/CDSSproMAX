"use client";

import { useState } from "react";
import type { DuatScore, GraderAction } from "@ticdss/shared-types";
import { ArbiterPill } from "./Pill";
import {
  MOCK_ADVOCATE_REPORTS,
  MOCK_EVIDENCE,
  dimensionLabel,
} from "@/lib/mock";
import { gradeItem } from "@/lib/api";

interface Props {
  score: DuatScore;
}

export function GradingCard({ score }: Props) {
  const [current, setCurrent] = useState<DuatScore>(score);
  const [showEvidence, setShowEvidence] = useState(false);
  const [showReasoning, setShowReasoning] = useState(false);
  const [modifyOpen, setModifyOpen] = useState(false);
  const [modifyScore, setModifyScore] = useState<number>(
    score.sScore ?? 0,
  );
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);

  const evidence = MOCK_EVIDENCE[score.id] ?? [];
  const advocateReport = MOCK_ADVOCATE_REPORTS[score.id] ?? null;

  const submit = async (
    action: GraderAction,
    finalScore: number | null,
    note: string | null,
  ) => {
    setBusy(true);
    await gradeItem(current.sessionId, current.id, action, finalScore, note);
    setCurrent((prev) => ({
      ...prev,
      graderAction: action,
      graderReason: note,
      finalScore: finalScore ?? prev.finalScore,
    }));
    setBusy(false);
    setModifyOpen(false);
  };

  const decided = current.graderAction !== null;

  return (
    <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
        <h3 className="text-sm font-semibold text-slate-900">
          {dimensionLabel(current.rubricItemId)}
        </h3>
        <div className="flex items-center gap-2">
          <ArbiterPill action={current.arbiterDecision} />
          {decided && (
            <span className="rounded-full bg-slate-900 px-2.5 py-0.5 text-xs font-medium text-white">
              已批改：{current.graderAction}
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 px-5 py-4 text-center">
        <div>
          <div className="text-xs text-slate-500">S-Agent 評分</div>
          <div className="mt-1 text-3xl font-bold text-slate-900">
            {current.sScore ?? "—"}
          </div>
        </div>
        <div>
          <div className="text-xs text-slate-500">A-Agent advocate</div>
          <div className="mt-1 text-3xl font-semibold text-slate-700">
            {current.aAdvocateScore?.toFixed(2) ?? "—"}
          </div>
        </div>
        <div>
          <div className="text-xs text-slate-500">E-Agent 信心</div>
          <div className="mt-1 text-3xl font-semibold text-slate-700">
            {current.eConfidence?.toFixed(2) ?? "—"}
          </div>
        </div>
      </div>

      <div className="border-t border-slate-100 px-5 py-3">
        <button
          type="button"
          onClick={() => setShowEvidence((v) => !v)}
          className="text-xs font-medium text-slate-600 hover:text-slate-900"
        >
          {showEvidence ? "▾" : "▸"} 證據片段（{evidence.length}）
        </button>
        {showEvidence && (
          <ul className="mt-2 space-y-1 rounded-md bg-slate-50 p-3 text-sm">
            {evidence.length === 0 && (
              <li className="text-slate-400">（無證據資料）</li>
            )}
            {evidence.map((seg, idx) => (
              <li key={idx} className="flex gap-2">
                <span
                  className={
                    seg.speaker === "student"
                      ? "shrink-0 rounded bg-sky-100 px-1.5 text-xs text-sky-800"
                      : "shrink-0 rounded bg-violet-100 px-1.5 text-xs text-violet-800"
                  }
                >
                  {seg.speaker === "student" ? "學生" : "病人"}
                </span>
                <span className="text-slate-700">{seg.text}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="border-t border-slate-100 px-5 py-3">
        <button
          type="button"
          onClick={() => setShowReasoning((v) => !v)}
          className="text-xs font-medium text-slate-600 hover:text-slate-900"
        >
          {showReasoning ? "▾" : "▸"} A-Agent 對抗報告
        </button>
        {showReasoning && (
          <p className="mt-2 rounded-md bg-amber-50 p-3 text-sm leading-relaxed text-amber-900">
            {advocateReport ?? "（A-Agent 尚未產出報告）"}
          </p>
        )}
      </div>

      <div className="border-t border-slate-100 bg-slate-50 px-5 py-3">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={busy}
            onClick={() => submit("accept", current.sScore, null)}
            className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-emerald-700 disabled:opacity-50"
          >
            接受 Accept
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => setModifyOpen((v) => !v)}
            className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-slate-700 disabled:opacity-50"
          >
            修改 Modify
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => submit("reject", 0, reason || "（無理由）")}
            className="rounded-md bg-rose-600 px-3 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-rose-700 disabled:opacity-50"
          >
            退回 Reject
          </button>
        </div>

        {modifyOpen && (
          <div className="mt-3 space-y-2 rounded-md border border-slate-200 bg-white p-3">
            <label className="block text-xs font-medium text-slate-700">
              最終分數
              <select
                value={modifyScore}
                onChange={(e) => setModifyScore(Number(e.target.value))}
                className="ml-2 rounded border border-slate-300 px-2 py-1 text-sm"
              >
                {[0, 1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-xs font-medium text-slate-700">
              修改理由
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                rows={2}
                className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-sm"
                placeholder="請說明調整原因…"
              />
            </label>
            <button
              type="button"
              disabled={busy}
              onClick={() =>
                submit("modify", modifyScore, reason || "（無理由）")
              }
              className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
            >
              送出修改
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
