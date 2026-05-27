"use client";

import { useState } from "react";
import { ChevronDown, BookOpen } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import type { StudyNoteSection } from "@ticdss/shared-types";

interface Props {
  sections: StudyNoteSection[];
}

export function StudyNotesCard({ sections }: Props) {
  const [openIds, setOpenIds] = useState<Set<string>>(
    new Set(sections.length > 0 ? [sections[0].id] : []),
  );

  const toggle = (id: string) => {
    setOpenIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <section className="bg-white border border-subtle rounded-xl p-6 shadow-sm">
      <h2 className="text-lg font-bold text-ink mb-1 flex items-center gap-2">
        <BookOpen size={18} className="text-brand-500" /> 個人化學習講義
      </h2>
      <p className="text-xs text-ink-muted mb-4">
        基於本次評分弱項自動生成的學習要點，附參考文獻。
      </p>

      <div className="space-y-2">
        {sections.map((s) => {
          const open = openIds.has(s.id);
          return (
            <div
              key={s.id}
              className="border border-faint rounded-lg overflow-hidden"
            >
              <button
                type="button"
                onClick={() => toggle(s.id)}
                className="w-full flex items-center justify-between px-4 py-3 bg-bg-surface hover:bg-bg-muted text-left"
              >
                <span className="font-semibold text-sm text-ink">
                  {s.heading}
                </span>
                <ChevronDown
                  size={16}
                  className={
                    "text-ink-muted transition-transform " +
                    (open ? "rotate-180" : "")
                  }
                />
              </button>
              <AnimatePresence initial={false}>
                {open && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div className="px-4 py-4 bg-white">
                      <p className="text-sm text-ink-soft leading-relaxed whitespace-pre-line">
                        {s.body}
                      </p>
                      {s.citations.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-faint">
                          <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-1">
                            參考文獻
                          </p>
                          <ul className="text-xs text-ink-muted space-y-0.5">
                            {s.citations.map((c, i) => (
                              <li key={i}>• {c}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export default StudyNotesCard;
