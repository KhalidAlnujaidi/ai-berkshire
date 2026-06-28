import type { Dict } from "@/i18n/ar";

interface FeaturesProps {
  dict: Dict;
}

const ICONS: Record<string, string> = {
  mosque: "M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v-2M9 7a4 4 0 100 8 4 4 0 000-8zm14 14v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75M9 11h0",
  brain: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m0 0A4 4 0 1012 7a4 4 0 00-5.657-1.657zM12 11v6m0 0l-2-2m2 2l2-2",
  landmark: "M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3",
  shield: "M20.618 4.744A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.668-1.8M5.744 20.618A11.955 11.955 0 0112 18.944a11.955 11.955 0 016.256 1.8M9 12h6m-3-3v6",
};

export default function Features({ dict }: FeaturesProps) {
  return (
    <section id="features" className="py-20 md:py-28">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold text-mizan-ink mb-4 font-arabic">
            {dict.features.sectionTitle}
          </h2>
          <p className="text-lg text-mizan-slate max-w-2xl mx-auto font-arabic">
            {dict.features.sectionSubtitle}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8">
          {dict.features.items.map((feature, i) => (
            <div
              key={i}
              className="group p-8 bg-white rounded-2xl border border-gray-100 hover:border-mizan-green/30 hover:shadow-xl transition-all duration-300"
            >
              <div className="flex items-start gap-5">
                {/* Icon */}
                <div className="flex-shrink-0 w-14 h-14 rounded-xl bg-mizan-green-pale flex items-center justify-center group-hover:bg-mizan-green/20 transition-colors">
                  <svg
                    className="w-7 h-7 text-mizan-green"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="1.5"
                      d={ICONS[feature.icon]}
                    />
                  </svg>
                </div>

                {/* Text */}
                <div>
                  <h3 className="text-xl font-bold text-mizan-ink mb-2 font-arabic">
                    {feature.title}
                  </h3>
                  <p className="text-mizan-slate leading-relaxed font-arabic">
                    {feature.description}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
