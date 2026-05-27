"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/authStore";

/**
 * Root index — pure redirect. AppShell handles the actual hydration logic;
 * here we just nudge the router so /  becomes a sensible destination.
 */
export default function IndexPage() {
  const router = useRouter();
  const hydrated = useAuthStore((s) => s.hydrated);
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn);

  useEffect(() => {
    if (!hydrated) return;
    router.replace(isLoggedIn ? "/home" : "/login");
  }, [hydrated, isLoggedIn, router]);

  return (
    <div className="min-h-screen flex items-center justify-center text-ink-muted text-sm">
      載入中…
    </div>
  );
}
