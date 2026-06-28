import "./globals.css";

import { Cairo, Inter, Amiri } from "next/font/google";

// Arabic primary font — modern, clean, widely used in Saudi digital products
const cairo = Cairo({
  subsets: ["arabic", "latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
  variable: "--font-cairo",
  display: "swap",
});

// Latin font — for English mode and mixed-content
const inter = Inter({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-inter",
  display: "swap",
});

// Arabic display/serif — for headlines, quotes, and Quranic-style typography
const amiri = Amiri({
  subsets: ["arabic", "latin"],
  weight: ["400", "700"],
  variable: "--font-amari",
  display: "swap",
});

// JSON-LD structured data for SEO
const orgJsonLd = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "Mizan",
  alternateName: "ميزان",
  url: "https://mizan-invest.com",
  description:
    "Sharia-compliant AI investment screening platform for the Saudi market. Screen stocks using AAOIFI Standard 21.",
  foundingDate: "2025",
  areaServed: "SA",
  knowsLanguage: ["ar", "en"],
  applicationCategory: "FinanceApplication",
  slogan: "Invest with confidence, the halal way",
};

const webAppJsonLd = {
  "@context": "https://schema.org",
  "@type": "WebApplication",
  name: "Mizan",
  url: "https://mizan-invest.com",
  description:
    "AI-powered Sharia compliance screening for Saudi stocks using AAOIFI Standard 21. Free instant screening, portfolio analysis, and comparison tools.",
  applicationCategory: "BusinessApplication",
  operatingSystem: "Web",
  offers: {
    "@type": "Offer",
    price: "0",
    priceCurrency: "SAR",
    description: "Free Sharia screening with paid Pro tier at 99 SAR/month",
  },
  featureList: [
    "Sharia compliance screening (AAOIFI Standard 21)",
    "Portfolio compliance monitoring",
    "Stock comparison tools",
    "Watchlist tracking",
    "Investment education center",
    "Bilingual Arabic/English interface",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html suppressHydrationWarning>
      <head>
        <style>{`
          :root {
            --font-cairo: ${cairo.style.fontFamily};
            --font-inter: ${inter.style.fontFamily};
            --font-amari: ${amiri.style.fontFamily};
          }
        `}</style>
        <link rel="manifest" href="/site.webmanifest" />
        <meta name="theme-color" content="#006C35" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(orgJsonLd) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(webAppJsonLd) }}
        />
      </head>
      <body className={`${cairo.variable} ${inter.variable} ${amiri.variable} antialiased`}>
        {children}
      </body>
    </html>
  );
}
