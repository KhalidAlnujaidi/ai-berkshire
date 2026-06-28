import type { MetadataRoute } from "next";

const BASE_URL = "https://mizan-invest.com";

export default function sitemap(): MetadataRoute.Sitemap {
  const locales = ["ar", "en"];
  const routes = [
    "",
    "/compare",
    "/portfolio",
    "/watchlist",
    "/learn",
    "/about",
    "/contact",
    "/privacy",
    "/terms",
    "/disclaimer",
  ];

  const entries: MetadataRoute.Sitemap = [];

  for (const locale of locales) {
    for (const route of routes) {
      entries.push({
        url: `${BASE_URL}/${locale}${route}`,
        lastModified: new Date(),
        changeFrequency: route === "" ? "daily" : "weekly",
        priority: route === "" ? 1.0 : 0.8,
        alternates: {
          languages: {
            ar: `${BASE_URL}/ar${route}`,
            en: `${BASE_URL}/en${route}`,
          },
        },
      });
    }
  }

  return entries;
}
