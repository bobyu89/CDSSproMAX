"use client";

import { useEffect, useState } from "react";

type HealthState =
  | { status: "loading" }
  | { status: "ok"; app: string; env: string; version: string }
  | { status: "error"; message: string };

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export function HealthBadge() {
  const [state, setState] = useState<HealthState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as {
          status: string;
          app: string;
          env: string;
          version: string;
        };
        if (!cancelled) {
          setState({
            status: "ok",
            app: data.app,
            env: data.env,
            version: data.version,
          });
        }
      } catch (err) {
        if (!cancelled) {
          setState({
            status: "error",
            message: err instanceof Error ? err.message : "unknown error",
          });
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (state.status === "loading") {
    return (
      <span className="inline-flex items-center gap-2 rounded-full bg-bg-surface px-3 py-1 text-xs font-medium text-ink-soft">
        <span className="h-2 w-2 animate-pulse rounded-full bg-ink-muted" />
        檢查中…
      </span>
    );
  }

  if (state.status === "error") {
    return (
      <span className="inline-flex items-center gap-2 rounded-full bg-danger-soft px-3 py-1 text-xs font-medium text-danger">
        <span className="h-2 w-2 rounded-full bg-danger" />
        後端未回應：{state.message}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-2 rounded-full bg-brand-100 px-3 py-1 text-xs font-medium text-brand-600">
      <span className="h-2 w-2 rounded-full bg-brand-500" />
      {state.app} v{state.version} ({state.env})
    </span>
  );
}
