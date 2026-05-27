"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Loader2 } from "lucide-react";
import { toast } from "sonner";
import {
  ApiError,
  createParticipant,
  type AdminParticipant,
} from "@/lib/api";

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: (p: AdminParticipant) => void;
}

type Role = "student" | "teacher" | "admin";

const ROLE_OPTIONS: { value: Role; label: string }[] = [
  { value: "student", label: "學員" },
  { value: "teacher", label: "教師" },
  { value: "admin", label: "管理員" },
];

export function AddParticipantModal({ open, onClose, onCreated }: Props) {
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [role, setRole] = useState<Role>("student");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const firstFieldRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      // Reset state on open
      setCode("");
      setName("");
      setRole("student");
      setPassword("");
      setEmail("");
      setErr(null);
      // Focus first input
      setTimeout(() => firstFieldRef.current?.focus(), 80);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    if (!code.trim() || !name.trim() || !password) {
      setErr("請填寫代碼、姓名與密碼");
      return;
    }
    if (password.length < 8) {
      setErr("密碼至少需 8 個字元");
      return;
    }
    setSubmitting(true);
    try {
      const created = await createParticipant({
        code: code.trim().toUpperCase(),
        name: name.trim(),
        role,
        password,
        email: email.trim() || undefined,
      });
      toast.success(`已建立 ${created.code}`);
      onCreated(created);
      onClose();
    } catch (e2) {
      if (e2 instanceof ApiError && e2.status === 409) {
        setErr(`代碼 ${code.trim().toUpperCase()} 已存在`);
      } else {
        const msg = e2 instanceof Error ? e2.message : "建立失敗";
        setErr(msg);
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
        >
          <div
            className="absolute inset-0 bg-ink/40"
            onClick={onClose}
            aria-hidden="true"
          />
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-labelledby="add-participant-title"
            initial={{ opacity: 0, y: 12, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 6, scale: 0.98 }}
            transition={{ duration: 0.2 }}
            className="relative w-full max-w-md rounded-xl bg-white shadow-xl border border-brand-100"
          >
            <div className="flex items-start justify-between px-6 pt-6 pb-2">
              <h3
                id="add-participant-title"
                className="text-lg font-extrabold text-ink"
              >
                新增參與者
              </h3>
              <button
                type="button"
                onClick={onClose}
                aria-label="關閉"
                className="p-1 rounded text-ink-muted hover:text-ink hover:bg-bg-surface"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="px-6 pb-6 pt-2 space-y-4">
              <div>
                <label
                  htmlFor="ap-code"
                  className="block text-[11px] uppercase tracking-widest font-bold text-ink-muted mb-1.5"
                >
                  參與者代碼
                </label>
                <input
                  id="ap-code"
                  ref={firstFieldRef}
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value.toUpperCase())}
                  autoCapitalize="characters"
                  autoComplete="off"
                  placeholder="例如：P006"
                  className="w-full px-3 py-2 rounded-lg text-sm bg-bg-surface focus:outline-none focus:ring-2 focus:ring-brand-500/30 border border-faint"
                />
              </div>

              <div>
                <label
                  htmlFor="ap-name"
                  className="block text-[11px] uppercase tracking-widest font-bold text-ink-muted mb-1.5"
                >
                  姓名
                </label>
                <input
                  id="ap-name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg text-sm bg-bg-surface focus:outline-none focus:ring-2 focus:ring-brand-500/30 border border-faint"
                />
              </div>

              <div>
                <label
                  htmlFor="ap-role"
                  className="block text-[11px] uppercase tracking-widest font-bold text-ink-muted mb-1.5"
                >
                  角色
                </label>
                <select
                  id="ap-role"
                  value={role}
                  onChange={(e) => setRole(e.target.value as Role)}
                  className="w-full px-3 py-2 rounded-lg text-sm bg-bg-surface focus:outline-none focus:ring-2 focus:ring-brand-500/30 border border-faint"
                >
                  {ROLE_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label
                  htmlFor="ap-pw"
                  className="block text-[11px] uppercase tracking-widest font-bold text-ink-muted mb-1.5"
                >
                  密碼（至少 8 字元）
                </label>
                <input
                  id="ap-pw"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="new-password"
                  className="w-full px-3 py-2 rounded-lg text-sm bg-bg-surface focus:outline-none focus:ring-2 focus:ring-brand-500/30 border border-faint"
                />
              </div>

              <div>
                <label
                  htmlFor="ap-email"
                  className="block text-[11px] uppercase tracking-widest font-bold text-ink-muted mb-1.5"
                >
                  Email（選填）
                </label>
                <input
                  id="ap-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="off"
                  className="w-full px-3 py-2 rounded-lg text-sm bg-bg-surface focus:outline-none focus:ring-2 focus:ring-brand-500/30 border border-faint"
                />
              </div>

              {err && (
                <div
                  role="alert"
                  className="text-xs text-danger bg-danger-soft rounded-md px-3 py-2"
                >
                  {err}
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={submitting}
                  className="px-4 py-2 rounded-lg text-sm font-semibold text-ink bg-bg-surface hover:bg-bg-muted disabled:opacity-50"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-lg text-sm font-semibold text-white bg-brand-500 hover:opacity-90 active:scale-[0.98] disabled:opacity-60 inline-flex items-center gap-1.5"
                >
                  {submitting && <Loader2 size={14} className="animate-spin" />}
                  建立
                </button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
