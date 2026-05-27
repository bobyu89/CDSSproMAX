// Thin client for the TICDSS ASR service (Breeze-ASR-25 wrapper).
// Falls back to a stub response when the ASR service is unreachable
// so the UI can still demonstrate the recording flow.

export interface TranscribeResult {
  text: string;
  language: string;
  duration_s: number;
  model_id: string;
  stub: boolean;
}

const ASR_URL =
  process.env.NEXT_PUBLIC_ASR_URL ?? "http://localhost:8002";

const OFFLINE_FALLBACK: TranscribeResult = {
  text: "[ASR 服務未連線]",
  language: "zh",
  duration_s: 0,
  model_id: "",
  stub: true,
};

export async function transcribeAudio(
  blob: Blob,
): Promise<TranscribeResult> {
  try {
    const form = new FormData();
    // Backend expects multipart field name "file".
    form.append("file", blob, "recording.webm");

    const res = await fetch(`${ASR_URL}/transcribe`, {
      method: "POST",
      body: form,
      cache: "no-store",
    });
    if (!res.ok) return OFFLINE_FALLBACK;
    return (await res.json()) as TranscribeResult;
  } catch {
    return OFFLINE_FALLBACK;
  }
}
