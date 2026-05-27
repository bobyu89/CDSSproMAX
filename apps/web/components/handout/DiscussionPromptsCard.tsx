"use client";

import { useEffect, useState } from "react";
import { MessageCircleQuestion, Check } from "lucide-react";
import type { DiscussionPrompt } from "@ticdss/shared-types";

interface Props {
  sessionId: string;
  prompts: DiscussionPrompt[];
}

export function DiscussionPromptsCard({ sessionId, prompts }: Props) {
  const storageKey = `ticdss:discussion-asked:${sessionId}`;
  const [asked, setAsked] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const raw = window.localStorage.getItem(storageKey);
      if (raw) setAsked(new Set(JSON.parse(raw) as string[]));
    } catch {
      // ignore
    }
  }, [storageKey]);

  const toggle = (id: string) => {
    setAsked((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      if (typeof window !== "undefined") {
        window.localStorage.setItem(storageKey, JSON.stringify(Array.from(next)));
      }
      return next;
    });
  };

  return (
    <section className="bg-white border border-subtle rounded-xl p-6 shadow-sm">
      <h2 className="text-lg font-bold text-ink mb-1 flex items-center gap-2">
        <MessageCircleQuestion size={18} className="text-brand-500" /> 督導討論題目
      </h2>
      <p className="text-xs text-ink-muted mb-4">
        建議帶到下次 debrief 與督導討論的問題；可標記為已詢問。
      </p>

      <ol className="space-y-3">
        {prompts.map((p, i) => {
          const isAsked = asked.has(p.id);
          return (
            <li
              key={p.id}
              className={
                "rounded-lg p-4 border transition-colors " +
                (isAsked
                  ? "bg-emerald-50 border-emerald-200"
                  : "bg-bg-surface border-faint")
              }
            >
              <div className="flex items-start gap-3">
                <button
                  type="button"
                  onClick={() => toggle(p.id)}
                  aria-label={isAsked ? "標記為未詢問" : "標記為已詢問"}
                  className={
                    "mt-0.5 w-5 h-5 rounded border flex items-center justify-center flex-shrink-0 transition-colors " +
                    (isAsked
                      ? "bg-emerald-500 border-emerald-500 text-white"
                      : "bg-white border-brand-100 hover:border-brand-500")
                  }
                >
                  {isAsked && <Check size={12} />}
                </button>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-ink mb-1">
                    Q{i + 1}. {p.question}
                  </p>
                  <p className="text-xs text-ink-muted leading-relaxed">
                    為何問：{p.why}
                  </p>
                </div>
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

export default DiscussionPromptsCard;
