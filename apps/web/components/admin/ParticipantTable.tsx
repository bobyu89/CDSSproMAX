"use client";

import type { MockParticipant } from "@/lib/mock";

const ROLE_LABEL: Record<MockParticipant["role"], string> = {
  student: "學員",
  teacher: "教師",
  admin: "管理員",
};

const ROLE_STYLE: Record<MockParticipant["role"], string> = {
  student: "bg-brand-100 text-brand-600",
  teacher: "bg-emerald-50 text-emerald-700",
  admin: "bg-danger-soft text-danger",
};

export function ParticipantTable({
  participants,
}: {
  participants: MockParticipant[];
}) {
  return (
    <div className="bg-white border border-subtle rounded-xl shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-bg-surface">
            <tr>
              {[
                "參與者代碼",
                "姓名",
                "角色",
                "訓練次數",
                "平均分數",
                "最後登入",
              ].map((h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left text-[11px] uppercase tracking-widest font-bold text-ink-muted"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[rgba(215,204,200,0.3)]">
            {participants.map((p) => (
              <tr key={p.id} className="hover:bg-bg-surface/60 transition-colors">
                <td className="px-4 py-3 font-mono text-xs text-ink-soft">
                  {p.code}
                </td>
                <td className="px-4 py-3 font-semibold text-ink">{p.name}</td>
                <td className="px-4 py-3">
                  <span
                    className={
                      "inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-semibold " +
                      ROLE_STYLE[p.role]
                    }
                  >
                    {ROLE_LABEL[p.role]}
                  </span>
                </td>
                <td className="px-4 py-3 text-ink">
                  {p.role === "student" ? p.sessionCount : "—"}
                </td>
                <td className="px-4 py-3 text-ink">
                  {p.role === "student" ? p.meanScore.toFixed(2) : "—"}
                </td>
                <td className="px-4 py-3 text-ink-muted text-xs">
                  {new Date(p.lastLoginAt).toLocaleString("zh-TW")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
