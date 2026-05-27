"use client";

import { useState, useEffect, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Loader2,
  Stethoscope,
  ClipboardList,
  BarChart2,
  Lock,
} from "lucide-react";
import { toast } from "sonner";
import { ApiError, loginApi } from "@/lib/api";
import { useAuthStore, type UserRole } from "@/lib/authStore";

export default function LoginPage() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn);
  const role = useAuthStore((s) => s.role);

  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isLoggedIn) {
      router.replace(role === "admin" ? "/admin" : "/home");
    }
  }, [isLoggedIn, role, router]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmedCode = code.trim();
    if (!trimmedCode || !password) return;

    setLoading(true);
    setError(null);

    try {
      const data = await loginApi(trimmedCode, password);
      login({
        participantId: data.participant.id,
        participantCode: data.participant.participant_code,
        role: data.participant.role as UserRole,
        name: data.participant.name,
        token: data.token,
        expiresAt: data.expires_at,
      });
      toast.success(`歡迎，${data.participant.name}`);
      router.replace(data.participant.role === "admin" ? "/admin" : "/home");
    } catch (err: unknown) {
      let msg = "登入失敗，請稍後再試";
      if (err instanceof ApiError) {
        if (err.status === 401) msg = "帳號或密碼錯誤";
        else if (err.status === 429) msg = "登入過於頻繁，請稍後再試";
        else if (err.message) msg = err.message;
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-bg">
      <div className="hidden lg:flex flex-col justify-between w-2/5 p-16 relative overflow-hidden bg-bg-surface">
        <div
          className="absolute -top-20 -right-20 w-72 h-72 rounded-full opacity-20 pointer-events-none"
          style={{ background: "#A1887F", filter: "blur(60px)" }}
        />
        <div
          className="absolute -bottom-16 -left-16 w-56 h-56 rounded-full opacity-15 pointer-events-none"
          style={{ background: "#D7CCC8", filter: "blur(50px)" }}
        />

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-brand-500">
              <Stethoscope size={20} className="text-white" />
            </div>
            <div>
              <h1 className="font-bold text-base text-brand-600">
                TICDSS 訓練系統
              </h1>
              <p className="text-[10px] uppercase tracking-widest text-ink-muted font-semibold">
                臨床推理決策支援
              </p>
            </div>
          </div>
        </div>

        <div className="relative z-10">
          <h2 className="text-4xl font-extrabold leading-tight text-ink mb-6">
            提升您的
            <br />
            臨床推理
            <br />
            判斷力
          </h2>
          <p className="text-ink-muted leading-relaxed text-sm max-w-xs">
            專為專科護理師設計的多代理人臨床決策支援訓練平台。整合 LQQOPERA
            結構化問診、身體評估與 DUAT 多驗證評分，系統性強化您的診斷思維。
          </p>

          <div className="mt-8 space-y-3">
            {[
              { Icon: Stethoscope, text: "練習模式：即時回饋、反覆學習" },
              { Icon: ClipboardList, text: "OSCE 模擬：計時測驗、模擬真實考場" },
              { Icon: BarChart2, text: "歷史記錄：追蹤學習進步曲線" },
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-3">
                <div
                  className="w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0"
                  style={{ background: "rgba(161,136,127,0.15)", color: "#A1887F" }}
                >
                  <item.Icon size={14} />
                </div>
                <p className="text-xs text-ink-soft">{item.text}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="relative z-10 flex items-center gap-4">
          <div className="w-10 h-0.5 bg-brand-500" />
          <p className="text-xs text-ink-muted">僅供學術研究使用</p>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center px-8">
        <motion.div
          className="w-full max-w-sm"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: "easeOut" }}
        >
          <div className="flex items-center gap-3 mb-10 lg:hidden">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-brand-500">
              <Stethoscope size={20} className="text-white" />
            </div>
            <div>
              <h1 className="font-bold text-sm text-brand-600">
                TICDSS 訓練系統
              </h1>
              <p className="text-[10px] text-ink-muted">臨床推理決策支援</p>
            </div>
          </div>

          <div className="mb-8">
            <h3 className="text-2xl font-bold text-ink mb-2">歡迎登入</h3>
            <p className="text-sm text-ink-muted">
              請輸入您的參與者代碼與密碼
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="login-code"
                className="block text-[10px] font-bold uppercase tracking-widest text-ink-muted mb-2"
              >
                參與者代碼
              </label>
              <input
                id="login-code"
                type="text"
                value={code}
                onChange={(e) => {
                  setCode(e.target.value);
                  if (error) setError(null);
                }}
                placeholder="如 P001 或 ADMIN001"
                className="w-full px-4 py-3.5 text-sm rounded-lg text-ink placeholder:text-ink-muted/50 bg-bg-surface focus:outline-none focus:ring-2 focus:ring-brand-500/30 transition-all border-0"
                autoFocus
                autoComplete="username"
                autoCapitalize="characters"
              />
            </div>

            <div>
              <label
                htmlFor="login-password"
                className="block text-[10px] font-bold uppercase tracking-widest text-ink-muted mb-2 flex items-center gap-1.5"
              >
                <Lock size={10} />
                密碼
              </label>
              <input
                id="login-password"
                type="password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (error) setError(null);
                }}
                placeholder="至少 8 字元"
                className="w-full px-4 py-3.5 text-sm rounded-lg text-ink placeholder:text-ink-muted/50 bg-bg-surface focus:outline-none focus:ring-2 focus:ring-brand-500/30 transition-all border-0"
                autoComplete="current-password"
                minLength={8}
              />
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2 text-sm px-3 py-2.5 rounded-lg bg-danger-soft text-danger"
                role="alert"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="w-4 h-4 flex-shrink-0"
                >
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>{error}</span>
              </motion.div>
            )}

            <button
              type="submit"
              disabled={!code.trim() || !password || loading}
              className="w-full py-3.5 rounded-lg text-white font-semibold text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all hover:opacity-90 active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/50 focus-visible:ring-offset-2"
              style={{
                background: "linear-gradient(135deg, #A1887F 0%, #6f5a52 100%)",
              }}
            >
              {loading ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                "登入系統"
              )}
            </button>

            <div className="text-[11px] text-ink-muted text-center mt-2 leading-relaxed">
              <p>示範帳號：</p>
              <p>學員 P001 / P002 · 教師 T001 · 管理員 ADMIN001</p>
              <p className="opacity-70">密碼為 demo1234（管理員為 admin1234）</p>
            </div>
          </form>

          <p className="text-[11px] text-ink-muted text-center mt-8">
            本系統僅供學術研究使用 · TICDSS 臨床推理訓練平台
          </p>
        </motion.div>
      </div>
    </div>
  );
}
