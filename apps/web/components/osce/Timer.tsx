"use client";

import { useEffect, useRef, useState } from "react";
import { Clock } from "lucide-react";
import { toast } from "sonner";

interface TimerProps {
  totalSeconds: number;
  onTimeUp: () => void;
  active: boolean;
}

function format(s: number): string {
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${m.toString().padStart(2, "0")}:${r.toString().padStart(2, "0")}`;
}

export function Timer({ totalSeconds, onTimeUp, active }: TimerProps) {
  const [remaining, setRemaining] = useState(totalSeconds);
  const warnedRef = useRef(false);
  const firedRef = useRef(false);

  // Reset when totalSeconds changes (new step started)
  useEffect(() => {
    setRemaining(totalSeconds);
    warnedRef.current = false;
    firedRef.current = false;
  }, [totalSeconds]);

  useEffect(() => {
    if (!active) return;
    const id = setInterval(() => {
      setRemaining((prev) => {
        const next = prev - 1;
        if (next === 60 && !warnedRef.current) {
          warnedRef.current = true;
          try {
            toast("剩餘 1 分鐘", { description: "請加快作答節奏" });
          } catch {
            /* ignore */
          }
        }
        if (next <= 0 && !firedRef.current) {
          firedRef.current = true;
          // Defer onTimeUp to avoid setState during render
          setTimeout(() => onTimeUp(), 0);
          return 0;
        }
        return next;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [active, onTimeUp]);

  const danger = remaining < 30;
  const pct =
    totalSeconds > 0
      ? Math.max(0, Math.min(100, (remaining / totalSeconds) * 100))
      : 0;

  return (
    <div
      className={[
        "rounded-xl border px-4 py-3 transition-colors",
        danger
          ? "border-danger/40 bg-danger/5 text-danger"
          : "border-faint bg-bg-surface text-ink",
      ].join(" ")}
    >
      <div className="flex items-center justify-between gap-3 mb-2">
        <div className="flex items-center gap-1.5">
          <Clock size={14} />
          <span className="text-[10px] uppercase tracking-widest font-bold">
            剩餘時間
          </span>
        </div>
        <span className="text-2xl font-extrabold tabular-nums tracking-tight">
          {format(remaining)}
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-bg-muted overflow-hidden">
        <div
          className={[
            "h-full rounded-full transition-[width] duration-700 ease-linear",
            danger ? "bg-danger" : "bg-brand-500",
          ].join(" ")}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default Timer;
