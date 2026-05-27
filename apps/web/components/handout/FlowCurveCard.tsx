"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Waves } from "lucide-react";
import type { FlowPoint } from "@ticdss/shared-types";

interface Props {
  data: FlowPoint[];
}

const ZONE_TINT = {
  flow: "rgba(16, 185, 129, 0.12)",
  anxiety: "rgba(244, 63, 94, 0.12)",
  boredom: "rgba(245, 158, 11, 0.12)",
  apathy: "rgba(100, 116, 139, 0.10)",
} as const;

const ZONE_LABEL = {
  flow: "心流",
  anxiety: "焦慮",
  boredom: "倦怠",
  apathy: "冷感",
} as const;

export function FlowCurveCard({ data }: Props) {
  // build zone backgrounds by emitting one Area per zone, masked.
  const zoneData = data.map((p) => ({
    ...p,
    flowBg: p.zone === "flow" ? 5 : 0,
    anxietyBg: p.zone === "anxiety" ? 5 : 0,
    boredomBg: p.zone === "boredom" ? 5 : 0,
    apathyBg: p.zone === "apathy" ? 5 : 0,
  }));

  return (
    <section className="bg-white border border-subtle rounded-xl p-6 shadow-sm">
      <h2 className="text-lg font-bold text-ink mb-1 flex items-center gap-2">
        <Waves size={18} className="text-brand-500" /> 預測心流曲線
      </h2>
      <p className="text-xs text-ink-muted mb-4">
        Csikszentmihalyi 心流理論：當挑戰 ≈ 技能且兩者皆高 → 心流；挑戰&gt;技能 → 焦慮；技能&gt;挑戰 → 倦怠。
      </p>

      <div style={{ width: "100%", height: 260 }}>
        <ResponsiveContainer>
          <AreaChart data={zoneData} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
            <CartesianGrid stroke="#F4EFEC" strokeDasharray="3 3" />
            <XAxis
              dataKey="tMin"
              tick={{ fill: "#8a827e", fontSize: 11 }}
              axisLine={{ stroke: "#D7CCC8" }}
              tickLine={false}
            />
            <YAxis
              domain={[0, 5]}
              tick={{ fill: "#8a827e", fontSize: 11 }}
              axisLine={{ stroke: "#D7CCC8" }}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                background: "#FDFBF9",
                border: "1px solid #D7CCC8",
                borderRadius: 8,
                fontSize: 12,
              }}
              formatter={(v: number, name: string) => {
                if (name.endsWith("Bg")) return ["", ""];
                return [v?.toFixed?.(2) ?? v, name];
              }}
              labelFormatter={(t) => `第 ${t} 分鐘`}
            />
            {/* zone backgrounds */}
            <Area dataKey="flowBg" stroke="none" fill={ZONE_TINT.flow} isAnimationActive={false} />
            <Area dataKey="anxietyBg" stroke="none" fill={ZONE_TINT.anxiety} isAnimationActive={false} />
            <Area dataKey="boredomBg" stroke="none" fill={ZONE_TINT.boredom} isAnimationActive={false} />
            <Area dataKey="apathyBg" stroke="none" fill={ZONE_TINT.apathy} isAnimationActive={false} />
            {/* actual curves */}
            <Area
              type="monotone"
              dataKey="challenge"
              stroke="#A1887F"
              strokeWidth={2}
              fill="rgba(161, 136, 127, 0.35)"
              name="挑戰"
            />
            <Area
              type="monotone"
              dataKey="skill"
              stroke="#5b483f"
              strokeWidth={2}
              fill="rgba(91, 72, 63, 0.25)"
              name="技能"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="flex flex-wrap items-center gap-4 mt-3 text-xs text-ink-muted">
        {(Object.keys(ZONE_LABEL) as Array<keyof typeof ZONE_LABEL>).map((k) => (
          <span key={k} className="inline-flex items-center gap-1.5">
            <span
              className="inline-block w-3 h-3 rounded-sm"
              style={{ background: ZONE_TINT[k] }}
            />
            {ZONE_LABEL[k]}
          </span>
        ))}
      </div>
    </section>
  );
}

export default FlowCurveCard;
