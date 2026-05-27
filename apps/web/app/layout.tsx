import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/AppShell";

export const metadata: Metadata = {
  title: "TICDSS 臨床推理訓練系統",
  description:
    "Technology-Integrated CDSS — multi-agent OSCE assessment for nurse practitioners",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-TW">
      <body className="bg-bg text-ink antialiased min-h-screen">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
