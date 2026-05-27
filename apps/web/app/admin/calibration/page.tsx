"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  CheckCircle2,
  AlertTriangle,
  Camera as CameraIcon,
  Clock,
  XCircle,
} from "lucide-react";
import type { AnatomyMarker, MarkerDetection } from "@ticdss/shared-types";
import { useAuthStore } from "@/lib/authStore";
import { fetchAnatomyMap } from "@/lib/vision";
import { CameraCapture } from "@/components/vision/CameraCapture";

interface MarkerStatus {
  spec: AnatomyMarker;
  lastSeenAt: number | null; // epoch ms
  totalSeen: number;
}

const STABLE_THRESHOLD_MS = 3000; // continuously seen for ≥ 3s = "stable"

export default function CalibrationPage() {
  const router = useRouter();
  const role = useAuthStore((s) => s.role);
  const hydrated = useAuthStore((s) => s.hydrated);
  const [anatomyMap, setAnatomyMap] = useState<AnatomyMarker[]>([]);
  const [statuses, setStatuses] = useState<Record<number, MarkerStatus>>({});
  const continuousSinceRef = useRef<Record<number, number>>({});
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const startRef = useRef<number>(Date.now());

  // Admin guard
  useEffect(() => {
    if (hydrated && role !== "admin") router.replace("/home");
  }, [hydrated, role, router]);

  // Load 15-marker map once
  useEffect(() => {
    fetchAnatomyMap().then((map) => {
      setAnatomyMap(map);
      const seed: Record<number, MarkerStatus> = {};
      for (const m of map) {
        seed[m.arucoId] = { spec: m, lastSeenAt: null, totalSeen: 0 };
      }
      setStatuses(seed);
    });
  }, []);

  // Elapsed timer
  useEffect(() => {
    const t = setInterval(
      () => setElapsedSeconds(Math.round((Date.now() - startRef.current) / 1000)),
      500,
    );
    return () => clearInterval(t);
  }, []);

  const handleDetections = useCallback((detections: MarkerDetection[]) => {
    const now = Date.now();
    const visible = new Set(detections.map((d) => d.arucoId));
    setStatuses((prev) => {
      const next: Record<number, MarkerStatus> = { ...prev };
      for (const idStr of Object.keys(prev)) {
        const id = Number(idStr);
        const wasVisible = continuousSinceRef.current[id] !== undefined;
        const isVisible = visible.has(id);
        if (isVisible && !wasVisible) {
          continuousSinceRef.current[id] = now;
        }
        if (!isVisible) {
          delete continuousSinceRef.current[id];
        }
        if (isVisible) {
          next[id] = {
            ...prev[id],
            lastSeenAt: now,
            totalSeen: prev[id].totalSeen + 1,
          };
        }
      }
      return next;
    });
  }, []);

  const stableIds = useMemo(() => {
    const now = Date.now();
    return Object.entries(continuousSinceRef.current)
      .filter(([, since]) => now - since >= STABLE_THRESHOLD_MS)
      .map(([id]) => Number(id));
  }, [statuses]);

  const total = anatomyMap.length || 16;
  const detectedCount = Object.values(statuses).filter(
    (s) => s.lastSeenAt !== null,
  ).length;
  const stableCount = stableIds.length;

  const allStable = stableCount === total && total > 0;

  if (!hydrated || role !== "admin") return null;

  return (
    <div className="p-6 lg:p-10 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-1">
          Admin / 校準工具
        </p>
        <h1 className="text-2xl font-bold text-ink mb-1">
          ArUco 標籤偵測校準
        </h1>
        <p className="text-sm text-ink-muted">
          確認所有 {total} 個解剖標籤都能在當前光線與攝影機位置下被穩定偵測，
          再進入正式 OSCE 評核。
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <StatBlock
          Icon={CameraIcon}
          label="偵測到至少一次"
          value={`${detectedCount} / ${total}`}
          tone={detectedCount === total ? "ok" : detectedCount > 0 ? "warn" : "neutral"}
        />
        <StatBlock
          Icon={CheckCircle2}
          label="連續穩定 ≥ 3 秒"
          value={`${stableCount} / ${total}`}
          tone={allStable ? "ok" : stableCount > 0 ? "warn" : "neutral"}
        />
        <StatBlock
          Icon={Clock}
          label="校準經過時間"
          value={`${elapsedSeconds} s`}
          tone="neutral"
        />
        <StatBlock
          Icon={allStable ? CheckCircle2 : AlertTriangle}
          label="整體狀態"
          value={allStable ? "可以開始評核" : "尚未完成"}
          tone={allStable ? "ok" : "warn"}
        />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left: camera */}
        <div className="lg:col-span-2">
          <CameraCapture
            detectIntervalMs={400}
            trackingDisabled
            largeIds
            onDetections={handleDetections}
          />
          <div className="mt-3 text-xs text-ink-muted leading-relaxed">
            <strong>建議流程：</strong>
            <ol className="list-decimal pl-5 mt-1 space-y-0.5">
              <li>啟動攝影機，等待約 5 秒讓自動曝光穩定。</li>
              <li>左右移動假人或攝影機，確認每個標籤都能至少偵測一次。</li>
              <li>固定攝影機角度，連續觀察 ≥ 3 秒，確認標籤穩定鎖定（綠色狀態）。</li>
              <li>所有 {total} 個標籤都標示綠色 = 校準完成。</li>
            </ol>
          </div>
        </div>

        {/* Right: marker grid */}
        <div className="rounded-xl border border-subtle bg-white p-4">
          <h2 className="text-xs font-bold uppercase tracking-widest text-ink-muted mb-3">
            標籤狀態
          </h2>
          <ul className="space-y-1.5 max-h-[600px] overflow-y-auto pr-1">
            {anatomyMap.map((m) => {
              const status = statuses[m.arucoId];
              const stable = stableIds.includes(m.arucoId);
              const everSeen = status?.lastSeenAt !== null && status?.lastSeenAt !== undefined;
              return (
                <motion.li
                  key={m.arucoId}
                  layout
                  className={[
                    "flex items-center gap-2 px-3 py-2 rounded-md text-xs",
                    stable
                      ? "bg-emerald-50 border border-emerald-200"
                      : everSeen
                        ? "bg-amber-50 border border-amber-200"
                        : "bg-bg-surface border border-faint",
                  ].join(" ")}
                >
                  {stable ? (
                    <CheckCircle2 size={14} className="text-emerald-600 flex-shrink-0" />
                  ) : everSeen ? (
                    <AlertTriangle size={14} className="text-amber-600 flex-shrink-0" />
                  ) : (
                    <XCircle size={14} className="text-ink-muted flex-shrink-0" />
                  )}
                  <span className="font-mono text-ink-muted">#{m.arucoId}</span>
                  <span className="flex-1 font-medium text-ink-soft">
                    {m.labelZh}
                  </span>
                  <span className="text-[10px] uppercase tracking-widest font-bold text-ink-muted">
                    {stable ? "穩定" : everSeen ? "閃爍" : "未偵測"}
                  </span>
                </motion.li>
              );
            })}
          </ul>
        </div>
      </div>

      {allStable && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 rounded-xl bg-emerald-50 border border-emerald-200 p-4 flex items-center gap-3"
          role="status"
        >
          <CheckCircle2 size={20} className="text-emerald-600" />
          <div>
            <p className="font-semibold text-emerald-800 text-sm">
              所有 {total} 個標籤皆已穩定偵測
            </p>
            <p className="text-xs text-emerald-700">
              可以將攝影機固定，進入 OSCE 或練習模式進行評核。
            </p>
          </div>
        </motion.div>
      )}
    </div>
  );
}

function StatBlock({
  Icon,
  label,
  value,
  tone,
}: {
  Icon: typeof CheckCircle2;
  label: string;
  value: string;
  tone: "ok" | "warn" | "neutral";
}) {
  const toneClass = {
    ok: "bg-emerald-50 text-emerald-700 border-emerald-200",
    warn: "bg-amber-50 text-amber-700 border-amber-200",
    neutral: "bg-white text-ink border-subtle",
  }[tone];
  return (
    <div className={`rounded-xl border p-4 ${toneClass}`}>
      <div className="flex items-center gap-2 mb-1">
        <Icon size={14} />
        <p className="text-[10px] uppercase tracking-widest font-bold opacity-80">
          {label}
        </p>
      </div>
      <p className="text-xl font-extrabold">{value}</p>
    </div>
  );
}
