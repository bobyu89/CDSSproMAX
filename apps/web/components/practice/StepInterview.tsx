"use client";

import { useState, useRef, useEffect, FormEvent } from "react";
import { motion } from "framer-motion";
import { Send, Mic, ArrowRight, MessageCircle } from "lucide-react";
import { toast } from "sonner";
import { useCdssStore, type InterviewTurn } from "@/lib/cdssStore";
import { appendTranscript } from "@/lib/api";
import { RecordButton } from "@/components/RecordButton";

interface LqqDef {
  dim: string;
  label: string;
  q: string;
}

const LQQOPERA_QUESTIONS: LqqDef[] = [
  { dim: "L", label: "L — 位置", q: "請問你哪裡不舒服？是固定一個地方，還是會跑到別的地方？" },
  { dim: "Q", label: "Q — 性質", q: "可以描述一下這個感覺是什麼樣子嗎？例如悶痛、刺痛、灼熱還是壓迫感？" },
  { dim: "Q2", label: "Q — 程度", q: "如果 0 分是完全不痛、10 分是最痛，現在大約幾分？" },
  { dim: "O", label: "O — 發作", q: "什麼時候開始的？是突然發生，還是慢慢出現的？" },
  { dim: "P", label: "P — 誘發", q: "有沒有特別什麼狀況下會變嚴重？例如吃東西、運動、姿勢改變？" },
  { dim: "E", label: "E — 延伸", q: "這個不舒服有沒有傳到其他地方？例如手臂、背部或下巴？" },
  { dim: "R", label: "R — 緩解", q: "什麼狀況下會比較舒服？休息、吃藥、改變姿勢有幫助嗎？" },
  { dim: "A", label: "A — 伴隨", q: "除了這個不舒服之外，還有沒有其他症狀？例如冒汗、噁心、喘不過氣？" },
];

function simulatePatientResponse(dim: string, scenario: string | null): string {
  // Very lightweight content router. For Wave 1 the Dialog Agent isn't online,
  // so we just produce plausible Chinese responses keyed by dimension.
  const s = (scenario ?? "").toLowerCase();
  const isChest = s.includes("胸") || s.includes("chest") || s.includes("冠心");
  const isAbdomen = s.includes("腹") || s.includes("闌尾");
  const isUti = s.includes("解尿") || s.includes("腎盂");

  const bank: Record<string, string[]> = {
    L: isChest
      ? ["主要在胸口正中間，有時候會延伸到左手臂內側。"]
      : isAbdomen
        ? ["右下腹這邊比較明顯，按下去更痛。"]
        : isUti
          ? ["下腹部跟腰部都覺得悶悶不舒服。"]
          : ["大部分集中在這個地方，偶爾會跑到旁邊。"],
    Q: isChest
      ? ["像有人壓在胸口上，悶悶緊緊的。"]
      : isAbdomen
        ? ["一陣一陣的刺痛，會越來越嚴重。"]
        : ["有點悶悶脹脹的感覺。"],
    Q2: ["大概 6 分左右，蠻不舒服的。"],
    O: ["大約一個多小時前突然開始的。"],
    P: isChest
      ? ["剛剛爬樓梯之後就變嚴重。"]
      : ["吃完東西或是走路會更不舒服。"],
    E: isChest
      ? ["會延伸到左手臂跟下巴。"]
      : ["沒有特別傳到其他地方。"],
    R: ["休息一下會稍微好一點，但沒有完全消失。"],
    A: isChest
      ? ["有冒冷汗，覺得有點喘、想吐。"]
      : isUti
        ? ["有發燒，解尿的時候會痛。"]
        : ["有點噁心想吐。"],
  };
  const arr = bank[dim] ?? ["我再想想…大概是這樣。"];
  return arr[0];
}

function nowIso(): string {
  return new Date().toISOString();
}

