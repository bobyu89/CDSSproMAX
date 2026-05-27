"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Stethoscope,
  Clock,
  ArrowRight,
  History,
  BarChart2,
  BookOpen,
} from "lucide-react";
import { useCdssStore } from "@/lib/cdssStore";

export default function HomePage() {
  const router = useRouter();
  const reset = useCdssStore((s) => s.reset);
  const setMode = useCdssStore((s) => s.setMode);

  const handlePractice = () => {
    reset();
    setMode("practice");
    router.push("/practice");
  };

  const handleOsce = () => {
    router.push("/osce");
  };

  return (
    <div className="p-8 lg:p-12 max-w-6xl mx-auto">
      <div className="mb-12">
        <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-2">
          TICDSS 訓練系統
        </p>
        <h2 className="text-4xl font-extrabold tracking-tight text-ink mb-4">
          選擇訓練模式
        </h2>
        <p className="text-ink-muted text-base leading-relaxed max-w-xl">
          歡迎使用 TICDSS 臨床決策訓練平台。請選擇適合您當前目標的學習路徑。
        </p>
      </div>

      {/* Asymmetric 7/5 grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-12">
        {/* Practice — wider */}
        <motion.div
          className="lg:col-span-7 group cursor-pointer"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          onClick={handlePractice}
        >
          <div className="relative h-full rounded-xl overflow-hidden p-10 transition-all duration-400 hover:shadow-cta bg-white border border-subtle">
            <div
              className="absolute -top-10 -right-10 w-40 h-40 rounded-full opacity-30 group-hover:opacity-60 transition-opacity blur-3xl pointer-events-none"
              style={{ background: "#D7CCC8" }}
            />
            <div className="relative z-10 flex flex-col h-full">
              <div className="w-14 h-14 rounded-lg flex items-center justify-center mb-8 shadow-sm bg-bg-surface text-brand-500">
                <Stethoscope size={24} />
              </div>
              <h3 className="text-2xl font-bold text-ink mb-4">練習模式</h3>
              <p className="text-ink-muted text-sm leading-relaxed mb-12 max-w-sm">
                每步即時回饋，可反覆練習，適合學習與複習。在低壓力環境中精進您的臨床判斷。
                DUAT 五代理人提供逐維度的問診回饋。
              </p>
              <div className="mt-auto flex items-center gap-6">
                <button className="px-8 py-3.5 rounded-lg font-bold text-sm text-white flex items-center gap-2 transition-all hover:opacity-90 active:scale-[0.97] bg-brand-500">
                  開始練習
                  <ArrowRight size={16} />
                </button>
                <span className="text-[10px] font-bold uppercase tracking-widest text-ink-muted">
                  不計入正式成績
                </span>
              </div>
            </div>
          </div>
        </motion.div>

        {/* OSCE — narrower */}
        <motion.div
          className="lg:col-span-5 group cursor-pointer"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          onClick={handleOsce}
        >
          <div className="relative h-full rounded-xl overflow-hidden p-10 transition-all duration-400 hover:shadow-cta bg-bg-surface border border-faint">
            <div className="relative z-10 flex flex-col h-full">
              <div className="w-14 h-14 rounded-lg flex items-center justify-center mb-8 shadow-sm bg-bg-muted text-brand-600">
                <Clock size={24} />
              </div>
              <h3 className="text-2xl font-bold text-ink mb-4">OSCE 模式</h3>
              <p className="text-ink-muted text-sm leading-relaxed mb-12">
                模擬考試，計時作答，完成後才顯示回饋。測試您在真實受壓環境下的專業素養。
              </p>
              <div className="mt-auto">
                <button className="w-full px-8 py-3.5 rounded-lg font-bold text-sm text-white flex items-center justify-center gap-2 transition-all hover:opacity-90 active:scale-[0.97] shadow-sm bg-brand-600">
                  進入模擬考試
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
                    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                  </svg>
                </button>
                <p className="text-center text-[10px] text-ink-muted mt-4 uppercase tracking-[0.2em] font-bold">
                  Official Assessment
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Status cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { Icon: History, label: "上次練習", value: "點擊開始第一次練習" },
          { Icon: BarChart2, label: "OSCE 成績", value: "尚無考試記錄" },
          { Icon: BookOpen, label: "可用案例", value: "36 個內建案例" },
        ].map((item, i) => (
          <motion.div
            key={i}
            className="flex items-center gap-4 rounded-xl p-5 shadow-sm bg-white border border-faint"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 + i * 0.08 }}
          >
            <div className="p-3 rounded-lg flex-shrink-0 bg-bg-surface text-brand-500">
              <item.Icon size={20} />
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest font-bold text-ink-muted mb-0.5">
                {item.label}
              </p>
              <p className="text-sm font-semibold text-ink">{item.value}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
