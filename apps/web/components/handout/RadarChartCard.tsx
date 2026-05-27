"use client";

import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";
import type { RadarPoint } from "@ticdss/shared-types";

interface Props {
  points: RadarPoint[];
}

export function RadarChartCard({ points }: Props) {
  const data = points.map((p) => ({
    label: p.label,
    score: p.score,
    fullMark: p.fullMark ?? 5,
  }));

  return (
    <section className="bg-white border border-subtle rounded-xl p-6 shadow-sm">
      <h2 className="text-lg font-bold text-ink mb-1">練習雷達圖</h2>
      <p className="text-xs text-ink-muted mb-4">
        LQQOPERA 八向度評分一覽（每軸 0-5 分）
      </p>
      <div style={{ width: "100%", height: 360 }}>
        <ResponsiveContainer>
          <RadarChart data={data} outerRadius="78%">
            <PolarGrid stroke="#D7CCC8" />
            <PolarAngleAxis
              dataKey="label"
              tick={{ fill: "#5b483f", fontSize: 12, fontWeight: 600 }}
            />
            <PolarRadiusAxis
              domain={[0, 5]}
              tick={{ fill: "#8a827e", fontSize: 10 }}
              axisLine={false}
            />
            <Radar
              name="score"
              dataKey="score"
              stroke="#A1887F"
              fill="#A1887F"
              fillOpacity={0.3}
              strokeWidth={2}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-4 gap-2 mt-4">
        {points.map((p) => (
          <div
            key={p.axis}
            className="rounded-md bg-bg-surface px-2 py-2 text-center"
          >
            <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted">
              {p.label}
            </p>
            <p className="text-lg font-extrabold text-brand-600">{p.score}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export default RadarChartCard;
