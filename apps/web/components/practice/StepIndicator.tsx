"use client";

import { motion } from "framer-motion";
import { Check } from "lucide-react";
import type { CdssStep } from "@/lib/cdssStore";

export interface StepDef {
  key: CdssStep;
  label: string;
}

interface Props {
  steps: StepDef[];
  current: CdssStep;
}

export function StepIndicator({ steps, current }: Props) {
  const currentIdx = steps.findIndex((s) => s.key === current);

  return (
    <ol className="flex items-center gap-1.5 overflow-x-auto py-2">
      {steps.map((s, i) => {
        const isActive = i === currentIdx;
        const isDone = i < currentIdx;
        return (
          <li key={s.key} className="flex items-center gap-1.5 shrink-0">
            <motion.div
              initial={false}
              animate={{
                scale: isActive ? 1.02 : 1,
              }}
              transition={{ duration: 0.2 }}
              className={[
                "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold transition-colors",
                isActive
                  ? "bg-brand-500 text-white shadow-sm"
                  : isDone
                    ? "bg-brand-100 text-brand-600"
                    : "bg-bg-surface text-ink-muted",
              ].join(" ")}
            >
              <span
                className={[
                  "inline-flex items-center justify-center w-4 h-4 rounded-full text-[10px] font-bold",
                  isActive
                    ? "bg-white/25 text-white"
                    : isDone
                      ? "bg-brand-500 text-white"
                      : "bg-white text-ink-muted",
                ].join(" ")}
              >
                {isDone ? <Check size={10} strokeWidth={3} /> : i + 1}
              </span>
              <span>{s.label}</span>
            </motion.div>
            {i < steps.length - 1 && (
              <span
                className={[
                  "w-3 h-[2px] rounded-full",
                  i < currentIdx ? "bg-brand-200" : "bg-bg-muted",
                ].join(" ")}
              />
            )}
          </li>
        );
      })}
    </ol>
  );
}

export default StepIndicator;
