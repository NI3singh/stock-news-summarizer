import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Pin the workspace root to this app. A stray package-lock.json exists in the
  // user's home dir, so Next would otherwise infer the wrong root.
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;
