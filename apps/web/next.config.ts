import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001",
    NEXT_PUBLIC_ASR_URL: process.env.NEXT_PUBLIC_ASR_URL ?? "http://localhost:8002",
  },
};

export default nextConfig;
