"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Activity, Bluetooth, BluetoothOff, Loader2, Play, Square } from "lucide-react";
import type {
  HrvWindowResult,
  IngestSampleInput,
  PhysioStateProxy,
} from "@ticdss/shared-types";
import { fetchHrvSummary, ingestSamples } from "@/lib/physio";
import {
  type ParsedHrSample,
  type StopFn,
  connect as bleConnect,
  startNotifications,
} from "@/lib/bluetoothHrv";
import { PhysioStateBadge } from "./PhysioStateBadge";

interface Props {
  sessionId: string;
  compact?: boolean;
}

type ConnState = "disconnected" | "connecting" | "connected";

const FLUSH_INTERVAL_MS = 5000;
const HRV_POLL_MS = 10000;
const CHART_MAX_POINTS = 60;
const MOCK_MEAN_RR = 800;
const MOCK_SD_RR = 30;


function randn(): number {
  // Box-Muller — good enough for demo synthetic RR.
  const u1 = Math.random() || 1e-9;
  const u2 = Math.random();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}


export function HRVMonitor({ sessionId, compact = false }: Props) {
  const [connState, setConnState] = useState<ConnState>("disconnected");
  const [deviceName, setDeviceName] = useState<string>("");
  const [mockMode, setMockMode] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [latestHr, setLatestHr] = useState<number | null>(null);
  const [rrHistory, setRrHistory] = useState<number[]>([]);
  const [hrv, setHrv] = useState<HrvWindowResult | null>(null);

  const bufferRef = useRef<IngestSampleInput[]>([]);
  const stopRef = useRef<StopFn | null>(null);
  const flushTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const mockTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── Sample handler ───────────────────────────────────────────────────

  const handleSample = useCallback((sample: ParsedHrSample) => {
    bufferRef.current.push({
      timestampMs: sample.timestampMs,
      rToRMs: sample.rToRMs,
      heartRate: sample.heartRate,
      qualityFlag: "good",
    });
    setLatestHr(sample.heartRate);
    setRrHistory((prev) => {
      const next = [...prev, sample.rToRMs];
      if (next.length > CHART_MAX_POINTS) next.splice(0, next.length - CHART_MAX_POINTS);
      return next;
    });
  }, []);

  // ── Flush buffer to API ──────────────────────────────────────────────

  const flushBuffer = useCallback(async () => {
    const batch = bufferRef.current;
    if (batch.length === 0) return;
    const toSend = batch.splice(0, batch.length);
    const deviceId = mockMode ? "mock-device" : deviceName || "ble-hr";
    await ingestSamples(sessionId, deviceId, toSend);
  }, [sessionId, mockMode, deviceName]);

  // ── HRV polling ──────────────────────────────────────────────────────

  const pollHrv = useCallback(async () => {
    const r = await fetchHrvSummary(sessionId, 60);
    setHrv(r);
  }, [sessionId]);

  // ── Lifecycle: connect / disconnect ──────────────────────────────────

  const stopAll = useCallback(async () => {
    if (flushTimerRef.current) {
      clearInterval(flushTimerRef.current);
      flushTimerRef.current = null;
    }
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
    if (mockTimerRef.current) {
      clearInterval(mockTimerRef.current);
      mockTimerRef.current = null;
    }
    if (stopRef.current) {
      try {
        await stopRef.current();
      } catch {
        // ignore
      }
      stopRef.current = null;
    }
    // Final flush of whatever's left
    await flushBuffer().catch(() => undefined);
    setConnState("disconnected");
  }, [flushBuffer]);

  const startBle = useCallback(async () => {
    setError(null);
    setConnState("connecting");
    try {
      const device = await bleConnect();
      setDeviceName(device.name || "BLE HR");
      const stop = await startNotifications(device, handleSample);
      stopRef.current = stop;
      setConnState("connected");
      setMockMode(false);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "BLE 連線失敗";
      setError(msg);
      setConnState("disconnected");
    }
  }, [handleSample]);

  const startMock = useCallback(() => {
    setError(null);
    setMockMode(true);
    setDeviceName("示範模式");
    setConnState("connected");
    mockTimerRef.current = setInterval(() => {
      const rr = Math.round(MOCK_MEAN_RR + randn() * MOCK_SD_RR);
      handleSample({
        timestampMs: Date.now(),
        rToRMs: rr,
        heartRate: Math.round(60000 / rr),
      });
    }, 850);
  }, [handleSample]);

  // ── Start timers on connect ──────────────────────────────────────────

  useEffect(() => {
    if (connState !== "connected") return;
    flushTimerRef.current = setInterval(() => {
      void flushBuffer();
    }, FLUSH_INTERVAL_MS);
    pollTimerRef.current = setInterval(() => {
      void pollHrv();
    }, HRV_POLL_MS);
    // Kick off first poll quickly so the tiles populate.
    void pollHrv();
    return () => {
      if (flushTimerRef.current) clearInterval(flushTimerRef.current);
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [connState, flushBuffer, pollHrv]);

  // ── Cleanup on unmount ───────────────────────────────────────────────

  useEffect(() => {
    return () => {
      void stopAll();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Mini sparkline ───────────────────────────────────────────────────

  const sparkline = useMemo(() => {
    if (rrHistory.length < 2) return null;
    const w = 240;
    const h = 56;
    const minV = Math.min(...rrHistory);
    const maxV = Math.max(...rrHistory);
    const range = Math.max(maxV - minV, 1);
    const stepX = w / Math.max(rrHistory.length - 1, 1);
    const points = rrHistory
      .map((v, i) => {
        const x = i * stepX;
        const y = h - ((v - minV) / range) * h;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");
    return { w, h, points };
  }, [rrHistory]);

  // ── UI ───────────────────────────────────────────────────────────────

  const state: PhysioStateProxy = hrv?.stateProxy ?? "no_data";
  const summary = hrv?.summary ?? null;
  const tilePad = compact ? "p-3" : "p-4";

  return (
    <div className="rounded-xl border border-subtle bg-bg-surface p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-rose-500" />
          <h3 className="text-sm font-semibold text-ink">HRV 心率變異監測</h3>
          <span className="text-[10px] uppercase tracking-widest font-bold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700">
            Wave 3
          </span>
          {connState === "connected" && (
            <span
              className={[
                "text-[10px] font-bold px-2 py-0.5 rounded-full",
                mockMode
                  ? "bg-amber-50 text-amber-700"
                  : "bg-emerald-50 text-emerald-700",
              ].join(" ")}
            >
              {mockMode ? "示範" : `已連線 · ${deviceName}`}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          {connState !== "connected" ? (
            <>
              <button
                type="button"
                onClick={startBle}
                disabled={connState === "connecting"}
                className="px-3 py-1.5 rounded-md text-xs font-semibold bg-brand-500 text-white hover:opacity-90 disabled:opacity-50 flex items-center gap-1.5"
                aria-label="連線藍牙心率裝置"
              >
                {connState === "connecting" ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Bluetooth size={14} />
                )}
                連線 Polar
              </button>
              <button
                type="button"
                onClick={startMock}
                className="px-3 py-1.5 rounded-md text-xs font-semibold bg-bg-muted text-ink-soft hover:bg-brand-100 flex items-center gap-1.5"
                aria-label="使用示範模式"
              >
                <Play size={14} />
                示範模式
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={() => void stopAll()}
              className="px-3 py-1.5 rounded-md text-xs font-semibold bg-bg-muted text-ink-soft hover:bg-rose-50 hover:text-rose-700 flex items-center gap-1.5"
              aria-label="中斷連線"
            >
              <Square size={14} />
              中斷
            </button>
          )}
        </div>
      </div>

      {error && (
        <div
          role="alert"
          className="mb-3 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700 flex items-center gap-2"
        >
          <BluetoothOff size={14} />
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
        <div className={`rounded-lg bg-bg-muted ${tilePad}`}>
          <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted">
            即時 HR
          </p>
          <p className="text-xl font-extrabold text-ink mt-0.5">
            {latestHr != null ? `${latestHr}` : "—"}
            <span className="text-[10px] font-semibold text-ink-muted ml-1">
              bpm
            </span>
          </p>
        </div>
        <div className={`rounded-lg bg-bg-muted ${tilePad}`}>
          <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted">
            SDNN
          </p>
          <p className="text-xl font-extrabold text-ink mt-0.5">
            {summary ? summary.sdnn.toFixed(1) : "—"}
            <span className="text-[10px] font-semibold text-ink-muted ml-1">
              ms
            </span>
          </p>
        </div>
        <div className={`rounded-lg bg-bg-muted ${tilePad}`}>
          <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted">
            RMSSD
          </p>
          <p className="text-xl font-extrabold text-ink mt-0.5">
            {summary ? summary.rmssd.toFixed(1) : "—"}
            <span className="text-[10px] font-semibold text-ink-muted ml-1">
              ms
            </span>
          </p>
        </div>
        <div className={`rounded-lg bg-bg-muted ${tilePad}`}>
          <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted">
            狀態
          </p>
          <div className="mt-1.5">
            <PhysioStateBadge state={state} />
          </div>
        </div>
      </div>

      {sparkline && (
        <div className="rounded-lg bg-bg-muted p-2">
          <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-1">
            RR 區間趨勢（最近 {rrHistory.length} 點）
          </p>
          <svg
            width="100%"
            viewBox={`0 0 ${sparkline.w} ${sparkline.h}`}
            preserveAspectRatio="none"
            className="block w-full h-14"
            aria-label="RR 區間趨勢圖"
          >
            <polyline
              fill="none"
              stroke="currentColor"
              className="text-rose-500"
              strokeWidth={1.5}
              points={sparkline.points}
            />
          </svg>
        </div>
      )}

      <p className="text-[11px] text-ink-muted mt-2 leading-relaxed">
        Wave 3 骨架：Polar H10 (BLE 0x180D/0x2A37) → RR 區間 → 後端時間域 HRV 計算。
        本訊號目前僅作監測，尚未納入 DUAT 評分（Fusion Engine 開發中）。
      </p>
    </div>
  );
}

export default HRVMonitor;
