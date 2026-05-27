"use client";

import type { LucideIcon } from "lucide-react";

interface Props {
  icon: LucideIcon;
  label: string;
  value: string | number;
  delta?: number; // positive = up (green); negative = down (red)
}

export function StatCard({ icon: Icon, label, value, delta }: Props) {
  const deltaColor =
    delta === undefined
      ? ""
      : delta >= 0
        ? "text-emerald-600"
        : "text-rose-600";
  const deltaSign = delta !== undefined && delta > 0 ? "+" : "";

  return (
    <div className="bg-white border border-subtle rounded-xl p-5 shadow-sm">
      <div className="flex items-start justify-between mb-3">
        <div className="p-2.5 rounded-lg bg-bg-surface text-brand-500">
          <Icon size={18} />
        </div>
        {delta !== undefined && (
          <span className={"text-xs font-bold " + deltaColor}>
            {deltaSign}
            {delta}%
          </span>
        )}
      </div>
      <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-1">
        {label}
      </p>
      <p className="text-2xl font-extrabold text-ink">{value}</p>
    </div>
  );
}
