"use client";

import { useCallback, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Camera as CameraIcon,
  CheckCircle2,
  Loader2,
  Mic,
  StopCircle,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";
import type { AnatomyRegion, MarkerDetection, VAgentResult } from "@ticdss/shared-types";
import { runVAgent } from "@/lib/vision";
import { CameraCapture } from "@/components/vision/CameraCapture";

interface Props {
  sessionId: string;
  /** Map of PE item key → expected anatomy region. When the student
   *  starts a capture burst we use this to tell V-Agent what to check. */
  itemTargets: Record<
    string,
    { rubricItemId: string; targetAction: string; targetRegion: AnatomyRegion; label: string }
  >;
  onResult?: (key: string, result: VAgentResult) => void;
}

type CaptureState =
  | { phase: "idle" }
  | { phase: "ready"; key: string }
  | { phase: "recording"; key: string; startedAt: number }
  | { phase: "scoring"; key: string }
  | { phase: "done"; key: string; result: VAgentResult };

const KEYFRAME_INTERVAL_MS = 700;
const MAX_BURST_MS = 8000;

/**
 * Intent-First PE assist:
 *   1. Student picks a target item ("我要聽右下肺葉").
 *   2. Click "開始示範" → start collecting keyframes from CameraCapture.
 *   3. Marker tracker reports touched regions in real time.
 *   4. Click "結束示範" (or auto-stop at 8s) → POST keyframes + intent
 *      to /vision/sessions/{id}/v-agent → display verdict.
 */
export function VisionPeAssist({ sessionId, itemTargets, onResult }: Props) {
  const keyframesRef = useRef<string[]>([]);
  const lastFrameAtRef = useRef<number>(0);
  const touchedRef = useRef<AnatomyRegion[]>([]);
  const captureRef = useRef<HTMLVideoElement | null>(null);
  const captureCanvasRef = useRef<HTMLCanvasElement | null>(null);

  const [state, setState] = useState<CaptureState>({ phase: "idle" });
  const [touched, setTouched] = useState<AnatomyRegion[]>([]);
  const [intentText, setIntentText] = useState<string>("");

  const items = Object.entries(itemTargets);

  const handleDetections = useCallback(
    (_dets: MarkerDetection[]) => {
      if (state.phase !== "recording") return;
      const now = Date.now();
      // Capture a keyframe at most every KEYFRAME_INTERVAL_MS, drawn from
      // a hidden canvas we duplicate from the CameraCapture video element.
      if (now - lastFrameAtRef.current < KEYFRAME_INTERVAL_MS) return;

      // Grab the first <video> on the page that's not muted=false — the
      // CameraCapture component owns it. This avoids prop-drilling a ref.
      const video = document.querySelector<HTMLVideoElement>(
        'video[aria-label="攝影機預覽"]',
      );
      if (!video || video.videoWidth === 0) return;

      if (!captureCanvasRef.current) {
        captureCanvasRef.current = document.createElement("canvas");
      }
      const c = captureCanvasRef.current;
      c.width = video.videoWidth;
      c.height = video.videoHeight;
      const ctx = c.getContext("2d");
      if (!ctx) return;
      ctx.drawImage(video, 0, 0, c.width, c.height);
      const dataUrl = c.toDataURL("image/jpeg", 0.65);
      keyframesRef.current.push(dataUrl);
      lastFrameAtRef.current = now;

      // Auto-stop at MAX_BURST_MS
      if (now - state.startedAt >= MAX_BURST_MS) {
        void stopAndScore();
      }
    },
    [state],
  );

  const handleTouched = useCallback((regions: AnatomyRegion[]) => {
    touchedRef.current = regions;
    setTouched(regions);
  }, []);

  const stopAndScore = useCallback(async () => {
    setState((prev) =>
      prev.phase === "recording" ? { phase: "scoring", key: prev.key } : prev,
    );
    const current = state.phase === "recording" ? state : null;
    if (!current) return;

    const target = itemTargets[current.key];
    if (!target) return;

    const frames = keyframesRef.current.slice();
    const detected = touchedRef.current.slice();
    const durationS = (Date.now() - current.startedAt) / 1000;

    try {
      const result = await runVAgent(sessionId, {
        rubricItemId: target.rubricItemId,
        targetAction: target.targetAction,
        targetRegion: target.targetRegion,
        studentIntent: intentText.trim(),
        detectedRegions: detected,
        keyframesB64: frames,
        durationSeconds: durationS,
      });
      setState({ phase: "done", key: current.key, result });
      onResult?.(current.key, result);
      toast.success(
        result.actionCorrect ? `${target.label}：動作正確` : `${target.label}：再試一次`,
      );
    } catch (err) {
      toast.error("V-Agent 評核失敗");
      setState({ phase: "idle" });
    } finally {
      keyframesRef.current = [];
    }
  }, [state, itemTargets, sessionId, intentText, onResult]);

  const startBurst = useCallback((key: string) => {
    keyframesRef.current = [];
    lastFrameAtRef.current = 0;
    setState({ phase: "recording", key, startedAt: Date.now() });
  }, []);

  const resetItem = useCallback(() => {
    setState({ phase: "idle" });
    keyframesRef.current = [];
  }, []);

  return (
    <div className="space-y-4">
      <CameraCapture
        sessionId={sessionId}
        detectIntervalMs={350}
        onDetections={handleDetections}
        onTouchedRegionsChange={handleTouched}
      />

      <div className="rounded-xl border border-subtle bg-white p-4">
        <div className="flex items-center gap-2 mb-3">
          <Mic size={16} className="text-brand-500" />
          <h3 className="text-sm font-semibold text-ink">語音宣告 (Intent-First)</h3>
        </div>
        <input
          type="text"
          value={intentText}
          onChange={(e) => setIntentText(e.target.value)}
          placeholder="例：我要聽右下肺葉的呼吸音"
          className="w-full px-3 py-2 rounded-lg bg-bg-surface text-sm border-0 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
        />
        <p className="text-[11px] text-ink-muted mt-1.5">
          開始示範前先說明您要評估什麼，V-Agent 會用這段宣告對照實際動作。
          （未來會接 Breeze ASR 自動辨識）
        </p>
      </div>

      <div className="rounded-xl border border-subtle bg-white p-4">
        <h3 className="text-sm font-semibold text-ink mb-3">PE 項目示範</h3>
        <ul className="space-y-2">
          {items.map(([key, target]) => {
            const isCurrent = state.phase !== "idle" && state.phase !== "done"
              ? state.key === key
              : state.phase === "done" && state.key === key;
            const isRecording = state.phase === "recording" && state.key === key;
            const isScoring = state.phase === "scoring" && state.key === key;
            const isDone = state.phase === "done" && state.key === key;
            const result = isDone ? state.result : null;
            return (
              <li
                key={key}
                className={[
                  "flex items-center gap-3 rounded-lg p-3 transition-colors",
                  isCurrent ? "bg-brand-50 border border-brand-300" : "bg-bg-surface",
                ].join(" ")}
              >
                <div className="flex-1">
                  <p className="text-sm font-semibold text-ink">{target.label}</p>
                  <p className="text-[11px] text-ink-muted mt-0.5">
                    目標位置：<code>{target.targetRegion}</code>
                    {touched.includes(target.targetRegion) && (
                      <span className="ml-2 text-emerald-700 font-bold">● 已觸碰</span>
                    )}
                  </p>
                  {isDone && result && (
                    <div className="mt-1.5 text-[11px] flex items-center gap-2">
                      {result.actionCorrect ? (
                        <span className="text-emerald-700 font-bold flex items-center gap-1">
                          <CheckCircle2 size={12} />
                          動作正確
                        </span>
                      ) : (
                        <span className="text-rose-700 font-bold flex items-center gap-1">
                          <XCircle size={12} />
                          動作有誤
                        </span>
                      )}
                      <span className="text-ink-muted">
                        技巧 {(result.techniqueScore * 100).toFixed(0)}%
                      </span>
                      <span className="text-ink-muted">
                        {result.durationAdequate ? "時長達標" : "時長不足"}
                      </span>
                    </div>
                  )}
                </div>
                <div className="flex-shrink-0">
                  {state.phase === "idle" || (isDone && !isRecording) ? (
                    <button
                      type="button"
                      onClick={() => startBurst(key)}
                      className="px-3 py-1.5 rounded-md text-xs font-semibold bg-brand-500 text-white hover:opacity-90 flex items-center gap-1.5"
                    >
                      <CameraIcon size={12} />
                      開始示範
                    </button>
                  ) : isRecording ? (
                    <button
                      type="button"
                      onClick={() => void stopAndScore()}
                      className="px-3 py-1.5 rounded-md text-xs font-semibold bg-rose-600 text-white hover:opacity-90 flex items-center gap-1.5 animate-pulse"
                    >
                      <StopCircle size={12} />
                      結束示範
                    </button>
                  ) : isScoring ? (
                    <span className="px-3 py-1.5 rounded-md text-xs font-semibold bg-amber-50 text-amber-700 flex items-center gap-1.5">
                      <Loader2 size={12} className="animate-spin" />
                      評核中
                    </span>
                  ) : (
                    <button
                      type="button"
                      onClick={resetItem}
                      className="px-3 py-1.5 rounded-md text-xs font-semibold bg-bg-muted text-ink-soft hover:bg-brand-100"
                      disabled
                    >
                      等候中
                    </button>
                  )}
                </div>
              </li>
            );
          })}
        </ul>

        <AnimatePresence>
          {state.phase === "recording" && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mt-3 px-3 py-2 rounded-lg bg-rose-50 text-rose-700 text-xs flex items-center gap-2"
              role="status"
            >
              <span className="w-2 h-2 rounded-full bg-rose-600 animate-pulse" />
              示範中 · 已蒐集 {keyframesRef.current.length} 幀 · 最多 {MAX_BURST_MS / 1000}s
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <p className="text-[11px] text-ink-muted leading-relaxed">
        Wave 1.5 整合：攝影機 → ArUco 偵測位置 → V-Agent (Gemini Vision) 評核手法 →
        寫入 <code className="px-1 bg-bg-muted rounded">pe_observations</code>。
        若後端未連線會自動退回 stub 模式，UI 仍可走完流程。
      </p>
    </div>
  );
}
