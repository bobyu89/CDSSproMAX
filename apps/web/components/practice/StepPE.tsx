"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Activity, Sparkles } from "lucide-react";
import type { AnatomyRegion, VAgentResult } from "@ticdss/shared-types";
import { useCdssStore } from "@/lib/cdssStore";
import { VisionPeAssist } from "./VisionPeAssist";

interface PeItem {
  key: string;
  label: string;
  expected: string;
  /** Wave 1.5 — anatomy region for ArUco + V-Agent (optional; some PE
   *  items like GCS don't have a single body marker). */
  targetRegion?: AnatomyRegion;
  /** Action the V-Agent should expect (auscultation, palpation, etc). */
  targetAction?: string;
  /** Rubric item id matching data/rubrics/pe.json — used by V-Agent. */
  rubricItemId?: string;
}

const PE_GROUPS: { title: string; items: PeItem[] }[] = [
  {
    title: "心血管",
    items: [
      {
        key: "cv.inspect",
        label: "視診（頸靜脈、水腫）",
        expected: "頸靜脈無怒張，雙下肢無凹陷性水腫",
        targetRegion: "jvp",
        targetAction: "inspection",
        rubricItemId: "pe.cardio.jvp",
      },
      {
        key: "cv.palpate",
        label: "觸診（PMI、震顫）",
        expected: "PMI 在第五肋間鎖骨中線，無震顫",
        targetRegion: "pmi",
        targetAction: "palpation",
        rubricItemId: "pe.cardio.palpation",
      },
      {
        key: "cv.auscult",
        label: "聽診（S1/S2、雜音）",
        expected: "S1 S2 規律，無明顯雜音、無 S3/S4",
        targetRegion: "pmi",
        targetAction: "auscultation",
        rubricItemId: "pe.cardio.auscultation",
      },
      { key: "cv.vitals", label: "生命徵象", expected: "BP 138/86 mmHg，HR 96 bpm 規律，SpO₂ 96%" },
    ],
  },
  {
    title: "呼吸",
    items: [
      { key: "rs.inspect", label: "視診（呼吸型態）", expected: "呼吸速率 22/min，無 retraction" },
      {
        key: "rs.percuss",
        label: "叩診",
        expected: "兩側胸壁共鳴音對稱",
        targetRegion: "right_lower_lung",
        targetAction: "percussion",
        rubricItemId: "pe.lung.percussion",
      },
      {
        key: "rs.auscult",
        label: "聽診",
        expected: "兩側肺野呼吸音清晰，無 wheezing/crackles",
        targetRegion: "right_lower_lung",
        targetAction: "auscultation",
        rubricItemId: "pe.lung.auscultation",
      },
    ],
  },
  {
    title: "腹部",
    items: [
      {
        key: "gi.inspect",
        label: "視診",
        expected: "腹部平坦，無可見蠕動或腫塊",
        targetRegion: "abdomen_ruq",
        targetAction: "inspection",
        rubricItemId: "pe.abdomen.inspection",
      },
      {
        key: "gi.auscult",
        label: "聽診（腸音）",
        expected: "腸音正常，每分鐘約 8 次",
        targetRegion: "abdomen_ruq",
        targetAction: "auscultation",
        rubricItemId: "pe.abdomen.auscultation",
      },
      {
        key: "gi.palpate",
        label: "觸診（壓痛、反彈痛）",
        expected: "右下腹輕度壓痛，無明顯反彈痛",
        targetRegion: "abdomen_rlq",
        targetAction: "palpation",
        rubricItemId: "pe.abdomen.palpation",
      },
    ],
  },
  {
    title: "神經",
    items: [
      { key: "neuro.gcs", label: "意識（GCS）", expected: "GCS E4V5M6 = 15" },
      { key: "neuro.cn", label: "腦神經檢查", expected: "腦神經 II–XII 無異常" },
      { key: "neuro.motor", label: "肌力與感覺", expected: "四肢肌力 5/5，感覺對稱" },
    ],
  },
];

