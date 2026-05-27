// Pure helper: build an iCalendar (.ics) string from spaced-repetition items.
import type { SpacedRepetitionItem } from "@ticdss/shared-types";

function pad(n: number): string {
  return n < 10 ? `0${n}` : String(n);
}

function toIcsDate(yyyymmdd: string): string {
  // input "2026-05-29" → "20260529"
  return yyyymmdd.replace(/-/g, "");
}

function fold(line: string): string {
  // RFC5545 line folding at 75 chars
  if (line.length <= 75) return line;
  const parts: string[] = [];
  let i = 0;
  while (i < line.length) {
    parts.push((i === 0 ? "" : " ") + line.slice(i, i + 73));
    i += 73;
  }
  return parts.join("\r\n");
}

export function buildSpacedRepetitionIcs(
  items: SpacedRepetitionItem[],
  caseTitle: string,
): string {
  const now = new Date();
  const stamp =
    now.getUTCFullYear().toString() +
    pad(now.getUTCMonth() + 1) +
    pad(now.getUTCDate()) +
    "T" +
    pad(now.getUTCHours()) +
    pad(now.getUTCMinutes()) +
    pad(now.getUTCSeconds()) +
    "Z";

  const lines: string[] = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//TICDSS//Handout Spaced Repetition//ZH",
    "CALSCALE:GREGORIAN",
  ];

  items.forEach((item) => {
    item.reviewDates.forEach((d, idx) => {
      const date = toIcsDate(d);
      const uid = `${item.id}-${idx}@ticdss`;
      lines.push("BEGIN:VEVENT");
      lines.push(`UID:${uid}`);
      lines.push(`DTSTAMP:${stamp}`);
      lines.push(`DTSTART;VALUE=DATE:${date}`);
      lines.push(fold(`SUMMARY:TICDSS 複習 — ${item.dimension}`));
      lines.push(
        fold(
          `DESCRIPTION:案例：${caseTitle}\\n弱項：${item.dimension}\\n${item.rationale}`,
        ),
      );
      lines.push("END:VEVENT");
    });
  });

  lines.push("END:VCALENDAR");
  return lines.join("\r\n");
}

export function downloadIcs(filename: string, content: string): void {
  if (typeof window === "undefined") return;
  const blob = new Blob([content], { type: "text/calendar;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
