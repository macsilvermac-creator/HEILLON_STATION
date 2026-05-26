import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://heillon-legal-ui.vercel.app";

  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/", "/docs", "/verification"],
        disallow: [
          "/api/",
          "/dashboard",
          "/missions",
          "/diary",
          "/privacy",
          "/compliance",
          "/agent-config",
          "/normative",
          "/ingestion",
          "/m/",
        ],
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
  };
}
