import type { NextConfig } from "next";
import withPWAInit from "@ducanh2912/next-pwa";

/** Dev/proxy: browser fetches same-origin `/api/v1/*` → forwarded to FastAPI (evita CORS). */
const backendProxyTarget = (process.env.BACKEND_PROXY_TARGET || "http://127.0.0.1:8000").replace(/\/$/, "");

const withPWA = withPWAInit({
  dest: "public",
  register: true,
  disable: process.env.NODE_ENV === "development",
});

const isProd = process.env.NODE_ENV === "production";

const baseSecurityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob:",
      "font-src 'self' data:",
      "connect-src 'self' http://127.0.0.1:8000 http://localhost:8000 ws: wss:",
      "worker-src 'self'",
    ].join("; "),
  },
];

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async headers() {
    const prodOnly = isProd
      ? [{ key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" }]
      : [];

    return [
      {
        source: "/(.*)",
        headers: [...baseSecurityHeaders, ...prodOnly],
      },
    ];
  },
  async rewrites() {
    return {
      beforeFiles: [
        {
          // Redirect to the cookie-aware Route Handler proxy
          source: "/api/v1/:path*",
          destination: "/api/proxy/:path*",
        },
      ],
    };
  },
};

export default withPWA(nextConfig);
