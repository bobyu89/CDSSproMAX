import type { Transcript } from "@ticdss/shared-types";

interface Props {
  transcripts: Transcript[];
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString("zh-TW", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  } catch {
    return "";
  }
}

export function TranscriptList({ transcripts }: Props) {
  if (transcripts.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-brand-200 bg-white p-8 text-center text-sm text-ink-muted">
        尚無對話紀錄
      </div>
    );
  }

  return (
    <ol
      aria-label="問診對話紀錄"
      className="flex max-h-[28rem] flex-col gap-2 overflow-y-auto rounded-lg border border-brand-100 bg-white p-3"
    >
      {transcripts.map((t) => {
        const isStudent = t.speaker === "student";
        return (
          <li
            key={t.id}
            className={`flex flex-col ${isStudent ? "items-start" : "items-end"}`}
          >
            <div
              className={[
                "max-w-[85%] rounded-lg px-3 py-2 text-sm shadow-sm border-l-4",
                isStudent
                  ? "bg-bg-surface border-brand-500 text-ink"
                  : "bg-white border-brand-200 text-ink",
              ].join(" ")}
            >
              <div className="mb-1 flex items-center gap-2 text-xs font-semibold text-ink-muted">
                <span>{isStudent ? "學員" : "病人"}</span>
                <span className="text-ink-muted/70">
                  {formatTime(t.createdAt)}
                </span>
              </div>
              <p className="whitespace-pre-wrap leading-relaxed">{t.text}</p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

export default TranscriptList;
