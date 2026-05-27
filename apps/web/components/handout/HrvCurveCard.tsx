"use client";

import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Activity } from "lucide-react";
import type { HrvTimePoint } from "@ticdss/shared-types";

interface Props {
  data: HrvTimePoint[];
  phaseBoundaries: { tMin: number; label: string }[];
}

// Compute contiguous stress bands where RMSSD < 20
function stressBands(data: HrvTimePoint[]): { start: number; end: number }[] {
  const out: { start: number; end: number }[] = [];
  let band: { start: number; end: number } | null = null;
  for (const p of data) {
    if (p.rmssd < 20) {
      if (!band) band = { start: p.tMin, end: p.tMin };
      else band.end = p.tMin;
    } else if (band) {
      out.push(band);
      band = null;
    }
  }
  if (band) out.push(band);
  return out;
}

export function HrvCurveCard({ data, phaseBoundaries }: Props) {
  const bands = stressBands(data);

  // Mash into a single series with "stressTop" for the band overlay
  const merged = data.map((p) => ({
    ...p,
    stressZone: p.rmssd < 20 ? 100 : null,
  }));

  return (
    <section className="bg-white border border-subtle rounded-xl p-6 shadow-sm">
      <h2 className="text-lg font-bold text-ink mb-1 flex items-center gap-2">
        <Activity size={18} className="text-brand-500" /> 壓力曲線 (HRV)
      </h2>
      <p className="text-xs text-ink-muted mb-4">
        心率 (HR) 與 RMSSD 隨時間變化；RMSSD &lt; 20 ms 區段以紅色背景標示為壓力區。
        共偵測到 {bands.length} 段壓力區。
      </p>

      <div style={{ width: "100%", height: 300 }}>
        <ResponsiveContainer>
          <ComposedChart data={merged} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
            <CartesianGrid stroke="#F4EFEC" strokeDasharray="3 3" />
            <XAxis
              dataKey="tMin"
              tick={{ fill: "#8a827e", fontSize: 11 }}
              axisLine={{ stroke: "#D7CCC8" }}
              tickLine={false}
              label={{
                value: "分鐘",
                position: "insideBottomRight",
                offset: -4,
                fill: "#8a827e",
                fontSize: 11,
              }}
            />
            <YAxis
              yAxisId="hr"
              orientation="left"
              tick={{ fill: "#8a827e", fontSize: 11 }}
              axisLine={{ stroke: "#D7CCC8" }}
              tickLine={false}
              domain={[40, 140]}
            />
            <YAxis
              yAxisId="rmssd"
              orientation="right"
              tick={{ fill: "#8a827e", fontSize: 11 }}
              axisLine={{ stroke: "#D7CCC8" }}
              tickLine={false}
              domain={[0, 80]}
            />
            <Tooltip
              contentStyle={{
                background: "#FDFBF9",
                border: "1px solid #D7CCC8",
                borderRadius: 8,
                fontSize: 12,
              }}
              formatter={(v: number, name: string) => {
                if (name === "stressZone") return ["", ""];
                return [v?.toFixed?.(1) ?? v, name];
              }}
              labelFormatter={(t) => `第 ${t} 分鐘`}
            />
            <Area
              yAxisId="hr"
              type="monotone"
              dataKey="stressZone"
              stroke="none"
              fill="#fecaca"
              fillOpacity={0.4}
              isAnimationActive={false}
              name=""
            />
            <Line
              yAxisId="hr"
              type="monotone"
              dataKey="hr"
              stroke="#dc2626"
              strokeWidth={2}
              dot={false}
              name="HR"
            />
            <Line
              yAxisId="rmssd"
              type="monotone"
              dataKey="rmssd"
              stroke="#A1887F"
              strokeWidth={2}
              strokeDasharray="4 3"
              dot={false}
              name="RMSSD"
            />
            {phaseBoundaries.map((b) => (
              <ReferenceLine
                key={b.label}
                x={b.tMin}
                yAxisId="hr"
                stroke="#6f5a52"
                strokeDasharray="2 4"
                label={{
                  value: b.label,
                  position: "top",
                  fill: "#6f5a52",
                  fontSize: 10,
                  fontWeight: 600,
                }}
              />
            ))}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center gap-6 mt-3 text-xs text-ink-muted">
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block w-3 h-0.5 bg-rose-600" /> HR (bpm)
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block w-3 h-0.5 border-t-2 border-dashed border-brand-500" /> RMSSD (ms)
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="inline-block w-3 h-3 bg-rose-200 rounded-sm" /> 壓力區
        </span>
      </div>
    </section>
  );
}

export default HrvCurveCard;
