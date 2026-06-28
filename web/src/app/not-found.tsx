import Link from "next/link";

export default function GlobalNotFound() {
  return (
    <html lang="ar" dir="rtl">
      <body style={{ fontFamily: "system-ui, sans-serif", background: "#FAFAF7", color: "#0D1B16", margin: 0, display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
        <div style={{ textAlign: "center", padding: "2rem" }}>
          <div style={{ fontSize: "6rem", fontWeight: 700, color: "rgba(0, 108, 53, 0.1)" }}>404</div>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}>
            الصفحة غير موجودة
          </h1>
          <p style={{ color: "#4A5A52", marginBottom: "2rem" }}>
            Page not found
          </p>
          <Link
            href="/ar"
            style={{
              display: "inline-block",
              padding: "0.75rem 2rem",
              background: "#006C35",
              color: "#fff",
              textDecoration: "none",
              borderRadius: "0.5rem",
              fontWeight: 600,
            }}
          >
            العودة للرئيسية
          </Link>
        </div>
      </body>
    </html>
  );
}
