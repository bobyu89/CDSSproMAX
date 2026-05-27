"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, Mic, MicOff, RotateCcw } from "lucide-react";
import { transcribeAudio } from "@/lib/asr";

interface Props {
  /** Called when transcription completes successfully. */
  onTranscribed: (text: string) => void;
  /** Optional placeholder hint. */
  placeholder?: string;
  /** Initial value (e.g. from a previous edit). */
  initialValue?: string;
}

type Phase = "idle" | "recording" | "transcribing" | "done" | "error";

function pickMimeType(): string | undefined {
  if (typeof MediaRecorder === "undefined") return undefined;
  const candidates = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/mp4",
    "audio/ogg;codecs=opus",
  ];
  for (const m of candidates) {
    if (MediaRecorder.isTypeSupported(m)) return m;
  }
  return undefined;
}

/**
 * Hold-to-record speech-to-text widget for Intent-First declarations.
 *
 * Sends audio to Breeze ASR (apps/asr) via `transcribeAudio` and surfaces
 * the recognised text. Unlike the practice-mode RecordButton, this widget
 * does NOT append to the session transcript — it just reports the text
 * back to the parent so it can be used as the V-Agent's `student_intent`.
 */
export function IntentRecorder({
  onTranscribed,
  placeholder = "例：我要聽右下肺葉的呼吸音",
  initialValue = "",
}: Props) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [text, setText] = useState<string>(initialValue);
  const [error, setError] = useState<string | null>(null);
  const [elapsedMs, setElapsedMs] = useState(0);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startedAtRef = useRef<number>(0);

  const cleanupStream = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    recorderRef.current = null;
  }, []);

  const start = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: false,
      });
      streamRef.current = stream;
      chunksRef.current = [];
      const mimeType = pickMimeType();
      const rec = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);
      recorderRef.current = rec;
      rec.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };
      rec.start();
      startedAtRef.current = Date.now();
      setPhase("recording");
      setElapsedMs(0);
      timerRef.current = setInterval(
        () => setElapsedMs(Date.now() - startedAtRef.current),
        100,
      );
    } catch (err) {
      const msg =
        err instanceof Error
          ? err.message
          : "無法存取麥克風，請確認瀏覽器權限。";
      setError(msg);
      setPhase("error");
    }
  }, []);

  const stop = useCallback(async () => {
    const rec = recorderRef.current;
    if (!rec) return;
    const blob = await new Promise<Blob>((resolve) => {
      rec.onstop = () => {
        const type = rec.mimeType || "audio/webm";
        resolve(new Blob(chunksRef.current, { type }));
      };
      rec.stop();
    });
    cleanupStream();
    setPhase("transcribing");
    try {
      const result = await transcribeAudio(blob);
      const recognised = result.text?.trim() ?? "";
      setText(recognised);
      onTranscribed(recognised);
      setPhase("done");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "辨識失敗",
      );
      setPhase("error");
    }
  }, [cleanupStream, onTranscribed]);

  // Cleanup on unmount
  useEffect(() => cleanupStream, [cleanupStream]);

  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        <Mic size={16} className="text-brand-500" />
        <h3 className="text-sm font-semibold text-ink">語音宣告 (Intent-First)</h3>
        {phase === "recording" && (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-600 animate-pulse" />
            錄音中 {(elapsedMs / 1000).toFixed(1)}s
          </span>
        )}
        {phase === "transcribing" && (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 flex items-center gap-1.5">
            <Loader2 size={10} className="animate-spin" />
            辨識中
          </span>
        )}
        {phase === "done" && (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700">
            辨識完成
          </span>
        )}
      </div>

      <div className="flex gap-2 items-stretch">
        <input
          type="text"
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            onTranscribed(e.target.value);
          }}
          placeholder={placeholder}
          className="flex-1 px-3 py-2.5 rounded-lg bg-bg-surface text-sm border-0 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
          aria-label="語音宣告內容（可編輯）"
        />
        {phase === "idle" || phase === "done" || phase === "error" ? (
          <button
            type="button"
            onClick={start}
            className="px-3 rounded-lg text-xs font-semibold bg-brand-500 text-white hover:opacity-90 flex items-center gap-1.5 flex-shrink-0"
            aria-label="開始錄音"
          >
            <Mic size={14} />
            錄音
          </button>
        ) : phase === "recording" ? (
          <button
            type="button"
            onClick={() => void stop()}
            className="px-3 rounded-lg text-xs font-semibold bg-rose-600 text-white hover:opacity-90 flex items-center gap-1.5 flex-shrink-0"
            aria-label="停止錄音"
          >
            <MicOff size={14} />
            停止
          </button>
        ) : (
          <button
            type="button"
            disabled
            className="px-3 rounded-lg text-xs font-semibold bg-bg-muted text-ink-muted flex items-center gap-1.5 flex-shrink-0"
          >
            <Loader2 size={14} className="animate-spin" />
            辨識
          </button>
        )}
        {phase === "done" && (
          <button
            type="button"
            onClick={() => {
              setText("");
              onTranscribed("");
              setPhase("idle");
            }}
            className="px-2 rounded-lg text-xs bg-bg-muted text-ink-soft hover:bg-brand-100 flex items-center gap-1 flex-shrink-0"
            aria-label="重新錄音"
            title="清除"
          >
            <RotateCcw size={12} />
          </button>
        )}
      </div>

      {error && (
        <p
          className="text-[11px] text-danger mt-1.5"
          role="alert"
        >
          {error}
        </p>
      )}
      <p className="text-[11px] text-ink-muted mt-1.5">
        按錄音說明您要評估什麼，系統會用 Breeze ASR 自動轉成文字，
        辨識完成後可再手動微調再送出評核。
      </p>
    </div>
  );
}
