"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Heart, Wind, Soup, Brain, Bone, Eye, Droplet, ArrowRight } from "lucide-react";
import { useCdssStore } from "@/lib/cdssStore";

const SYSTEMS = [
  { key: "cardio", label: "心血管系統", Icon: Heart },
  { key: "respiratory", label: "呼吸系統", Icon: Wind },
  { key: "gi", label: "消化系統", Icon: Soup },
  { key: "neuro", label: "神經系統", Icon: Brain },
  { key: "msk", label: "肌肉骨骼", Icon: Bone },
  { key: "gu", label: "泌尿生殖", Icon: Droplet },
  { key: "ent", label: "耳鼻喉/眼", Icon: Eye },
] as const;

export function StepSystem() {
  const [selected, setSelected] = useState<string[]>([]);
  const scenario = useCdssStore((s) => s.scenario);
  const setSelectedSystem = useCdssStore((s) => s.setSelectedSystem);
  const setStep = useCdssStore((s) => s.setStep);

  const toggle = (k: string) =>
    setSelected((cur) =>
      cur.includes(k) ? cur.filter((x) => x !== k) : [...cur, k],
    );

  const confirm = () => {
    if (selected.length === 0) return;
    setSelectedSystem(selected.join(","));
    setStep("interview");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="max-w-4xl mx-auto"
    >
      <div className="mb-8">
        <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-2">
          Step 2 / 6
        </p>
        <h2 className="text-3xl font-extrabold text-ink mb-3">
          請選擇應評估的系統
        </h2>
        {scenario && (
          <div className="rounded-lg bg-bg-surface border border-brand-100 px-4 py-3 mb-4">
            <p className="text-[10px] uppercase tracking-widest font-bold text-brand-600 mb-1">
              當前主訴
            </p>
            <p className="text-sm text-ink">{scenario}</p>
          </div>
        )}
        <p className="text-ink-muted text-sm">
          可複選——選擇本次問診與身體評估的重點系統。
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mb-8">
        {SYSTEMS.map(({ key, label, Icon }, i) => {
          const active = selected.includes(key);
          return (
            <motion.button
              key={key}
              type="button"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.04 * i, duration: 0.2 }}
              onClick={() => toggle(key)}
              className={[
                "flex flex-col items-center gap-2 p-5 rounded-xl border transition-all text-sm font-semibold",
                active
                  ? "bg-brand-500 text-white border-brand-500 shadow-card"
                  : "bg-white text-ink border-brand-100 hover:border-brand-400 hover:bg-bg-surface",
              ].join(" ")}
            >
              <Icon size={22} />
              <span>{label}</span>
            </motion.button>
          );
        })}
      </div>

      <div className="flex items-center justify-between">
        <p className="text-xs text-ink-muted">
          已選 <span className="font-bold text-brand-600">{selected.length}</span> 個系統
        </p>
        <button
          type="button"
          disabled={selected.length === 0}
          onClick={confirm}
          className="px-6 py-3 rounded-lg font-bold text-sm text-white flex items-center gap-2 transition-all hover:opacity-90 active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed bg-brand-500"
        >
          進入問診階段
          <ArrowRight size={16} />
        </button>
      </div>
    </motion.div>
  );
}

export default StepSystem;
