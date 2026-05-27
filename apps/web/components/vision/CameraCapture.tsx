"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Camera, CameraOff, Loader2 } from "lucide-react";
import type { AnatomyRegion, MarkerDetection } from "@ticdss/shared-types";
import { detectMarkers, postTrackSample, resetTracker } from "@/lib/vision";
import { MarkerOverlay } from "./MarkerOverlay";

interface Props {
  /** Polling interval for marker detection (ms). Default 500ms = 2 fps. */
  detectIntervalMs?: number;
  /** Called every time markers are re-detected. */
  onDetections?: (detections: MarkerDetection[]) => void;
  /** When provided, the component also posts visible IDs to the per-
   *  session tracker and exposes "currently touched" regions. */
  sessionId?: string;
  onTouchedRegionsChange?: (regions: AnatomyRegion[]) => void;
  /** Stop polling & free the webcam stream. */
  active?: boolean;
  /** Optional: bypass tracker calls (useful for the calibration page). */
  trackingDisabled?: boolean;
  /** Pass-through to MarkerOverlay: render giant IDs for calibration. */
  largeIds?: boolean;
}

/**
 * Wave 1.5 — webcam preview + marker detection overlay + tracker.
 *
 * Per-tick flow when `sessionId` is provided:
 *   1. capture JPEG from <video>
 *   2. POST /vision/markers/detect → MarkerDetection[]
 *   3. POST /vision/sessions/{id}/track → currently touched regions
 *   4. fire callbacks
 *
 * In-flight guard: skips a tick if the previous call hasn't returned.
 * This prevents request pileup when the backend is slow.
 */
export function CameraCapture({
  detectIntervalMs = 500,
  onDetections,
  sessionId,
  onTouchedRegionsChange,
  active = true,
  trackingDisabled = false,
  largeIds = false,
}: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const inFlightRef = useRef<boolean>(false);

  const [state, setState] = useState<"idle" | "starting" | "running" | "error">(
    "idle",
  );
  const [error, setError] = useState<string | null>(null);
  const [detections, setDetections] = useState<MarkerDetection[]>([]);
  const [touchedRegions, setTouchedRegions] = useState<AnatomyRegion[]>([]);
  const [backend, setBackend] = useState<"opencv" | "stub">("stub");
  const [frameDims, setFrameDims] = useState<{ w: number; h: number }>({
    w: 640,
    h: 480,
  });

  // ── Start / stop webcam ──────────────────────────────────────────────

  const stop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setState("idle");
    setDetections([]);
    setTouchedRegions([]);
    if (sessionId && !trackingDisabled) {
      void resetTracker(sessionId);
    }
  }, [sessionId, trackingDisabled]);

  const start = useCallback(async () => {
    if (state === "running" || state === "starting") return;
    setState("starting");
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setState("running");
    } catch (err) {
      const msg =
        err instanceof Error
          ? err.message
          : "無法存取攝影機，請確認瀏覽器權限。";
      setError(msg);
      setState("error");
    }
  }, [state]);

  // ── Detection polling loop ───────────────────────────────────────────

  const captureAndDetect = useCallback(async () => {
    if (inFlightRef.current) return; // backend slower than poll rate — skip
    if (!videoRef.current || !canvasRef.current) return;
    const v = videoRef.current;
    const c = canvasRef.current;
    if (v.videoWidth === 0 || v.videoHeight === 0) return;

    c.width = v.videoWidth;
    c.height = v.videoHeight;
    const ctx = c.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(v, 0, 0, c.width, c.height);
    const dataUrl = c.toDataURL("image/jpeg", 0.55);

    inFlightRef.current = true;
    try {
      const result = await detectMarkers(dataUrl);
      setDetections(result.detections);
      setBackend(result.backend);
      setFrameDims({ w: result.frameW || c.width, h: result.frameH || c.height });
      onDetections?.(result.detections);

      if (sessionId && !trackingDisabled) {
        const ids = result.detections.map((d) => d.arucoId);
        const track = await postTrackSample(sessionId, ids);
        setTouchedRegions(track.touchedRegions);
        onTouchedRegionsChange?.(track.touchedRegions);
      }
    } catch {
      // swallow — keep camera running even if backend is down
    } finally {
      inFlightRef.current = false;
    }
  }, [onDetections, onTouchedRegionsChange, sessionId, trackingDisabled]);

  useEffect(() => {
    if (state !== "running" || !active) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }
    intervalRef.current = setInterval(captureAndDetect, detectIntervalMs);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [state, active, detectIntervalMs, captureAndDetect]);

  // Cleanup on unmount
  useEffect(() => stop, [stop]);

  // ── UI ───────────────────────────────────────────────────────────────

  return (
    <div className="rounded-xl border border-subtle bg-bg-surface p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Camera size={16} className="text-brand-500" />
          <h3 className="text-sm font-semibold text-ink">攝影機評估</h3>
          {state === "running" && (
            <span
              className={`text-[10px] uppercase tracking-widest font-bold px-2 py-0.5 rounded-full ${
                backend === "opencv"
                  ? "bg-emerald-50 text-emerald-700"
                  : "bg-amber-50 text-amber-700"
              }`}
            >
              {backend === "opencv" ? "偵測中" : "STUB（後端未啟用 OpenCV）"}
            </span>
          )}
          {state === "running" && touchedRegions.length > 0 && (
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-brand-100 text-brand-600">
              觸碰中 · {touchedRegions.length}
            </span>
          )}
        </div>
        {state !== "running" ? (
          <button
            type="button"
            onClick={start}
            className="px-3 py-1.5 rounded-md text-xs font-semibold bg-brand-500 text-white hover:opacity-90 disabled:opacity-50 flex items-center gap-1.5"
            disabled={state === "starting"}
            aria-label="啟動攝影機"
          >
            {state === "starting" ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Camera size={14} />
            )}
            啟動攝影機
          </button>
        ) : (
          <button
            type="button"
            onClick={stop}
            className="px-3 py-1.5 rounded-md text-xs font-semibold bg-bg-muted text-ink-soft hover:bg-brand-100 flex items-center gap-1.5"
            aria-label="停止攝影機"
          >
            <CameraOff size={14} />
            停止
          </button>
        )}
      </div>

      <div className="relative w-full aspect-video bg-black rounded-lg overflow-hidden">
        <video
          ref={videoRef}
          className="w-full h-full object-contain"
          muted
          playsInline
          aria-label="攝影機預覽"
        />
        {state === "running" && (
          <MarkerOverlay
            detections={detections}
            frameW={frameDims.w}
            frameH={frameDims.h}
            largeIds={largeIds}
          />
        )}
        {state === "error" && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50 text-white text-sm">
            <div role="alert" className="text-center px-6">
              <p className="font-semibold mb-1">攝影機無法啟動</p>
              <p className="text-xs opacity-80">{error}</p>
            </div>
          </div>
        )}
        <canvas ref={canvasRef} className="hidden" />
      </div>

      <p className="text-[11px] text-ink-muted mt-2 leading-relaxed">
        Wave 1.5 骨架：ArUco 標籤偵測 + V-Agent 視覺評核。
        若顯示 STUB 表示後端未安裝 OpenCV（執行
        <code className="px-1 bg-bg-muted rounded mx-1">uv sync --extra vision</code>
        補裝）。
      </p>
    </div>
  );
}

// Expose a method to grab a one-shot keyframe — used by StepPE to build
// a burst for V-Agent. Returns a JPEG data URL (or null if not running).
export type CameraSnapshot = (() => string | null) | null;
