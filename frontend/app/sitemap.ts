import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://heillon-legal-ui.vercel.app";
  const now = new Date();

  // Public pages only (private routes excluded — see robots.ts)
  const publicPaths = [
    "",
    "/docs",
    "/docs/quickstart",
    "/docs/usage",
    "/docs/architecture",
    "/docs/regulations",
    "/docs/chain-of-custody",
    "/docs/lgpd",
    "/docs/compliance",
    "/docs/expert",
    "/docs/admin",
    "/docs/faq",
    "/docs/changelog",
    "/docs/terms",
    "/docs/privacy",
    "/login",
    "/register",
  ];

  return publicPaths.map((path) => ({
    url: `${baseUrl}${path}`,
    lastModified: now,
    changeFrequency: path === "" ? "weekly" : "monthly",
    priority: path === "" ? 1.0 : path.startsWith("/docs") ? 0.8 : 0.5,
  }));
}
