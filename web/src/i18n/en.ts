import type { Dict } from "./ar";

// English translations — secondary language
// Must mirror all keys from ar.ts

export const en: Dict = {
  meta: {
    title: "Mizan | Sharia-Compliant AI Investment Platform",
    description:
      "AI-powered investment research platform with Sharia compliance screening for the Saudi market. Check your stocks now — free.",
  },

  nav: {
    features: "Features",
    shariaChecker: "Sharia Checker",
    pricing: "Pricing",
    vision2030: "Vision 2030",
    login: "Log In",
    signup: "Sign Up",
    langSwitch: "العربية",
  },

  hero: {
    badge: "AI-Powered · Sharia-Compliant",
    title: "Invest with confidence,",
    titleHighlight: "the halal way",
    subtitle:
      "Mizan is a full investment research team in your pocket. Screen any Saudi stock for Sharia compliance and get institutional-grade analysis.",
    ctaPrimary: "Check a stock — free",
    ctaSecondary: "See how it works",
    stats: {
      investors: "Live Portfolio Return (2024–2025)",
      stocks: "Stocks Screened via Tadawul",
      sharia: "Screening Standard",
      accuracy: "Assessment Languages",
    },
    statValues: {
      investors: "+146%",
      stocks: "49",
      sharia: "AAOIFI 21",
      accuracy: "Arabic + English",
    },
    statSources: {
      investors: "Source: Brokerage statement (real portfolio)",
      stocks: "Source: Tadawul data (Jun 2025)",
      sharia: "Source: AAOIFI",
      accuracy: "Source: User settings",
    },
  },

  // Track Record
  trackRecord: {
    badge: "Real Performance · Real Money",
    title: "Not Theory — Results",
    subtitle:
      "This framework is backed by real investments. +146% over two years, beating every major index.",
    year2024: "Year 2024",
    year2025: "2025 YTD",
    "beatS&P": "Beat S&P 500",
    tableTitle: "vs. Global Indices",
    colStrategy: "Strategy",
    col2024: "2024",
    col2025: "2025",
    rows: [
      { name: "Our Framework", y2024: "+69.29%", y2025: "+66.38%", highlight: true },
      { name: "S&P 500", y2024: "+23.31%", y2025: "+16.39%", highlight: false },
      { name: "Hang Seng", y2024: "+17.67%", y2025: "+27.77%", highlight: false },
      { name: "CSI 300", y2024: "+14.68%", y2025: "+17.66%", highlight: false },
      { name: "Nasdaq", y2024: "+28.64%", y2025: "+20.36%", highlight: false },
    ],
    disclaimer:
      "Past performance does not guarantee future results. Figures above verified from a real brokerage account statement.",
    sourceLabel: "Source: Brokerage account statement (verified)",
  },

  trustBar: {
    title: "Built On",
    aaoifi: "AAOIFI Standards",
    tadawul: "Saudi Tadawul",
    vision2030: "Vision 2030",
    cma: "Capital Market Authority",
  },

  checker: {
    title: "Sharia Compliance Checker",
    subtitle: "Enter a ticker number or company name for instant screening",
    placeholder: "e.g., 1120 (Al Rajhi Bank) or company name",
    button: "Screen Now",
    checking: "Screening...",
    resultCompliant: "Sharia-Compliant",
    resultNonCompliant: "Non-Compliant",
    resultOverlay: "Compliant with Overlay",
    resultPurification: "Compliant with Purification",
    sectorScreen: "Qualitative Screen (Sector)",
    ratioScreen: "Quantitative Screen (Financial Ratios)",
    verdict: "Final Verdict",
    tryExample: "Try an example:",
    examples: {
      rajhi: "Al Rajhi Bank",
      aramco: "Saudi Aramco",
      stc: "STC",
      sabic: "SABIC",
    },
    verdicts: {
      compliant: "This stock is Sharia-compliant per AAOIFI standards",
      overlay: "This stock is compliant but requires income purification",
      nonCompliant: "This stock is NOT Sharia-compliant",
    },
    warningTitle: "Purification Required",
    warningExplanation: "This stock passes the sector screen but has financial ratios that require earnings purification. Non-compliant income must be donated to charity. Consult a Sharia scholar for the exact purification ratio.",
    nonCompliantTitle: "Not Sharia-Compliant",
    nonCompliantExplanation: "This stock fails one or more AAOIFI Standard No. 21 screens. It cannot be held by Sharia-compliant portfolios. See the specific failed ratios above for details.",
    aiDisclaimer: "This screening was performed by artificial intelligence based on AAOIFI Standard No. 21. It is not a religious ruling (fatwa). Consult a qualified Sharia scholar for definitive guidance.",
  },

  // Discover — Halal Stocks Grid
  discover: {
    title: "The Halal Universe",
    subtitle: "Every stock here has already passed dual Sharia screening — browse with confidence",
    filterAll: "All Sectors",
    screened: "Screened",
    passed: "Passed",
    verifiedHalal: "Verified Halal",
    needsPurification: "Needs Purification",
    viewDetails: "View Details",
    loadingText: "Screening stocks...",
  },

  features: {
    sectionTitle: "Why Mizan?",
    sectionSubtitle: "Dual AAOIFI screening + Buffett-Munger analysis methodology",
    items: [
      {
        icon: "mosque",
        title: "Instant Sharia Screening",
        description:
          "Every stock passes a dual screen: qualitative (business activity) and quantitative (financial ratios) per AAOIFI Standard 21. No guesses — deterministic rules.",
      },
      {
        icon: "brain",
        title: "Investment Intelligence",
        description:
          "Four AI agents analyze each stock using Buffett and Munger's methodology. Deep dialectical analysis ending in a clear verdict: Pass or Fail.",
      },
      {
        icon: "landmark",
        title: "Vision 2030 Context",
        description:
          "Every analysis includes a Vision 2030 alignment score. Does the company benefit from megaprojects? Is PIF a partner? We know the answer.",
      },
      {
        icon: "shield",
        title: "Mathematical Rigor",
        description:
          "We use exact Decimal arithmetic, not floating point. Every ratio calculated to 28-digit precision. No rounding errors, no approximations.",
      },
    ],
  },

  pricing: {
    sectionTitle: "Simple, Fair Pricing",
    sectionSubtitle: "Free Sharia screening for all stocks. Pay only for deep research reports.",
    monthly: "Monthly",
    yearly: "Yearly",
    save: "Save 2 months",
    popular: "Most Popular",
    plans: [
      {
        name: "Free",
        price: "0",
        currency: "SAR",
        period: "forever",
        description: "Full Sharia screening at no cost",
        features: [
          "Unlimited Sharia screening for all stocks",
          "Basic company information",
          "Saudi financial news feed",
          "Arabic language account",
        ],
        cta: "Get Started",
        highlight: false,
      },
      {
        name: "Pro",
        price: "99",
        currency: "SAR",
        period: "/month",
        description: "Institutional research at your fingertips",
        features: [
          "Everything in Free",
          "Full investment research reports",
          "Four AI agent analysis",
          "Portfolio Sharia compliance monitoring",
          "WhatsApp & email alerts",
          "Bilingual reports (Arabic/English)",
          "Vision 2030 alignment score",
        ],
        cta: "Subscribe Now",
        highlight: true,
      },
      {
        name: "Enterprise",
        price: "Custom",
        currency: "",
        period: "",
        description: "For family offices & firms",
        features: [
          "Everything in Pro",
          "API access for integration",
          "Portfolio-wide Sharia audit",
          "White-label reports",
          "Multi-user team management",
          "Dedicated 24/7 support",
        ],
        cta: "Contact Us",
        highlight: false,
      },
    ],
  },

  vision: {
    badge: "Saudi Vision 2030",
    title: "Invest in the Kingdom's Future",
    subtitle:
      "Mizan connects every analysis to Vision 2030 — does the company benefit from megaprojects? Where is PIF deploying capital?",
    pillars: [
      {
        title: "Vibrant Society",
        description: "Entertainment, sports, culture, and lifestyle sectors",
        icon: "heart",
      },
      {
        title: "Thriving Economy",
        description: "Renewable energy, mining, industry, and tourism",
        icon: "chart",
      },
      {
        title: "Ambitious Nation",
        description: "Infrastructure, housing, and government services",
        icon: "flag",
      },
    ],
    pifTitle: "Public Investment Fund Alignment",
    pifDescription:
      "We analyse how Tadawul-listed companies connect to PIF's portfolio strategy and Vision 2030 priorities — helping you invest in the national transformation.",
    pifSource: "Source: PIF Annual Report (2024)",
    totalValue: "925B+",
    totalValueLabel: "PIF Total AUM (2024 est.)",
  },

  howItWorks: {
    title: "How Mizan Works",
    subtitle: "Enter a ticker → Sharia screen → verdict in seconds",
    steps: [
      {
        number: "1",
        title: "Enter Stock",
        description: "Type the ticker or company name in the Sharia checker",
      },
      {
        number: "2",
        title: "Screen",
        description: "Mizan analyses the stock per AAOIFI standards and financial ratios",
      },
      {
        number: "3",
        title: "Decide",
        description: "Get a clear verdict: Compliant, Non-Compliant, or Needs Purification",
      },
    ],
  },

  // CTA
  cta: {
    title: "Ready for Smarter Investing?",
    subtitle: "Thousands of investors trust Mizan — join them today",
    button: "Start Free Screening",
    note: "No credit card required · Cancel anytime",
  },

  // Footer
  footer: {
    rights: "© 2025 Mizan. All rights reserved.",
    disclaimer: "Mizan is an investment research tool and does not provide personal financial advice. Always consult a qualified financial advisor.",
    links: {
      privacy: "Privacy Policy",
      terms: "Terms of Service",
      contact: "Contact Us",
    },
  },

  // Education Center
  education: {
    heroBadge: "Education Center",
    title: "Understanding Sharia Stock Screening",
    subtitle: "A comprehensive guide to AAOIFI standards, financial ratios, and their application to the Saudi stock market",
    statTotalStocks: "Total Stocks",
    statHalalRate: "Halal Rate",
    statSectors: "Sectors",
    statStandard: "Standard",
    sectionRatios: "The Six Financial Ratios",
    sectionRatiosDesc: "These are the ratios used in quantitative screening per AAOIFI Standard 21",
    ratio1Name: "Debt-to-Assets Ratio",
    ratio1Threshold: "< 30%",
    ratio1Desc: "Total interest-bearing debt must not exceed 30% of total assets.",
    ratio2Name: "Cash-to-Assets Ratio",
    ratio2Threshold: "< 30%",
    ratio2Desc: "Cash and short-term deposits must not exceed 30% of total assets.",
    ratio3Name: "Receivables-to-Assets Ratio",
    ratio3Threshold: "< 30% (or 70%)",
    ratio3Desc: "Accounts receivable must not exceed 30% (or 70% per some interpretations) of total assets.",
    ratio4Name: "Non-Compliant Revenue Ratio",
    ratio4Threshold: "< 5%",
    ratio4Desc: "Revenue from prohibited activities must not exceed 5% of total revenue.",
    ratio5Name: "Loans-to-Market Cap Ratio",
    ratio5Threshold: "< 30%",
    ratio5Desc: "Interest-bearing loans relative to the company's average market cap must not exceed 30%.",
    ratio6Name: "Non-Compliant Investments",
    ratio6Threshold: "< 30%",
    ratio6Desc: "Investments in non-compliant instruments or companies must not exceed 30% of assets.",
    sectionQualitative: "Qualitative Screen: Permitted vs Prohibited",
    sectionQualitativeDesc: "Sector classification based on compliance of core business activity with Sharia",
    prohibitedTitle: "Prohibited Activities",
    prohibitedDesc: "Companies whose primary activity falls in these areas are rejected immediately regardless of financial ratios",
    prohibited: [
      "Conventional banks and financial institutions (riba-based)",
      "Conventional insurance companies",
      "Alcohol and tobacco production & distribution",
      "Weapons manufacturing & arms dealing",
      "Unlawful entertainment (casinos, music, explicit films)",
      "Non-halal meat and pork products",
    ],
    permittedTitle: "Permitted Activities",
    permittedDesc: "Companies in these sectors qualify for quantitative (ratio-based) screening",
    permitted: [
      "Islamic banks and financial institutions",
      "Energy (oil, gas, petrochemicals)",
      "Telecommunications and IT",
      "Industry and manufacturing",
      "Healthcare and pharmaceuticals",
      "Real estate and construction",
      "Transportation and logistics",
      "Agriculture and halal food",
    ],
    sectionPurification: "Income Purification",
    sectionPurificationDesc: "When a stock is compliant but has a negligible portion of non-compliant revenue",
    purifStep1: "Calculate the percentage of non-compliant revenue",
    purifStep2: "Calculate the profit amount attributable to this revenue (dividend share)",
    purifStep3: "Donate this amount to charity (without intention of reward)",
    purifStep4: "Record the donation in your records — not typically tax-deductible",
    sectionFaq: "Frequently Asked Questions",
    faq: [
      {
        q: "What is AAOIFI Standard 21?",
        a: "It is Sharia Standard No. 21 issued by the Accounting and Auditing Organization for Islamic Financial Institutions, governing equity investment guidelines.",
      },
      {
        q: "Is the screening completely free?",
        a: "Yes, Sharia screening for all stocks is completely free. Paid subscription is only required for in-depth research reports.",
      },
      {
        q: "Can I fully rely on Mizan's results?",
        a: "Mizan is an investment research tool and does not issue formal fatwa. It is recommended to consult a certified Sharia board for critical decisions.",
      },
      {
        q: "How often is stock data updated?",
        a: "Financial data is updated as soon as it is announced by Tadawul-listed companies (typically quarterly).",
      },
    ],
  },

  // Glossary
  glossary: {
    title: "Sharia & Investment Glossary",
    subtitle: "Key terms for understanding Sharia stock screening",
    terms: [
      { term: "AAOIFI", definition: "Accounting and Auditing Organization for Islamic Financial Institutions — the recognised body for Sharia standards." },
      { term: "Qualitative Screen", definition: "Verification that a company's core business does not contradict Sharia principles." },
      { term: "Quantitative Screen", definition: "Analysis of a company's financial ratios to ensure they stay within Sharia-permitted thresholds." },
      { term: "Income Purification", definition: "Donating the portion of profit derived from negligible non-compliant revenue to charity." },
      { term: "Riba", definition: "Excess or increase in a loan or debt in exchange for deferment — prohibited in Sharia." },
      { term: "Halal Stocks", definition: "Stocks of companies that pass both qualitative and quantitative screening per AAOIFI standards." },
    ],
  },

  // Auth page
  auth: {
    title: "Log In",
    subtitle: "Enter your email to log in or create a new account",
    email: "Email",
    password: "Password",
    login: "Log In",
    signup: "Sign Up",
    loggingIn: "Logging in...",
    errorGeneric: "Login failed. Check your credentials and try again.",
    noAccount: "Don't have an account?",
    haveAccount: "Already have an account?",
    createOne: "Create one",
    loginInstead: "Log in instead",
  },
};