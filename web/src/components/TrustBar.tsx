import Link from "next/link";

interface TrustBarProps {
  locale: string;
}

const ITEMS = [
  { ar: "معايير AAOIFI", en: "AAOIFI Standards" },
  { ar: "تداول السعودي", en: "Saudi Tadawul" },
  { ar: "رؤية 2030", en: "Vision 2030" },
  { ar: "هيئة السوق المالية", en: "Capital Market Authority" },
];

export default function TrustBar({ locale }: TrustBarProps) {
  return (
    <div className="border-y border-gray-100 bg-white/50 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <p className="text-center text-xs font-medium text-mizan-slate uppercase tracking-widest mb-5 font-arabic">
          {locale === "ar" ? "موثوق بمعايير" : "Built on standards from"}
        </p>
        <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-4 md:gap-x-14">
          {ITEMS.map((item, i) => (
            <span
              key={i}
              className="text-sm md:text-base font-semibold text-mizan-slate/70 hover:text-mizan-green transition-colors font-arabic cursor-default"
            >
              {locale === "ar" ? item.ar : item.en}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
