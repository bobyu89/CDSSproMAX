"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

export function Nav() {
  const pathname = usePathname();
  const router = useRouter();

  const linkClass = (href: string) => {
    const active =
      href === "/" ? pathname === "/" : pathname.startsWith(href);
    return [
      "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
      active
        ? "bg-slate-900 text-white"
        : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
    ].join(" ");
  };

  const handleLogout = () => {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("ticdss_user");
    }
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <Link href="/" className="flex items-center gap-2">
          <span className="rounded bg-slate-900 px-2 py-1 text-xs font-bold text-white">
            TICDSS
          </span>
          <span className="text-sm text-slate-500">DUAT 評量平台</span>
        </Link>
        <nav className="flex items-center gap-1">
          <Link href="/" className={linkClass("/")}>
            首頁
          </Link>
          <Link href="/sessions" className={linkClass("/sessions")}>
            Sessions
          </Link>
          <button
            type="button"
            onClick={handleLogout}
            className="ml-2 rounded-md px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-rose-50 hover:text-rose-700"
          >
            登出
          </button>
        </nav>
      </div>
    </header>
  );
}
