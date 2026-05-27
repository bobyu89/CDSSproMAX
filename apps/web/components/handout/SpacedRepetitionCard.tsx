"use client";

import { CalendarPlus, CalendarDays } from "lucide-react";
import { toast } from "sonner";
import type { SpacedRepetitionItem } from "@ticdss/shared-types";
import { buildSpacedRepetitionIcs, downloadIcs } from "@/lib/calendar";

interface Props {
  items: SpacedRepetitionItem[];
  caseTitle: string;
}

function formatDate(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("zh-TW", { month: "short", day: "numeric" });
}

export function SpacedRepetitionCard({ items, caseTitle }: Props) {
  const handleAddCalendar = () => {
    if (items.length === 0) {
      toast.error("無複習排程可匯出");
      return;
    }
    const ics = buildSpacedRepetitionIcs(items, caseTitle);
    downloadIcs("ticdss-spaced-repetition.ics", ics);
    toast.success("已下載 .ics 行事曆檔案");
  };

  return (
    <section className="bg-white border border-subtle rounded-xl p-6 shadow-sm">
      <div className="flex items-start justify-between mb-1">
        <h2 className="text-lg font-bold text-ink flex items-center gap-2">
          <CalendarDays size={18} className="text-brand-500" /> 間隔重複排程
        </h2>
        <button
          type="button"
          onClick={handleAddCalendar}
          className="print:hidden px-3 py-1.5 rounded-md text-xs font-semibold bg-brand-500 text-white hover:opacity-90 flex items-center gap-1.5"
        >
          <CalendarPlus size={12} /> 加入行事曆
        </button>
      </div>
      <p className="text-xs text-ink-muted mb-5">
        依 Ebbinghaus 遺忘曲線排定四次複習提醒（1 天 / 5 天 / 14 天 / 30 天）。
      </p>

      <div className="space-y-4">
        {items.map((item) => (
          <div key={item.id} className="bg-bg-surface rounded-lg p-4">
            <p className="text-sm font-bold text-ink mb-1">{item.dimension}</p>
            <p className="text-xs text-ink-muted mb-3">{item.rationale}</p>
            <ol className="relative ml-3 border-l-2 border-brand-100 space-y-2 pt-1">
              {item.reviewDates.map((d, i) => (
                <li key={i} className="ml-4 relative">
                  <span className="absolute -left-[1.4rem] top-0.5 w-3 h-3 rounded-full bg-brand-500 border-2 border-bg-surface" />
                  <p className="text-xs text-ink-soft">
                    <span className="font-bold">第 {i + 1} 次</span> ·{" "}
                    {formatDate(d)}
                  </p>
                </li>
              ))}
            </ol>
          </div>
        ))}
      </div>
    </section>
  );
}

export default SpacedRepetitionCard;
