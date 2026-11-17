import type { NextConfig } from "next";

const config: NextConfig = {
  transpilePackages: ["@f1/ui", "@f1/contract"],
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
          // Content-Security-Policy is set per request in src/proxy.ts (runtime API_BASE_URL).
        ],
      },
    ];
  },
};
export default config;
