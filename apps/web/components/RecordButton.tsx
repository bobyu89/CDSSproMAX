"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Transcript } from "@ticdss/shared-types";
import { transcribeAudio } from "@/lib/asr";
import { appendTranscript } from "@/lib/api";

type RecState = "idle" | "recording" | "transcribing" | "error";

interface Props {
  sessionId: string;
  onAppended?: (t: Transcript) => void;
}

// Pick the first MediaRecorder mimeType the browser supports. Some
// platforms (Safari iOS) lack audio/webm; fall back gracefully.
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

export function RecordButton({ sessionId, onAppended }: Props) {
  const [state, setState] = useState<RecState>("idle");
  const [elapsedMs, setElapsedMs] = useState(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const startedAtRef = useRef<number>(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const cleanupStream = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
  }, []);

  useEffect(() => () => cleanupStream(), [cleanupStream]);

  const startRecording = useCallback(async () => {
    if (state !== "idle") return;
    setErrorMsg(null);
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("瀏覽器不支援錄音功能");
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
      streamRef.current = stream;

      const mimeType = pickMimeType();
      const rec = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);
      recorderRef.current = rec;
      chunksRef.current = [];

      rec.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };

      rec.onstop = async () => {
        const mt = rec.mimeType || mimeType || "audio/webm";
        const blob = new Blob(chunksRef.current, { type: mt });
        const startedMs = startedAtRef.current;
        const endedMs = Date.now();
        cleanupStream();

        if (blob.size === 0) {
          setState("idle");
          setElapsedMs(0);
          return;
        }

        setState("transcribing");
        try {
          const asr = await transcribeAudio(blob);
          const t = await appendTranscript(sessionId, {
            speaker: "student",
            text: asr.text,
            started_ms: 0,
            ended_ms: endedMs - startedMs,
          });
          onAppended?.(t);
          setState("idle");
          setElapsedMs(0);
        } catch (err) {
          setErrorMsg(
            err instanceof Error ? err.message : "辨識失敗，請再試一次",
          );
          setState("error");
        }
      };

      startedAtRef.current = Date.now();
      rec.start();
      setState("recording");
      setElapsedMs(0);
      timerRef.current = setInterval(() => {
        setElapsedMs(Date.now() - startedAtRef.current);
      }, 100);
    } catch (err) {
      cleanupStream();
      const name = (err as { name?: string }).name;
      if (name === "NotAllowedError" || name === "SecurityError") {
        setErrorMsg(
          "麥克風權限被拒，請於瀏覽器網址列重新允許麥克風存取後再試。",
        );
      } else if (name === "NotFoundError") {
        setErrorMsg("找不到麥克風裝置，請確認硬體已連接。");
      } else {
        setErrorMsg(
          err instanceof Error ? err.message : "無法開始錄音",
        );
      }
      setState("error");
    }
  }, [state, sessionId, onAppended, cleanupStream]);

  const stopRecording = useCallback(() => {
    const rec = recorderRef.current;
    if (rec && rec.state === "recording") {
      rec.stop();
    }
  }, []);

  // Pointer handlers — pointerdown/up covers mouse + touch + pen
  // in a single set of events and avoids double-firing.
  const handleDown = (e: React.PointerEvent<HTMLButtonElement>) => {
    e.preventDefault();
    void startRecording();
  };
  const handleUp = (e: React.PointerEvent<HTMLButtonElement>) => {
    e.preventDefault();
    if (state === "recording") stopRecording();
  };

  // Keyboard accessibility: hold Space / Enter while focused.
  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    if ((e.key === " " || e.key === "Enter") && !e.repeat) {
      e.preventDefault();
      void startRecording();
    }
  };
  const handleKeyUp = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    if ((e.key === " " || e.key === "Enter") && state === "recording") {
      e.preventDefault();
      stopRecording();
    }
  };

  const isRecording = state === "recording";
  const isBusy = state === "transcribing";

  let label = "🎙 按住錄音";
  let ariaLabel = "按住以開始錄音，放開停止";
  let cls =
    "bg-brand-500 hover:bg-brand-600 active:bg-brand-700 text-white";
  if (isRecording) {
    label = `● 錄音中 ${(elapsedMs / 1000).toFixed(1)}s`;
    ariaLabel = "錄音中，放開以停止";
    cls = "bg-danger text-white animate-pulse";
  } else if (isBusy) {
    label = "⏳ 辨識中…";
    ariaLabel = "正在辨識語音";
    cls = "bg-ink-muted text-white cursor-wait";
  }

  return (
    <div className="flex flex-col items-center gap-3">
      <button
        type="button"
        aria-label={ariaLabel}
        aria-pressed={isRecording}
        aria-busy={isBusy}
        disabled={isBusy}
        onPointerDown={handleDown}
        onPointerUp={handleUp}
        onPointerLeave={(e) => {
          // If pointer slips off while pressed, stop.
          if (isRecording && e.buttons === 0) stopRecording();
        }}
        onPointerCancel={handleUp}
        onKeyDown={handleKeyDown}
        onKeyUp={handleKeyUp}
        className={`select-none rounded-full px-8 py-6 text-lg font-semibold shadow-md transition focus:outline-none focus-visible:ring-4 focus-visible:ring-brand-200 ${cls}`}
      >
        {label}
      </button>
      {errorMsg && (
        <p
          role="alert"
          className="max-w-xs text-center text-sm text-danger"
        >
          {errorMsg}
        </p>
      )}
    </div>
  );
}

export default RecordButton;
