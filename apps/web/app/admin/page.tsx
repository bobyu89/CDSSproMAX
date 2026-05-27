"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  BarChart,
  Bar,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { toast } from "sonner";
import {
  Users,
  Activity,
  Award,
  CheckCircle2,
  Plus,
} from "lucide-react";
import { useAuthStore } from "@/lib/authStore";
import { fetchCases, type CaseSummary } from "@/lib/api";
import {
  MOCK_ADMIN_DASHBOARD,
  MOCK_PARTICIPANTS,
} from "@/lib/mock";
import { StatCard } from "@/components/admin/StatCard";
import { ParticipantTable } from "@/components/admin/ParticipantTable";

type Tab = "overview" | "participants" | "cases";

const TABS: { key: Tab; label: string }[] = [
  { key: "overview", label: "總覽" },
  { key: "participants", label: "學員" },
  { key: "cases", label: "案例" },
];

const BAR_COLORS = ["#A1887F", "#6f5a52", "#D7CCC8", "#8a827e", "#5b483f"];

export default function AdminPage() {
  const role = useAuthStore((s) => s.role);
  const hydrated = useAuthStore((s) => s.hydrated);
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [cases, setCases] = useState<CaseSummary[] | null>(null);
  const [enabledMap, setEnabledMap] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!hydrated) return;
    if (role !== "admin") router.replace("/home");
  }, [hydrated, role, router]);

  useEffect(() => {
    if (activeTab === "cases" && cases === null) {
      fetchCases().then((rows) => {
        setCases(rows);
        setEnabledMap(Object.fromEntries(rows.map((c) => [c.id, true])));
      });
    }
  }, [activeTab, cases]);

  if (!hydrated || role !== "admin") return null;

  const dash = MOCK_ADMIN_DASHBOARD;

  return (
    <div className="max-w-6xl mx-auto py-8 lg:py-12 px-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold tracking-tight text-ink mb-2">
          管理後台
        </h1>
        <p className="text-ink-muted text-base">
          檢視訓練統計、管理學員與案例。
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-subtle mb-8">
        <div className="flex gap-1">
          {TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => setActiveTab(t.key)}
              className={
                "px-5 py-3 text-sm transition-colors " +
                (activeTab === t.key
                  ? "border-b-2 border-brand-500 text-brand-600 font-semibold"
                  : "text-ink-muted hover:text-brand-500")
              }
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      {activeTab === "overview" && (
        <div className="space-y-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              icon={Users}
              label="總學員數"
              value={dash.totalParticipants}
              delta={5}
            />
            <StatCard
              icon={Activity}
              label="總訓練次數"
              value={dash.totalSessions}
              delta={12}
            />
            <StatCard
              icon={Award}
              label="平均分數"
              value={dash.meanScore.toFixed(2)}
              delta={3}
            />
            <StatCard
              icon={CheckCircle2}
              label="完訓率"
              value={`${(dash.completionRate * 100).toFixed(0)}%`}
              delta={-2}
            />
          </div>

          <div className="bg-white border border-subtle rounded-xl p-6 shadow-sm">
            <h3 className="text-lg font-bold text-ink mb-1">學員平均分數</h3>
            <p className="text-xs text-ink-muted mb-6">
              各參與者跨所有 session 的平均得分
            </p>
            <div style={{ width: "100%", height: 320 }}>
              <ResponsiveContainer>
                <BarChart
                  data={dash.perParticipantScores}
                  margin={{ top: 8, right: 16, bottom: 8, left: 0 }}
                >
                  <XAxis
                    dataKey="code"
                    tick={{ fill: "#8a827e", fontSize: 12 }}
                    axisLine={{ stroke: "#D7CCC8" }}
                    tickLine={false}
                  />
                  <YAxis
                    domain={[0, 5]}
                    tick={{ fill: "#8a827e", fontSize: 12 }}
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
                    formatter={(v: number) => v.toFixed(2)}
                    labelFormatter={(label: string) => {
                      const p = dash.perParticipantScores.find(
                        (x) => x.code === label,
                      );
                      return p ? `${p.code} · ${p.name}` : label;
                    }}
                  />
                  <Bar dataKey="meanScore" radius={[6, 6, 0, 0]}>
                    {dash.perParticipantScores.map((_, i) => (
                      <Cell
                        key={i}
                        fill={BAR_COLORS[i % BAR_COLORS.length]}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {activeTab === "participants" && (
        <ParticipantTable participants={MOCK_PARTICIPANTS} />
      )}

      {activeTab === "cases" && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              type="button"
              onClick={() => toast("新增案例尚未實作")}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-500 text-white text-sm font-semibold hover:opacity-90 active:scale-[0.97] transition-all"
            >
              <Plus size={16} />
              新增案例
            </button>
          </div>
          <div className="bg-white border border-subtle rounded-xl shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-bg-surface">
                  <tr>
                    {["案例代碼", "標題", "主訴", "是否啟用"].map((h) => (
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
                  {cases === null && (
                    <tr>
                      <td
                        colSpan={4}
                        className="px-4 py-8 text-center text-ink-muted"
                      >
                        載入中…
                      </td>
                    </tr>
                  )}
                  {cases !== null && cases.length === 0 && (
                    <tr>
                      <td
                        colSpan={4}
                        className="px-4 py-8 text-center text-ink-muted"
                      >
                        尚無案例
                      </td>
                    </tr>
                  )}
                  {cases?.map((c) => {
                    const enabled = enabledMap[c.id] ?? true;
                    return (
                      <tr
                        key={c.id}
                        className="hover:bg-bg-surface/60 transition-colors"
                      >
                        <td className="px-4 py-3 font-mono text-xs text-ink-soft">
                          {c.code}
                        </td>
                        <td className="px-4 py-3 font-semibold text-ink">
                          {c.title}
                        </td>
                        <td className="px-4 py-3 text-ink-soft">
                          {c.chief_complaint}
                        </td>
                        <td className="px-4 py-3">
                          <button
                            type="button"
                            onClick={() =>
                              setEnabledMap((m) => ({
                                ...m,
                                [c.id]: !enabled,
                              }))
                            }
                            className={
                              "relative inline-flex h-6 w-11 items-center rounded-full transition-colors " +
                              (enabled ? "bg-brand-500" : "bg-bg-muted")
                            }
                            aria-label="切換啟用"
                          >
                            <span
                              className={
                                "inline-block h-4 w-4 transform rounded-full bg-white transition-transform " +
                                (enabled ? "translate-x-6" : "translate-x-1")
                              }
                            />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
