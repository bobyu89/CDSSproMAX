"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Toaster } from "sonner";
import { useAuthStore } from "@/lib/authStore";
import { Footer, Sidebar, TopBar } from "./Sidebar";

/**
 * AppShell wraps every page. It:
 *  - hydrates the auth store from sessionStorage on mount
 *  - redirects unauthenticated users to /login (except when they're already there)
 *  - hides the sidebar/topbar on the /login screen
 *  - mounts a single Toaster for the whole app
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn);
  const hydrated = useAuthStore((s) => s.hydrated);
  const hydrate = useAuthStore((s) => s.hydrate);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (!hydrated) return;
    const onLogin = pathname === "/login";
    if (!isLoggedIn && !onLogin) {
      router.replace("/login");
    } else if (isLoggedIn && onLogin) {
      router.replace("/home");
    }
  }, [hydrated, isLoggedIn, pathname, router]);

  const isLoginPage = pathname === "/login";
  const showShell = isLoggedIn && !isLoginPage;

  return (
    <div className="min-h-screen flex flex-col bg-bg">
      {showShell && <Sidebar />}
      {showShell && <TopBar />}
      <main className={`flex-1 flex flex-col ${showShell ? "md:ml-64 pt-14" : ""}`}>
        <div className="flex-1">{children}</div>
        {showShell && <Footer />}
      </main>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: "#FDFBF9",
            border: "1px solid #D7CCC8",
            color: "#4a4441",
          },
        }}
      />
    </div>
  );
}
