import Link from "next/link";
import type { Dict } from "@/i18n/ar";

interface FooterProps {
  dict: Dict;
  locale: string;
}

export default function Footer({ dict, locale }: FooterProps) {
  return (
    <footer className="bg-mizan-ink text-gray-400 pt-16 pb-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
          {/* Brand */}
          <div className="col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-mizan-green to-mizan-green-dark flex items-center justify-center">
                <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6 text-white">
                  <path
                    d="M12 3v18M5 8h14M7 8l-2 6a4 4 0 008 0L11 8M13 8l-2 6a4 4 0 008 0L17 8"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <span className="text-xl font-bold text-white font-arabic">
                {locale === "ar" ? "ميزان" : "Mizan"}
              </span>
            </div>
            <p className="text-sm text-gray-500 mb-4 font-arabic">{dict.footer.tagline}</p>
            <p className="text-xs text-gray-600 font-arabic">{dict.footer.madeIn}</p>
          </div>

          {/* Product links */}
          <div>
            <h4 className="text-sm font-semibold text-white mb-4 font-arabic">{dict.footer.product}</h4>
            <ul className="space-y-2">
              <li>
                <Link href={`/${locale}#checker`} className="text-sm hover:text-mizan-gold transition-colors font-arabic">
                  {dict.footer.productLinks.sharia}
                </Link>
              </li>
              <li>
                <Link href={`/${locale}#discover`} className="text-sm hover:text-mizan-gold transition-colors font-arabic">
                  {dict.footer.productLinks.research}
                </Link>
              </li>
              <li>
                <Link href={`/${locale}/portfolio`} className="text-sm hover:text-mizan-gold transition-colors font-arabic">
                  {dict.footer.productLinks.portfolio}
                </Link>
              </li>
              <li>
                <Link href={`/${locale}/learn`} className="text-sm hover:text-mizan-gold transition-colors font-arabic">
                  {locale === "ar" ? "مركز التعليم" : "Education Center"}
                </Link>
              </li>
              <li>
                <Link href={`/${locale}/zakat`} className="text-sm hover:text-mizan-gold transition-colors font-arabic">
                  {locale === "ar" ? "حاسبة الزكاة" : "Zakat Calculator"}
                </Link>
              </li>
              <li>
                <Link href={`/${locale}/purification`} className="text-sm hover:text-mizan-gold transition-colors font-arabic">
                  {locale === "ar" ? "حاسبة التنقية" : "Purification"}
                </Link>
              </li>
            </ul>
          </div>

          {/* Company links */}
          <div>
            <h4 className="text-sm font-semibold text-white mb-4 font-arabic">{dict.footer.company}</h4>
            <ul className="space-y-2">
              <li>
                <Link href={`/${locale}/about`} className="text-sm hover:text-mizan-gold transition-colors font-arabic">
                  {dict.footer.companyLinks.about}
                </Link>
              </li>
              <li>
                <Link href={`/${locale}/contact`} className="text-sm hover:text-mizan-gold transition-colors font-arabic">
                  {dict.footer.companyLinks.contact}
                </Link>
              </li>
              <li>
                <Link href={`/${locale}#pricing`} className="text-sm hover:text-mizan-gold transition-colors font-arabic">
                  {dict.footer.companyLinks.blog}
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal links */}
          <div>
            <h4 className="text-sm font-semibold text-white mb-4 font-arabic">{dict.footer.legal}</h4>
            <ul className="space-y-2">
              <li>
                <Link href={`/${locale}/privacy`} className="text-sm hover:text-mizan-gold transition-colors font-arabic">
                  {dict.footer.legalLinks.privacy}
                </Link>
              </li>
              <li>
                <Link href={`/${locale}/terms`} className="text-sm hover:text-mizan-gold transition-colors font-arabic">
                  {dict.footer.legalLinks.terms}
                </Link>
              </li>
              <li>
                <Link href={`/${locale}#compliance`} className="text-sm hover:text-mizan-gold transition-colors font-arabic">
                  {dict.footer.legalLinks.compliance}
                </Link>
              </li>
              <li>
                <Link href={`/${locale}/disclaimer`} className="text-sm hover:text-mizan-gold transition-colors font-arabic">
                  {dict.footer.legalLinks.disclaimer}
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="border-t border-white/10 pt-8 mb-6">
          <p className="text-xs text-gray-500 leading-relaxed font-arabic max-w-4xl">
            ⚠️ {dict.footer.disclaimer}
          </p>
        </div>

        {/* Copyright */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-gray-600 font-arabic">{dict.footer.copyright}</p>
          <div className="flex items-center gap-6">
            {/* Social icons */}
            <a href="https://x.com/mizan_invest" aria-label="X / Twitter" className="text-gray-500 hover:text-mizan-gold transition-colors">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
              </svg>
            </a>
            <a href="https://facebook.com/mizan_invest" aria-label="Facebook" className="text-gray-500 hover:text-mizan-gold transition-colors">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2.04c-5.5 0-10 4.49-10 10.02 0 5 3.66 9.15 8.44 9.9v-7H7.9v-2.9h2.54V9.85c0-2.51 1.49-3.89 3.78-3.89 1.09 0 2.23.19 2.23.19v2.47h-1.26c-1.24 0-1.63.77-1.63 1.56v1.88h2.78l-.45 2.9h-2.33v7a10 10 0 008.44-9.9c0-5.53-4.5-10.02-10-10.02z" />
              </svg>
            </a>
            <a href="https://instagram.com/mizan_invest" aria-label="Instagram" className="text-gray-500 hover:text-mizan-gold transition-colors">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2.163c3.204 0 3.584.012 4.85.07 1.366.062 2.633.334 3.608 1.31.975.975 1.248 2.242 1.31 3.608.058 1.266.069 1.646.069 4.85s-.011 3.584-.069 4.85c-.062 1.366-.335 2.633-1.31 3.608-.975.975-2.242 1.248-3.608 1.31-1.266.058-1.646.069-4.85.069s-3.584-.011-4.85-.069c-1.366-.062-2.633-.335-3.608-1.31-.975-.975-1.248-2.242-1.31-3.608C2.175 15.747 2.163 15.367 2.163 12s.012-3.584.07-4.85c.062-1.366.334-2.633 1.31-3.608.975-.975 2.242-1.248 3.608-1.31C8.416 2.175 8.796 2.163 12 2.163zm0 1.838c-3.143 0-3.51.012-4.747.068-1.022.047-1.575.217-1.944.36-.49.19-.838.418-1.205.785-.367.367-.595.715-.785 1.205-.143.369-.313.922-.36 1.944-.056 1.237-.068 1.604-.068 4.747s.012 3.51.068 4.747c.047 1.022.217 1.575.36 1.944.19.49.418.838.785 1.205.367.367.715.595 1.205.785.369.143.922.313 1.944.36 1.237.056 1.604.068 4.747.068s3.51-.012 4.747-.068c1.022-.047 1.575-.217 1.944-.36.49-.19.838-.418 1.205-.785.367-.367.595-.715.785-1.205.143-.369.313-.922.36-1.944.056-1.237.068-1.604.068-4.747s-.012-3.51-.068-4.747c-.047-1.022-.217-1.575-.36-1.944-.19-.49-.418-.838-.785-1.205-.367-.367-.715-.595-1.205-.785-.369-.143-.922-.313-1.944-.36-1.237-.056-1.604-.068-4.747-.068zM12 6.865a5.135 5.135 0 100 10.27 5.135 5.135 0 000-10.27zm0 8.468a3.333 3.333 0 110-6.666 3.333 3.333 0 010 6.666zm6.538-8.671a1.2 1.2 0 11-2.4 0 1.2 1.2 0 012.4 0z" />
              </svg>
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
