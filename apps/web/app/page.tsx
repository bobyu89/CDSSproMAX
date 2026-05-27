import Link from "next/link";
import { HealthBadge } from "@/components/HealthBadge";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-8 px-6 py-16">
      <header className="space-y-3">
        <h1 className="text-3xl font-bold tracking-tight">TICDSS</h1>
        <p className="text-slate-600">
          Technology-Integrated Clinical Decision Support System — DUAT five-agent OSCE
          assessment for nurse practitioners.
        </p>
        <div>
          <Link
            href="/sessions"
            className="inline-flex items-center rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-slate-700"
          >
            進入系統 →
          </Link>
        </div>
      </header>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">後端狀態</h2>
        <p className="mt-2 text-sm text-slate-500">
          目前指向 <code className="rounded bg-slate-100 px-1 py-0.5">
            {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001"}
          </code>
        </p>
        <div className="mt-4">
          <HealthBadge />
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Wave 1 進度</h2>
        <ul className="mt-3 space-y-1 text-sm text-slate-600">
          <li>✅ Step 1-6 骨架（DB / Agent shells / Arbiter）</li>
          <li>✅ Step 7 Langfuse + Audit Log</li>
          <li>🚧 Step 8 前端骨架（你現在看到的這頁）</li>
          <li>⏳ Step 9 shared-types</li>
          <li>⏳ Step 10 從舊專案匯入 cases</li>
          <li>⏳ Step 11 Breeze ASR 服務</li>
          <li>⏳ Step 12 真接 LLM (E-Agent 先)</li>
        </ul>
      </section>
    </main>
  );
}
