import type { Dict } from "@/i18n/ar";

interface TrustBarProps {
  dict: Dict;
}

export default function TrustBar({ dict }: TrustBarProps) {
  const ITEMS = [
    { label: dict.trustBar.aaoifi },
    { label: dict.trustBar.tadawul },
    { label: dict.trustBar.vision2030 },
    { label: dict.trustBar.cma },
  ];

  return (
    <div className="border-y border-gray-100 bg-white/50 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <p className="text-center text-xs font-medium text-mizan-slate uppercase tracking-widest mb-5 font-arabic">
          {dict.trustBar.title}
        </p>
        <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-4 md:gap-x-14">
          {ITEMS.map((item, i) => (
            <span
              key={i}
              className="text-sm md:text-base font-semibold text-mizan-slate/70 hover:text-mizan-green transition-colors font-arabic cursor-default"
            >
              {item.label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}