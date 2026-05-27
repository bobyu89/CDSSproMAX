import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "@/components/Nav";

export const metadata: Metadata = {
  title: "TICDSS",
  description: "Multi-agent OSCE assessment for nurse practitioners",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-TW">
      <body className="bg-slate-50 text-slate-900 antialiased">
        <Nav />
        {children}
      </body>
    </html>
  );
}
