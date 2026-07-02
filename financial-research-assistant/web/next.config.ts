import type { NextConfig } from "next";

const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      { source: "/chat", destination: `${BACKEND_ORIGIN}/chat` },
      { source: "/research", destination: `${BACKEND_ORIGIN}/research` },
      { source: "/research/:path*", destination: `${BACKEND_ORIGIN}/research/:path*` },
    ];
  },
};

export default nextConfig;
