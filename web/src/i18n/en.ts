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
      investors: "+146%",
      stocks: "20",
      sharia: "70%",
      accuracy: "+66%",
    },
    statValues: {
      investors: "4.5M+",
      stocks: "200+",
      sharia: "70%",
      accuracy: "99%",
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
      "Past performance does not guarantee future results. Returns verified from real brokerage account.",
  },

  trustBar: {
    title: "Trusted by",
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
  },

  // Discover — Halal Stocks Grid
  discover: {
    title: "The Halal Universe",
    subtitle: "Every stock here has already passed dual Sharia screening — browse with confidence",
    filterAll: "All Sectors",
    screened: "screened",
    passed: "passed",
    verifiedHalal: "Verified Halal",
    needsPurification: "Needs Purification",
    viewDetails: "View Details",
    loadingText: "Screening stocks...",
  },


  features: {
    sectionTitle: "Why Mizan?",
    sectionSubtitle: "Four engines working together for your best investment decision",
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
    sectionSubtitle: "Start free — pay only when you need depth",
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
        description: "For the beginning investor",
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
        description: "For the serious investor",
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
    pifTitle: "Track the Public Investment Fund",
    pifDescription:
      "$925B+. We track where Saudi Arabia's sovereign wealth fund deploys capital and connect it to Tadawul investment opportunities.",
  },

  howItWorks: {
    title: "How Mizan Works",
    subtitle: "Three simple steps to a confident investment decision",
    steps: [
      {
        number: "1",
        title: "Enter Stock",
        description: "Type the ticker or company name in the Sharia checker",
      },
      {
        number: "2",
        title: "Screen for Sharia",
        description: "Mizan analyzes the stock per AAOIFI standards and financial ratios",
      },
      {
        number: "3",
        title: "Make a Decision",
        description: "Get a clear verdict: Compliant, Compliant with Purification, or Non-Compliant",
      },
    ],
  },

  cta: {
    title: "Ready to start your investment journey?",
    subtitle: "Join thousands of Saudi investors who trust Mizan",
    button: "Start Free Now",
    note: "No credit card required",
  },

  // Compare tool
  compare: {
    title: "Compare Stocks",
    subtitle: "Compare up to 3 stocks side by side — Sharia screening, financial ratios, and verdicts",
    addStock: "Add a stock to compare",
    searchPlaceholder: "Search by ticker or company name...",
    remove: "Remove",
    maxReached: "Maximum 3 stocks",
    emptyState: "Add at least one stock to start comparing",
    metricVerdict: "Sharia Verdict",
    metricSector: "Sector",
    metricMarket: "Market",
    metricDebtAssets: "Debt / Assets",
    metricDebtMcap: "Debt / Market Cap",
    metricInterestInv: "Interest Investments / Assets",
    metricReceivables: "Receivables",
    metricNonCompliant: "Non-compliant Income",
    metricStandard: "Standard",
    bestInClass: "Best",
    passCount: "Ratios Passed",
    compliant: "Compliant",
    nonCompliant: "Non-compliant",
    needsPurification: "Needs Purification",
    pickPrompt: "Select stocks to compare",
    vs: "vs",
    noRatios: "No financial data available",
  },

  // Portfolio Screener
  portfolio: {
    title: "Portfolio Screener",
    subtitle: "Enter your holdings to get a comprehensive Sharia assessment of your entire portfolio",
    addHolding: "Add Holding",
    tickerPlaceholder: "Ticker or company name",
    amountPlaceholder: "Amount invested",
    analyze: "Analyze Portfolio",
    analyzing: "Analyzing...",
    empty: "Add at least one holding to start analysis",
    remove: "Remove",
    yourPortfolio: "Your Portfolio",
    portfolioScore: "Portfolio Score",
    halalScore: "Halal Ratio",
    totalValue: "Total Value",
    holdings: "Holdings",
    nonCompliantAmount: "Non-compliant",
    purificationAmount: "Needs Purification",
    halalAmount: "Halal",
    perHolding: "Holding Details",
    recommendations: "Recommendations",
    weight: "Weight",
    verdict: "Verdict",
    amount: "Amount",
    sector: "Sector",
    addExample: "Add Example",
    gradeCompliant: "Sharia-Compliant",
    gradeRebalancing: "Needs Rebalancing",
    gradePurification: "Purification Required",
    gradeHighRisk: "High Risk",
  },

  // Education Center
  education: {
    title: "Sharia Investment Academy",
    subtitle: "Learn the principles of halal investing — understand how Mizan screens every stock",
    heroBadge: "Knowledge is power",
    statTotalStocks: "Stocks Screened",
    statHalalRate: "Halal Rate",
    statSectors: "Sectors Covered",
    statStandard: "Sharia Standard",

    sectionRatios: "The 6 Financial Ratios",
    sectionRatiosDesc: "Every stock must pass all six AAOIFI quantitative screens. If any ratio exceeds its threshold, the stock is non-compliant.",
    ratio1Name: "Debt to Total Assets",
    ratio1Threshold: "≤ 33%",
    ratio1Desc: "Interest-bearing debt must not exceed one-third of total assets. This ensures the company isn't overly leveraged.",
    ratio2Name: "Debt to Market Cap",
    ratio2Threshold: "≤ 33%",
    ratio2Desc: "Interest-bearing debt relative to market value must stay under one-third. A market check on borrowing.",
    ratio3Name: "Interest-Bearing Investments",
    ratio3Threshold: "≤ 33%",
    ratio3Desc: "Cash and investments in interest-bearing instruments must not exceed one-third of total assets.",
    ratio4Name: "Receivables to Assets",
    ratio4Threshold: "≤ 50%",
    ratio4Desc: "Accounts receivable and cash must not exceed 50% of total assets. Prevents over-reliance on debt-based transactions.",
    ratio5Name: "Non-Compliant Income",
    ratio5Threshold: "≤ 5%",
    ratio5Desc: "Income from non-compliant activities must not exceed 5% of total revenue. Minor impurities are purified.",
    ratio6Name: "Illiquid Asset Ratio",
    ratio6Threshold: "≥ 20%",
    ratio6Desc: "The company must hold at least 20% of assets in real, tangible (non-monetary) form.",

    sectionQualitative: "Qualitative Screen — Permitted & Prohibited Sectors",
    sectionQualitativeDesc: "Before checking ratios, Mizan checks the core business activity itself. Some sectors are prohibited outright.",
    prohibitedTitle: "Prohibited Activities",
    prohibitedDesc: "Stocks in these sectors fail immediately — no ratio screen can save them.",
    permittedTitle: "Permitted Activities",
    permittedDesc: "These sectors are allowed by default, subject to passing the financial ratio screens.",
    prohibited: [
      "Conventional banking & insurance (riba-based)",
      "Pork production & related products",
      "Alcoholic beverages & related",
      "Gambling & casinos",
      "Adult entertainment",
      "Weapons of mass destruction",
    ],
    permitted: [
      "Islamic banking & financial services",
      "Energy (oil, gas, petrochemicals)",
      "Technology & telecommunications",
      "Real estate & construction",
      "Healthcare & pharmaceuticals",
      "Agriculture & food (halal)",
      "Manufacturing & industrials",
      "Retail & consumer goods",
    ],

    sectionPurification: "Income Purification",
    sectionPurificationDesc: "When a halal stock earns a small amount of non-compliant income (≤ 5%), you must purify that portion by donating it to charity.",
    purifStep1: "Identify the non-compliant income percentage from the screening report",
    purifStep2: "Calculate that percentage of your dividends or investment gains",
    purifStep3: "Donate the calculated amount to a qualified charity (not as regular zakat)",
    purifStep4: "Keep records for accountability",
    purifNote: "Mizan calculates this automatically in the Portfolio Screener.",

    sectionFaq: "Frequently Asked Questions",
    faq: [
      {
        q: "What is AAOIFI Standard No. 21?",
        a: "AAOIFI (Accounting and Auditing Organization for Islamic Financial Institutions) Standard 21 defines the criteria for Sharia-compliant equities. It is the most widely accepted standard among Islamic scholars worldwide.",
      },
      {
        q: "Is Mizan's screening a fatwa?",
        a: "No. Mizan applies AAOIFI ratios deterministically — it's a mathematical filter. For a formal religious ruling, consult a qualified Sharia scholar. Mizan helps you narrow down, not replace, scholarly advice.",
      },
      {
        q: "What happens if a stock passes today but fails tomorrow?",
        a: "Financial ratios change quarterly as companies report new data. Mizan re-screens every time you query, so the verdict always reflects current data. We recommend re-screening after each earnings season.",
      },
      {
        q: "Can a halal stock become non-compliant?",
        a: "Yes. If a company takes on too much debt or its non-compliant income spikes above 5%, it can lose compliance. Mizan's Portfolio Screener alerts you to this.",
      },
      {
        q: "Do you cover US or international stocks?",
        a: "The screening engine is market-agnostic. We currently cover Saudi Tadawul stocks, with US and international markets on the roadmap.",
      },
    ],

    marketOverview: "Market Compliance Overview",
    sectorCol: "Sector",
    totalCol: "Total Stocks",
    halalCol: "Halal",
    rateCol: "Compliance Rate",
    loadingStats: "Loading market data...",
    ctaTitle: "Ready to apply what you learned?",
    ctaButton: "Screen Your First Stock",
  },


  footer: {
    tagline: "The Sharia-compliant investment platform",
    product: "Product",
    productLinks: {
      sharia: "Sharia Checker",
      research: "Investment Research",
      portfolio: "Portfolio Monitoring",
      api: "API",
    },
    company: "Company",
    companyLinks: {
      about: "About",
      careers: "Careers",
      blog: "Blog",
      contact: "Contact",
    },
    legal: "Legal",
    legalLinks: {
      privacy: "Privacy Policy",
      terms: "Terms & Conditions",
      compliance: "Compliance",
      disclaimer: "Disclaimer",
    },
    disclaimer:
      "Mizan is an analytical platform, not a financial advisor. All investment decisions are the user's responsibility. Content is for educational and research purposes only.",
    copyright: "© 2025 Mizan. All rights reserved.",
    madeIn: "Made in Saudi Arabia 🇸🇦",
  },
};
