"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Camera, CameraOff, Loader2 } from "lucide-react";
import type { MarkerDetection } from "@ticdss/shared-types";
import { detectMarkers } from "@/lib/vision";
import { MarkerOverlay } from "./MarkerOverlay";

interface Props {
  /** Polling interval for marker detection (ms). Default 500ms = 2 fps. */
  detectIntervalMs?: number;
  /** Called every time markers are re-detected. */
  onDetections?: (detections: MarkerDetection[]) => void;
  /** Stop polling & free the webcam stream. */
  active?: boolean;
}

/**
 * Wave 1.5 skeleton — webcam preview + marker detection overlay.
 *
 * Posts a JPEG frame to /vision/markers/detect every N ms. When the
 * backend has OpenCV installed the overlay shows real marker boxes;
 * without OpenCV the backend returns empty detections and the overlay
 * stays clean — UI doesn't break.
 */
export function CameraCapture({
  detectIntervalMs = 500,
  onDetections,
  active = true,
}: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [state, setState] = useState<"idle" | "starting" | "running" | "error">(
    "idle",
  );
  const [error, setError] = useState<string | null>(null);
  const [detections, setDetections] = useState<MarkerDetection[]>([]);
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
  }, []);

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
    if (!videoRef.current || !canvasRef.current) return;
    const v = videoRef.current;
    const c = canvasRef.current;
    if (v.videoWidth === 0 || v.videoHeight === 0) return;

    c.width = v.videoWidth;
    c.height = v.videoHeight;
    const ctx = c.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(v, 0, 0, c.width, c.height);
    const dataUrl = c.toDataURL("image/jpeg", 0.7);

    try {
      const result = await detectMarkers(dataUrl);
      setDetections(result.detections);
      setBackend(result.backend);
      setFrameDims({ w: result.frameW || c.width, h: result.frameH || c.height });
      onDetections?.(result.detections);
    } catch {
      // swallow — keep camera running even if backend is down
    }
  }, [onDetections]);

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
              {backend === "opencv" ? "標籤偵測中" : "STUB（後端未啟用 OpenCV）"}
            </span>
          )}
        </div>
        {state !== "running" ? (
          <button
            type="button"
            onClick={start}
            className="px-3 py-1.5 rounded-md text-xs font-semibold bg-brand-500 text-white hover:opacity-90 disabled:opacity-50 flex items-center gap-1.5"
            disabled={state === "starting"}
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
        {/* hidden capture canvas */}
        <canvas ref={canvasRef} className="hidden" />
      </div>

      <p className="text-[11px] text-ink-muted mt-2 leading-relaxed">
        Wave 1.5 骨架：ArUco 標籤偵測 + V-Agent 視覺評核
        目前後端為 stub 模式（顯示 STUB 標籤即為未啟用 OpenCV／V-Agent）。
        正式版需在後端安裝 <code className="px-1 bg-bg-muted rounded">opencv-python</code>
        並開啟 V-Agent。
      </p>
    </div>
  );
}
