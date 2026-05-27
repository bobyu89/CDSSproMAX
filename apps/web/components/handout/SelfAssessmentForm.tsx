"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Star, Sparkles, Send, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";
import type { SelfAssessmentResponse } from "@ticdss/shared-types";

interface Props {
  sessionId: string;
  initial: SelfAssessmentResponse | null;
  onSubmit: (payload: SelfAssessmentResponse) => Promise<void>;
}

const LIKERT_QUESTIONS: { key: keyof SelfAssessmentResponse["likert"]; label: string }[] = [
  { key: "confidence", label: "我對本次臨床判斷的信心程度" },
  { key: "clarity", label: "我表達思路與決策的清晰度" },
  { key: "empathy", label: "我對病人感受的同理與回應" },
  { key: "safety", label: "我在過程中對病人安全的注意" },
  { key: "growth", label: "我認為本次練習對未來成長的幫助" },
];

const emptyForm: SelfAssessmentResponse = {
  likert: { confidence: 3, clarity: 3, empathy: 3, safety: 3, growth: 3 },
  textGoodWhat: "",
  textGoodWhy: "",
  textNextStep: "",
};

export function SelfAssessmentForm({ sessionId, initial, onSubmit }: Props) {
  const storageKey = `ticdss:self-assessment-draft:${sessionId}`;
  const [form, setForm] = useState<SelfAssessmentResponse>(initial ?? emptyForm);
  const [submitted, setSubmitted] = useState<boolean>(initial !== null);
  const [submitting, setSubmitting] = useState(false);

  // Load draft from localStorage on mount
  useEffect(() => {
    if (initial || typeof window === "undefined") return;
    try {
      const raw = window.localStorage.getItem(storageKey);
      if (raw) setForm(JSON.parse(raw) as SelfAssessmentResponse);
    } catch {
      // ignore
    }
  }, [initial, storageKey]);

  // Auto-save draft on change
  useEffect(() => {
    if (submitted || typeof window === "undefined") return;
    window.localStorage.setItem(storageKey, JSON.stringify(form));
  }, [form, storageKey, submitted]);

  const setLikert = (key: keyof SelfAssessmentResponse["likert"], v: number) => {
    setForm((f) => ({ ...f, likert: { ...f.likert, [key]: v } }));
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await onSubmit(form);
      setSubmitted(true);
      if (typeof window !== "undefined") {
        window.localStorage.removeItem(storageKey);
      }
      toast.success("自評已送出");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "送出失敗";
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    const avg =
      Object.values(form.likert).reduce((a, b) => a + b, 0) /
      Object.values(form.likert).length;
    return (
      <section className="bg-white border border-subtle rounded-xl p-6 shadow-sm">
        <h2 className="text-lg font-bold text-ink mb-1 flex items-center gap-2">
          <Sparkles size={18} className="text-brand-500" /> 反脆弱自評
        </h2>
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-emerald-50 border border-emerald-200 rounded-lg p-5 mt-4"
        >
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle2 size={20} className="text-emerald-600" />
            <p className="text-base font-bold text-ink">感謝你完成自評</p>
          </div>
          <p className="text-sm text-ink-soft mb-3">
            Likert 平均：<span className="font-extrabold text-brand-600">{avg.toFixed(2)} / 5</span>
          </p>
          {form.textGoodWhat && (
            <div className="mt-3 pt-3 border-t border-emerald-200">
              <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-1">
                本次做得好的地方
              </p>
              <p className="text-xs text-ink-soft">{form.textGoodWhat}</p>
            </div>
          )}
          {form.textNextStep && (
            <div className="mt-3 pt-3 border-t border-emerald-200">
              <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-1">
                下次的具體行動
              </p>
              <p className="text-xs text-ink-soft">{form.textNextStep}</p>
            </div>
          )}
        </motion.div>
      </section>
    );
  }

  return (
    <section className="bg-white border border-subtle rounded-xl p-6 shadow-sm">
      <h2 className="text-lg font-bold text-ink mb-1 flex items-center gap-2">
        <Sparkles size={18} className="text-brand-500" /> 反脆弱自評
      </h2>
      <p className="text-xs text-ink-muted mb-5">
        誠實面對才能成長 — 草稿會自動儲存在瀏覽器，送出後送往伺服器。
      </p>

      <div className="space-y-4 mb-6">
        {LIKERT_QUESTIONS.map((q) => (
          <div key={q.key}>
            <p className="text-sm text-ink mb-2">{q.label}</p>
            <div className="flex items-center gap-1">
              {[1, 2, 3, 4, 5].map((n) => {
                const filled = form.likert[q.key] >= n;
                return (
                  <button
                    key={n}
                    type="button"
                    onClick={() => setLikert(q.key, n)}
                    aria-label={`${q.label} 評 ${n} 星`}
                    className="p-1"
                  >
                    <motion.span
                      animate={{ scale: filled ? 1.1 : 1 }}
                      transition={{ duration: 0.15 }}
                      style={{ display: "inline-block" }}
                    >
                      <Star
                        size={22}
                        className={
                          filled
                            ? "fill-brand-500 text-brand-500"
                            : "text-bg-muted"
                        }
                      />
                    </motion.span>
                  </button>
                );
              })}
              <span className="ml-2 text-xs font-bold text-ink-soft">
                {form.likert[q.key]} / 5
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="space-y-4 mb-6">
        <div>
          <label className="text-sm font-semibold text-ink mb-1.5 block">
            本次做得好的地方（What）
          </label>
          <textarea
            value={form.textGoodWhat}
            onChange={(e) => setForm({ ...form, textGoodWhat: e.target.value })}
            rows={2}
            className="w-full rounded-lg border border-brand-100 bg-bg-surface px-3 py-2 text-sm focus:outline-none focus:border-brand-500"
            placeholder="例如：完整問了 LQQOPERA 的 Location 與 Onset…"
          />
        </div>
        <div>
          <label className="text-sm font-semibold text-ink mb-1.5 block">
            為什麼能做到（Why）
          </label>
          <textarea
            value={form.textGoodWhy}
            onChange={(e) => setForm({ ...form, textGoodWhy: e.target.value })}
            rows={2}
            className="w-full rounded-lg border border-brand-100 bg-bg-surface px-3 py-2 text-sm focus:outline-none focus:border-brand-500"
            placeholder="例如：上週讀過急性胸痛問診清單，提前準備過…"
          />
        </div>
        <div>
          <label className="text-sm font-semibold text-ink mb-1.5 block">
            下次的具體行動（Next Step）
          </label>
          <textarea
            value={form.textNextStep}
            onChange={(e) => setForm({ ...form, textNextStep: e.target.value })}
            rows={2}
            className="w-full rounded-lg border border-brand-100 bg-bg-surface px-3 py-2 text-sm focus:outline-none focus:border-brand-500"
            placeholder="例如：下次練習一定要使用 0-10 NRS 量表詢問疼痛強度…"
          />
        </div>
      </div>

      <button
        type="button"
        onClick={handleSubmit}
        disabled={submitting}
        className="w-full px-4 py-2.5 rounded-lg bg-brand-500 text-white font-bold text-sm hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2"
      >
        <Send size={14} /> 送出自評
      </button>
    </section>
  );
}

export default SelfAssessmentForm;
