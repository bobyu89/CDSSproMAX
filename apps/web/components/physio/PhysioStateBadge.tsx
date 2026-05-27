"use client";

import type { PhysioStateProxy } from "@ticdss/shared-types";

const LABELS: Record<PhysioStateProxy, string> = {
  flow: "心流",
  anxious: "焦慮",
  low_engagement: "低投入",
  ambiguous: "未確定",
  no_data: "無資料",
};

const CLASSES: Record<PhysioStateProxy, string> = {
  flow: "bg-emerald-50 text-emerald-700 border-emerald-200",
  anxious: "bg-rose-50 text-rose-700 border-rose-200",
  low_engagement: "bg-amber-50 text-amber-700 border-amber-200",
  ambiguous: "bg-slate-100 text-slate-700 border-slate-200",
  no_data: "bg-slate-50 text-slate-500 border-slate-200",
};


export function PhysioStateBadge({ state }: { state: PhysioStateProxy }) {
  return (
    <span
      className={[
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold border",
        CLASSES[state],
      ].join(" ")}
      aria-label={`學習者狀態：${LABELS[state]}`}
    >
      {LABELS[state]}
    </span>
  );
}

export default PhysioStateBadge;
