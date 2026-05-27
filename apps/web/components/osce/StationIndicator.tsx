"use client";

interface Props {
  total: number;
  currentIdx: number; // 0-based
  withLabels?: boolean;
}

export function StationIndicator({ total, currentIdx, withLabels = true }: Props) {
  return (
    <div className="flex items-center gap-3">
      {Array.from({ length: total }).map((_, i) => {
        const state =
          i < currentIdx ? "done" : i === currentIdx ? "current" : "upcoming";
        return (
          <div key={i} className="flex items-center gap-2">
            <span
              className={[
                "w-2.5 h-2.5 rounded-full transition-colors",
                state === "current"
                  ? "bg-brand-500 ring-4 ring-brand-500/15"
                  : state === "done"
                    ? "bg-brand-200"
                    : "bg-bg-muted",
              ].join(" ")}
            />
            {withLabels && (
              <span
                className={[
                  "text-[11px] font-semibold",
                  state === "current"
                    ? "text-ink"
                    : state === "done"
                      ? "text-ink-soft"
                      : "text-ink-muted",
                ].join(" ")}
              >
                第 {i + 1} 站
              </span>
            )}
            {i < total - 1 && (
              <span className="w-4 h-[2px] rounded-full bg-bg-muted" />
            )}
          </div>
        );
      })}
    </div>
  );
}

export default StationIndicator;