export function StepPE() {
  const [selected, setSelected] = useState<string[]>([]);
  const [visionMode, setVisionMode] = useState<boolean>(false);
  const [visionResults, setVisionResults] = useState<Record<string, VAgentResult>>({});
  const setPeSelections = useCdssStore((s) => s.setPeSelections);
  const setStep = useCdssStore((s) => s.setStep);
  const sessionId = useCdssStore((s) => s.sessionId);

  const toggle = (k: string) =>
    setSelected((cur) =>
      cur.includes(k) ? cur.filter((x) => x !== k) : [...cur, k],
    );

  const allItems: PeItem[] = PE_GROUPS.flatMap((g) => g.items);
  const expectedFor = (k: string) =>
    allItems.find((i) => i.key === k)?.expected ?? "";

  // Wave 1.5 — items eligible for V-Agent assist (have a targetRegion).
  const visionTargets = useMemo(() => {
    const out: Record<
      string,
      { rubricItemId: string; targetAction: string; targetRegion: AnatomyRegion; label: string }
    > = {};
    for (const item of allItems) {
      if (
        item.targetRegion &&
        item.targetAction &&
        item.rubricItemId &&
        selected.includes(item.key)
      ) {
        out[item.key] = {
          rubricItemId: item.rubricItemId,
          targetAction: item.targetAction,
          targetRegion: item.targetRegion,
          label: item.label,
        };
      }
    }
    return out;
  }, [allItems, selected]);

  const confirm = () => {
    setPeSelections(selected);
    setStep("diagnosis");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="max-w-5xl mx-auto"
    >
      <div className="mb-8">
        <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-2">
          Step 4 / 6
        </p>
        <h2 className="text-3xl font-extrabold text-ink mb-2">
          請選擇要執行的身體評估項目
        </h2>
        <p className="text-ink-muted text-sm">
          選擇後右側會顯示模擬預期結果（練習用）。
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-8">
        {PE_GROUPS.map((g, gi) => (
          <motion.div
            key={g.title}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: gi * 0.05, duration: 0.25 }}
            className="rounded-xl bg-white border border-brand-100 p-5"
          >
            <div className="flex items-center gap-2 mb-3">
              <Activity size={14} className="text-brand-500" />
              <p className="text-[10px] uppercase tracking-widest font-bold text-brand-600">
                {g.title}
              </p>
            </div>
            <div className="space-y-2">
              {g.items.map((it) => {
                const active = selected.includes(it.key);
                return (
                  <label
                    key={it.key}
                    className={[
                      "flex items-start gap-3 p-3 rounded-lg cursor-pointer border transition-all",
                      active
                        ? "bg-brand-100 border-brand-200"
                        : "bg-bg-surface border-transparent hover:border-brand-400",
                    ].join(" ")}
                  >
                    <input
                      type="checkbox"
                      checked={active}
                      onChange={() => toggle(it.key)}
                      className="mt-0.5 accent-brand-500"
                    />
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-ink">
                        {it.label}
                      </p>
                      {active && (
                        <p className="text-xs text-ink-soft mt-1 leading-relaxed">
                          <span className="font-bold text-brand-600">
                            預期結果：
                          </span>
                          {expectedFor(it.key)}
                        </p>
                      )}
                    </div>
                  </label>
                );
              })}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Wave 1.5 vision toggle */}
      {sessionId && Object.keys(visionTargets).length > 0 && (
        <div className="mb-6 rounded-xl border border-brand-300 bg-brand-50 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles size={16} className="text-brand-600" />
              <p className="text-sm font-semibold text-ink">
                啟用攝影機評估 (Wave 1.5)
              </p>
            </div>
            <button
              type="button"
              onClick={() => setVisionMode((v) => !v)}
              className={[
                "px-3 py-1.5 rounded-md text-xs font-semibold transition-colors",
                visionMode
                  ? "bg-brand-600 text-white"
                  : "bg-white text-brand-600 border border-brand-300",
              ].join(" ")}
            >
              {visionMode ? "已啟用" : "啟用"}
            </button>
          </div>
          <p className="text-[11px] text-ink-soft mt-2 leading-relaxed">
            選擇了 {Object.keys(visionTargets).length} 個含解剖位置的項目。
            啟用後可使用攝影機 + ArUco 標籤 + V-Agent 進行半身假人實作評估。
            未啟用則沿用練習模式的模擬結果。
          </p>
        </div>
      )}

      {visionMode && sessionId && Object.keys(visionTargets).length > 0 && (
        <div className="mb-6">
          <VisionPeAssist
            sessionId={sessionId}
            itemTargets={visionTargets}
            onResult={(key, r) =>
              setVisionResults((cur) => ({ ...cur, [key]: r }))
            }
          />
        </div>
      )}

      <div className="flex items-center justify-between">
        <p className="text-xs text-ink-muted">
          已選 <span className="font-bold text-brand-600">{selected.length}</span> 項
          {Object.keys(visionResults).length > 0 && (
            <>
              {" · 已完成攝影機評核 "}
              <span className="font-bold text-emerald-700">
                {Object.keys(visionResults).length}
              </span>
              {" 項"}
            </>
          )}
        </p>
        <button
          type="button"
          onClick={confirm}
          className="px-6 py-3 rounded-lg font-bold text-sm text-white flex items-center gap-2 transition-all hover:opacity-90 active:scale-[0.98] bg-brand-500"
        >
          進入鑑別診斷
          <ArrowRight size={16} />
        </button>
      </div>
    </motion.div>
  );
}

export default StepPE;
