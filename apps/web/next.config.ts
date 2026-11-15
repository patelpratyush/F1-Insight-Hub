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
          {
            key: "Content-Security-Policy",
            value:
              "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self' " +
              (process.env.API_BASE_URL ?? "http://localhost:8000"),
          },
        ],
      },
    ];
  },
};
export default config;
