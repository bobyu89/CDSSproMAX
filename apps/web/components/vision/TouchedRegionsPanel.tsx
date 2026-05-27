"use client";

import { CheckCircle2, Circle } from "lucide-react";
import type { AnatomyMarker, AnatomyRegion } from "@ticdss/shared-types";

interface Props {
  anatomyMap: AnatomyMarker[];
  touchedRegions: AnatomyRegion[];
  expectedRegion?: AnatomyRegion;
}

/**
 * Sidebar panel listing all 15 anatomy regions. Shows which are currently
 * "touched" (marker occluded ≥ threshold) and highlights the expected one
 * for the current rubric item.
 */
export function TouchedRegionsPanel({
  anatomyMap,
  touchedRegions,
  expectedRegion,
}: Props) {
  const touched = new Set(touchedRegions);
  return (
    <div className="rounded-xl border border-subtle bg-white p-4">
      <h3 className="text-xs font-bold uppercase tracking-widest text-ink-muted mb-3">
        標籤狀態 ({anatomyMap.length} 個)
      </h3>
      <ul className="space-y-1.5">
        {anatomyMap.map((m) => {
          const isTouched = touched.has(m.region);
          const isExpected = expectedRegion === m.region;
          return (
            <li
              key={m.arucoId}
              className={[
                "flex items-center gap-2 px-2 py-1.5 rounded-md text-xs",
                isExpected
                  ? "bg-brand-100 border border-brand-300"
                  : isTouched
                    ? "bg-emerald-50"
                    : "bg-bg-surface",
              ].join(" ")}
            >
              {isTouched ? (
                <CheckCircle2 size={14} className="text-emerald-600 flex-shrink-0" />
              ) : (
                <Circle size={14} className="text-ink-muted flex-shrink-0" />
              )}
              <span className="font-mono text-ink-muted">#{m.arucoId}</span>
              <span
                className={`flex-1 ${
                  isExpected ? "font-semibold text-brand-600" : "text-ink-soft"
                }`}
              >
                {m.labelZh}
              </span>
              {isExpected && (
                <span className="text-[10px] uppercase tracking-widest font-bold text-brand-600">
                  目標
                </span>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