export function StepInterview() {
  const sessionId = useCdssStore((s) => s.sessionId);
  const scenario = useCdssStore((s) => s.scenario);
  const turns = useCdssStore((s) => s.interviewTurns);
  const appendTurn = useCdssStore((s) => s.appendTurn);
  const setStep = useCdssStore((s) => s.setStep);

  const [askedDims, setAskedDims] = useState<Set<string>>(new Set());
  const [freeText, setFreeText] = useState("");
  const [sending, setSending] = useState(false);
  const listRef = useRef<HTMLOListElement>(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [turns.length]);

  const pushPair = async (studentText: string, dim?: string) => {
    if (!studentText.trim() || sending) return;
    setSending(true);
    const studentTurn: InterviewTurn = {
      speaker: "student",
      text: studentText.trim(),
      createdAt: nowIso(),
    };
    appendTurn(studentTurn);

    // Best-effort persistence (api.ts already falls back to mock).
    if (sessionId) {
      try {
        await appendTranscript(sessionId, {
          speaker: "student",
          text: studentTurn.text,
        });
      } catch {
        /* ignore — mock fallback */
      }
    }

    // Simulate patient reply with a small delay so the UI feels conversational.
    await new Promise((r) => setTimeout(r, 320));
    const reply = simulatePatientResponse(dim ?? "A", scenario);
    const patientTurn: InterviewTurn = {
      speaker: "patient",
      text: reply,
      createdAt: nowIso(),
    };
    appendTurn(patientTurn);

    if (sessionId) {
      try {
        await appendTranscript(sessionId, {
          speaker: "patient",
          text: reply,
        });
      } catch {
        /* ignore */
      }
    }
    setSending(false);
  };

  const handleChip = (def: LqqDef) => {
    setAskedDims((prev) => {
      const next = new Set(prev);
      next.add(def.dim);
      return next;
    });
    void pushPair(def.q, def.dim);
  };

  const handleFreeSubmit = (e: FormEvent) => {
    e.preventDefault();
    const t = freeText.trim();
    if (!t) return;
    setFreeText("");
    void pushPair(t);
  };

  const handleFinish = () => {
    if (turns.length === 0) {
      toast.error("請至少進行一輪問診後再進入下一步");
      return;
    }
    setStep("pe");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="max-w-7xl mx-auto"
    >
      <div className="mb-6">
        <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-2">
          Step 3 / 6
        </p>
        <h2 className="text-3xl font-extrabold text-ink mb-2">LQQOPERA 問診</h2>
        <p className="text-ink-muted text-sm">
          點擊下方維度即可送出結構化問句，或在自由提問框輸入您自己的問題。
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        {/* LEFT — question controls (~60%) */}
        <div className="lg:col-span-3 space-y-5">
          <div className="rounded-xl bg-white border border-brand-100 p-5">
            <div className="flex items-center gap-2 mb-4">
              <MessageCircle size={16} className="text-brand-500" />
              <p className="text-[10px] uppercase tracking-widest font-bold text-brand-600">
                LQQOPERA 八大維度
              </p>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {LQQOPERA_QUESTIONS.map((def) => {
                const asked = askedDims.has(def.dim);
                return (
                  <button
                    key={def.dim}
                    type="button"
                    onClick={() => handleChip(def)}
                    disabled={sending}
                    className={[
                      "text-left px-3 py-2.5 rounded-lg text-xs font-semibold transition-all border",
                      asked
                        ? "bg-brand-100 text-brand-700 border-brand-200"
                        : "bg-bg-surface text-ink border-transparent hover:border-brand-400 hover:bg-white",
                      sending ? "opacity-60 cursor-wait" : "",
                    ].join(" ")}
                  >
                    <span className="block text-[11px] font-bold text-brand-600 mb-0.5">
                      {def.label}
                    </span>
                    <span className="block text-[11px] text-ink-soft leading-snug line-clamp-2">
                      {def.q}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          <form
            onSubmit={handleFreeSubmit}
            className="rounded-xl bg-white border border-brand-100 p-5"
          >
            <label
              htmlFor="free-q"
              className="block text-[10px] uppercase tracking-widest font-bold text-brand-600 mb-2"
            >
              自由提問
            </label>
            <div className="flex gap-2">
              <input
                id="free-q"
                type="text"
                value={freeText}
                onChange={(e) => setFreeText(e.target.value)}
                placeholder="例如：您之前有類似症狀嗎？"
                className="flex-1 px-4 py-3 rounded-lg text-sm bg-bg-surface text-ink placeholder:text-ink-muted/60 focus:outline-none focus:ring-2 focus:ring-brand-500/30 border-0"
              />
              <button
                type="submit"
                disabled={!freeText.trim() || sending}
                className="px-4 py-3 rounded-lg text-sm font-bold text-white flex items-center gap-1.5 transition-all hover:opacity-90 active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed bg-brand-500"
              >
                <Send size={14} />
                送出
              </button>
            </div>
          </form>

          {sessionId && (
            <div className="rounded-xl bg-bg-surface border border-brand-100 p-5">
              <div className="flex items-center gap-2 mb-3">
                <Mic size={14} className="text-brand-500" />
                <p className="text-[10px] uppercase tracking-widest font-bold text-brand-600">
                  語音問診
                </p>
              </div>
              <RecordButton
                sessionId={sessionId}
                onAppended={(t) => {
                  // Mirror into store + trigger simulated patient reply.
                  appendTurn({
                    speaker: "student",
                    text: t.text,
                    createdAt: t.createdAt,
                  });
                  setTimeout(() => {
                    appendTurn({
                      speaker: "patient",
                      text: simulatePatientResponse("A", scenario),
                      createdAt: nowIso(),
                    });
                  }, 320);
                }}
              />
            </div>
          )}
        </div>

        {/* RIGHT — transcript (~40%) */}
        <div className="lg:col-span-2">
          <div className="rounded-xl bg-white border border-brand-100 p-4 sticky top-20">
            <p className="text-[10px] uppercase tracking-widest font-bold text-brand-600 mb-3 px-1">
              對話紀錄（{turns.length}）
            </p>
            {turns.length === 0 ? (
              <div className="rounded-lg border border-dashed border-brand-200 bg-bg-surface p-8 text-center text-sm text-ink-muted">
                點擊左側維度開始問診
              </div>
            ) : (
              <ol
                ref={listRef}
                className="flex max-h-[28rem] flex-col gap-2 overflow-y-auto pr-1"
              >
                {turns.map((t, idx) => {
                  const isStudent = t.speaker === "student";
                  return (
                    <li
                      key={idx}
                      className={`flex flex-col ${isStudent ? "items-start" : "items-end"}`}
                    >
                      <div
                        className={[
                          "max-w-[90%] rounded-lg px-3 py-2 text-sm border-l-4 shadow-sm",
                          isStudent
                            ? "bg-bg-surface border-brand-500 text-ink"
                            : "bg-white border-brand-200 text-ink",
                        ].join(" ")}
                      >
                        <div className="text-[10px] font-bold uppercase tracking-widest text-ink-muted mb-1">
                          {isStudent ? "學員" : "病人"}
                        </div>
                        <p className="whitespace-pre-wrap leading-relaxed">
                          {t.text}
                        </p>
                      </div>
                    </li>
                  );
                })}
              </ol>
            )}
          </div>
        </div>
      </div>

      <div className="mt-8 flex justify-end">
        <button
          type="button"
          onClick={handleFinish}
          className="px-6 py-3 rounded-lg font-bold text-sm text-white flex items-center gap-2 transition-all hover:opacity-90 active:scale-[0.98] bg-brand-500"
        >
          完成問診 → 身體評估
          <ArrowRight size={16} />
        </button>
      </div>
    </motion.div>
  );
}

export default StepInterview;
