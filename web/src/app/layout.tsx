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
      </head>
      <body className={`${cairo.variable} ${inter.variable} ${amiri.variable} antialiased`}>
        {children}
      </body>
    </html>
  );
}
