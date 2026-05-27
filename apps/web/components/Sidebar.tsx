"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import {
  Home,
  Stethoscope,
  Timer,
  Clock,
  Shield,
  HelpCircle,
  LogOut,
  Menu,
  X,
} from "lucide-react";
import { useAuthStore } from "@/lib/authStore";

interface NavItem {
  to: string;
  label: string;
  Icon: typeof Home;
}

const PARTICIPANT_NAV: NavItem[] = [
  { to: "/home", label: "首頁", Icon: Home },
  { to: "/practice", label: "練習模式", Icon: Stethoscope },
  { to: "/osce", label: "OSCE 模式", Icon: Timer },
  { to: "/history", label: "歷史記錄", Icon: Clock },
];

const ADMIN_EXTRA_NAV: NavItem[] = [
  { to: "/admin/calibration", label: "標籤校準", Icon: Shield },
];

const ADMIN_NAV: NavItem[] = [
  { to: "/admin", label: "管理後台", Icon: Shield },
];

export function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const logout = useAuthStore((s) => s.logout);
  const role = useAuthStore((s) => s.role);
  const participantCode = useAuthStore((s) => s.participantCode);
  const navItems =
    role === "admin" ? [...ADMIN_NAV, ...ADMIN_EXTRA_NAV] : PARTICIPANT_NAV;

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <>
      {/* Mobile hamburger trigger (top-left, visible only on mobile) */}
      <button
        onClick={() => setOpen(true)}
        className="md:hidden fixed top-3 left-3 z-50 p-2 rounded-md text-ink-soft hover:bg-bg-muted bg-white/80 backdrop-blur shadow-sm"
        aria-label="開啟選單"
      >
        <Menu size={18} />
      </button>

      {/* Mobile backdrop */}
      {open && (
        <div
          className="fixed inset-0 bg-black/40 z-30 md:hidden"
          onClick={() => setOpen(false)}
          aria-hidden
        />
      )}

      <aside
        className={`fixed left-0 top-0 h-full w-64 flex flex-col z-40 transition-transform duration-200
          ${open ? "translate-x-0" : "-translate-x-full"} md:translate-x-0 bg-bg-surface`}
      >
        {/* Brand */}
        <div className="px-6 py-6 border-b border-subtle flex items-center justify-between">
          <div>
            <h1 className="font-bold text-base text-brand-600">
              TICDSS 訓練系統
            </h1>
            <p className="text-[10px] uppercase tracking-widest text-ink-muted font-semibold mt-0.5">
              臨床推理決策支援
            </p>
          </div>
          <button
            onClick={() => setOpen(false)}
            className="md:hidden p-1 rounded text-ink-soft hover:bg-bg-muted"
            aria-label="關閉選單"
          >
            <X size={18} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const active = pathname === item.to || pathname?.startsWith(item.to + "/");
            return (
              <Link
                key={item.to}
                href={item.to}
                onClick={() => setOpen(false)}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all
                  ${
                    active
                      ? "bg-white text-brand-500 shadow-sm font-semibold"
                      : "text-ink-soft hover:text-brand-500 hover:bg-bg-muted"
                  }`}
              >
                <item.Icon size={18} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Bottom */}
        <div className="px-4 py-5 border-t border-subtle space-y-1">
          {participantCode && (
            <div className="px-4 py-2 mb-2">
              <p className="text-[10px] text-ink-muted uppercase tracking-widest font-semibold">
                操作者
              </p>
              <p className="text-sm font-semibold text-ink mt-0.5">
                {participantCode}
              </p>
            </div>
          )}
          <button className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium text-ink-soft hover:text-brand-500 hover:bg-bg-muted transition-all text-left">
            <HelpCircle size={18} />
            <span>使用說明</span>
          </button>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium text-ink-soft hover:text-brand-500 hover:bg-bg-muted transition-all text-left"
          >
            <LogOut size={18} />
            <span>登出</span>
          </button>
        </div>
      </aside>
    </>
  );
}

export function TopBar() {
  return (
    <header
      className="fixed top-0 right-0 z-30 flex items-center justify-end px-4 sm:px-6 lg:px-8 h-14 left-0 md:left-64"
      style={{
        background: "rgba(253,251,249,0.80)",
        backdropFilter: "blur(16px)",
        borderBottom: "1px solid rgba(215,204,200,0.4)",
      }}
    >
      <div className="flex items-center gap-2 text-ink-muted text-xs">
        <span>TICDSS 臨床推理訓練系統</span>
      </div>
    </header>
  );
}

export function Footer() {
  return (
    <footer
      className="py-5 px-8 text-center"
      style={{ borderTop: "1px solid rgba(215,204,200,0.3)" }}
    >
      <p className="text-xs text-ink-muted leading-relaxed">
        本系統採用 AI 技術輔助生成臨床情境，僅供學術研究與教育訓練使用。
        <br />
        所有內容不得作為實際臨床診斷、治療或醫療決策之依據。
      </p>
    </footer>
  );
}
