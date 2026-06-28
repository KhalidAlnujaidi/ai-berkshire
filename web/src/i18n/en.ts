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
  // ===== Legal Pages =====
  legalPages: {
    privacy: {
      title: "Privacy Policy",
      lastUpdated: "Last updated: January 2025",
      intro: "This Privacy Policy explains how Mizan collects, uses, and protects your personal information when you use our platform.",
      sections: [
        {
          heading: "1. Information We Collect",
          body: "We collect information you provide directly: name, email address, and investment preferences. We also automatically collect usage data including pages visited, features used, and device information through cookies and similar technologies.",
        },
        {
          heading: "2. How We Use Your Information",
          body: "We use your information to: (a) provide and maintain the service; (b) notify you about changes to our service; (c) provide customer support; (d) gather analysis to improve our product; (e) monitor usage to detect and prevent fraud or technical issues.",
        },
        {
          heading: "3. Data Storage and Security",
          body: "Your data is stored on secure servers with industry-standard encryption (AES-256 at rest, TLS 1.3 in transit). We are hosted on Vercel and comply with Saudi Personal Data Protection Law (PDPL). Access is restricted to authorized personnel only.",
        },
        {
          heading: "4. Sharing of Information",
          body: "We do not sell your personal data. We may share information with: (a) service providers who help us operate the platform (hosting, analytics); (b) regulatory authorities when legally required. All third parties are bound by confidentiality obligations.",
        },
        {
          heading: "5. Your Rights",
          body: "Under Saudi PDPL, you have the right to: (a) access your personal data; (b) request correction of inaccurate data; (c) request deletion of your data; (d) withdraw consent to processing; (e) lodge a complaint with the relevant authority.",
        },
        {
          heading: "6. Cookies",
          body: "We use essential cookies for authentication and optional cookies for analytics. You can control cookie preferences in your browser settings. Disabling non-essential cookies will not affect core functionality.",
        },
        {
          heading: "7. Children's Privacy",
          body: "Our service is not directed to individuals under 18. We do not knowingly collect personal information from children.",
        },
        {
          heading: "8. Changes to This Policy",
          body: "We may update this Privacy Policy from time to time. We will notify you of significant changes via email or in-app notification at least 30 days before they take effect.",
        },
        {
          heading: "9. Contact Us",
          body: "If you have questions about this Privacy Policy, contact us at: privacy@mizan-invest.com",
        },
      ],
    },
    terms: {
      title: "Terms & Conditions",
      lastUpdated: "Last updated: January 2025",
      intro: "By accessing and using Mizan (mizan-invest.com), you accept and agree to be bound by these Terms and Conditions. If you do not agree, please do not use our service.",
      sections: [
        {
          heading: "1. Definitions",
          body: "\"Service\" refers to the Mizan platform. \"User\" refers to any individual accessing the service. \"Content\" refers to all data, analysis, reports, and information provided through the service.",
        },
        {
          heading: "2. Not Financial Advice",
          body: "Mizan is an analytical and educational platform. All content is provided for informational and research purposes only. Nothing on this platform constitutes financial, investment, legal, or tax advice. You should consult a licensed financial advisor before making investment decisions.",
        },
        {
          heading: "3. Sharia Compliance Disclaimer",
          body: "While Mizan screens stocks using AAOIFI Standard 21 criteria, our screening is algorithmic and informational. It is not a fatwa or religious ruling. For definitive religious guidance, consult a qualified Sharia scholar or your local Sharia board.",
        },
        {
          heading: "4. User Accounts",
          body: "You are responsible for maintaining the confidentiality of your account credentials and for all activities under your account. You agree to provide accurate information during registration and to keep it updated.",
        },
        {
          heading: "5. Acceptable Use",
          body: "You agree not to: (a) use the service for any unlawful purpose; (b) attempt to gain unauthorized access to any part of the service; (c) interfere with the proper functioning of the service; (d) scrape, copy, or redistribute content without permission; (e) use automated tools to access the service excessively.",
        },
        {
          heading: "6. Intellectual Property",
          body: "All content on Mizan — including text, graphics, logos, software, and analysis methodologies — is the property of Mizan and protected by intellectual property laws. You may not reproduce, distribute, or create derivative works without written permission.",
        },
        {
          heading: "7. Free and Paid Tiers",
          body: "The Free tier provides unlimited Sharia screening at no cost. The Pro tier (99 SAR/month) provides full investment research reports and additional features. Enterprise pricing is custom. All paid subscriptions can be cancelled at any time. Refunds are processed per our refund policy.",
        },
        {
          heading: "8. Limitation of Liability",
          body: "Mizan, its owners, and affiliates shall not be liable for any direct, indirect, incidental, consequential, or punitive damages arising from your use of the service. Investment decisions made based on information from this platform are entirely at your own risk.",
        },
        {
          heading: "9. No Warranty",
          body: "The service is provided \"as is\" and \"as available\" without warranties of any kind, express or implied. We do not warrant that the service will be uninterrupted, error-free, or that data will be accurate or complete.",
        },
        {
          heading: "10. Governing Law",
          body: "These terms are governed by the laws of the Kingdom of Saudi Arabia. Any disputes shall be resolved in the courts of Riyadh, Saudi Arabia.",
        },
        {
          heading: "11. Changes to Terms",
          body: "We reserve the right to modify these Terms at any time. Continued use of the service after changes constitutes acceptance of the new Terms.",
        },
        {
          heading: "12. Contact",
          body: "For questions about these Terms, contact: legal@mizan-invest.com",
        },
      ],
    },
    disclaimer: {
      title: "Disclaimer",
      lastUpdated: "Last updated: January 2025",
      sections: [
        {
          heading: "General Disclaimer",
          body: "The information provided by Mizan is for general informational and educational purposes only. All information is provided in good faith; however, we make no representation or warranty of any kind regarding the accuracy, adequacy, validity, reliability, or completeness of any information on the platform.",
        },
        {
          heading: "Not Financial Advice",
          body: "No content on Mizan constitutes financial, investment, legal, or tax advice. You should always seek the advice of a qualified financial advisor who understands your specific financial situation before making any investment decisions.",
        },
        {
          heading: "Sharia Screening Disclaimer",
          body: "Mizan's Sharia compliance screening is based on AAOIFI Standard 21 financial ratio thresholds. This is an algorithmic assessment, not a religious ruling (fatwa). For definitive religious guidance, please consult a qualified Sharia scholar. The screening criteria may not capture all relevant factors for every individual's specific religious obligations.",
        },
        {
          heading: "Investment Risk",
          body: "All investments carry risk, including the potential loss of principal. Past performance does not guarantee future results. The investment strategies discussed may not be suitable for all investors. You are responsible for your own investment decisions.",
        },
        {
          heading: "Data Accuracy",
          body: "While we strive to provide accurate and up-to-date financial data, we cannot guarantee the accuracy of all information. Financial data may be delayed or contain errors. Always verify critical data from official sources before making decisions.",
        },
        {
          heading: "Third-Party Links",
          body: "Mizan may contain links to third-party websites. We are not responsible for the content, accuracy, or practices of any third-party sites. We do not endorse or guarantee the offerings of any third party.",
        },
        {
          heading: "No Liability",
          body: "Under no circumstances shall Mizan, its team, or affiliates be liable for any loss or damage of any kind incurred as a result of using the platform or relying on any information provided. Your use of the platform is solely at your own risk.",
        },
      ],
    },
    compliance: {
      title: "Compliance",
      lastUpdated: "Last updated: January 2025",
      intro: "Mizan operates with a commitment to transparency, regulatory compliance, and user protection.",
      items: [
        { label: "Saudi PDPL", description: "We comply with the Kingdom of Saudi Arabia's Personal Data Protection Law (PDPL) for data handling and user privacy." },
        { label: "CMA Awareness", description: "We are not a licensed financial advisor under the Capital Market Authority (CMA). Our platform provides analytical tools, not investment advice." },
        { label: "AAOIFI Standards", description: "Our Sharia screening engine implements AAOIFI Standard 21 financial ratio thresholds for stock compliance assessment." },
        { label: "Data Security", description: "All data is encrypted in transit (TLS 1.3) and at rest (AES-256). User data is never sold to third parties." },
        { label: "Open Methodology", description: "Our screening criteria and thresholds are publicly documented on our Education Center page for full transparency." },
        { label: "Disclaimer", description: "Mizan is an analytical platform. All investment decisions are the user's responsibility." },
      ],
    },
  },

  // ===== About Page =====
  about: {
    title: "About Mizan",
    subtitle: "Making Sharia-compliant investing accessible to every Muslim investor",
    storyTitle: "Our Story",
    storyText: [
      "Mizan — meaning \"scale\" or \"balance\" in Arabic — was born from a simple observation: Muslim investors face a unique challenge. They need to evaluate not just whether a stock is a good investment, but whether it aligns with their faith.",
      "For too long, Sharia screening has been opaque, expensive, or locked behind consultant subscriptions. We believe every Muslim deserves free, instant, and transparent access to AAOIFI-standard compliance screening.",
      "Our team combines expertise in Islamic finance, software engineering, and AI. We have built a platform that applies the rigor of institutional Sharia screening algorithms — the same ratios used by specialized Sharia advisory firms — and makes it available to everyone, for free.",
      "We are proudly built in Saudi Arabia, aligned with Vision 2030's goal of a thriving financial sector, and committed to serving the 4.5 million+ retail investors in the Kingdom.",
    ],
    missionTitle: "Our Mission",
    missionText: "To empower every Muslim investor with free, instant, and transparent Sharia compliance tools — because faith and finance should never be in conflict.",
    valuesTitle: "Our Values",
    values: [
      { icon: "scale", title: "Transparency", description: "Every ratio, every threshold, every rule is public. No black boxes, no hidden criteria." },
      { icon: "mosque", title: "Faithfulness", description: "We follow AAOIFI standards rigorously. When criteria are ambiguous, we default to the stricter interpretation." },
      { icon: "shield", title: "User Protection", description: "We never sell user data. We never push stocks. We are an analytical tool, not a broker." },
      { icon: "lightbulb", title: "Education", description: "We do not just give verdicts — we explain the reasoning, so users learn and grow as investors." },
    ],
    teamTitle: "Built by Experts",
    teamText: "Our team brings together decades of experience in Islamic finance, software engineering at top tech companies, and AI research. We are based in Saudi Arabia and serve the Arabic-speaking world.",
    statsTitle: "Mizan by the Numbers",
    stats: [
      { value: "49", label: "Stocks Screened" },
      { value: "AAOIFI 21", label: "Standard Applied" },
      { value: "100%", label: "Free Core Features" },
      { value: "2", label: "Languages (AR/EN)" },
    ],
  },

  // ===== Contact Page =====
  contact: {
    title: "Contact Us",
    subtitle: "Questions, feedback, or partnership inquiries? We would love to hear from you.",
    formTitle: "Send a Message",
    nameLabel: "Your Name",
    namePlaceholder: "Ahmed Mohammed",
    emailLabel: "Email Address",
    emailPlaceholder: "ahmed@example.com",
    subjectLabel: "Subject",
    subjectPlaceholder: "How can we help?",
    messageLabel: "Message",
    messagePlaceholder: "Tell us more...",
    submitButton: "Send Message",
    submitting: "Sending...",
    successMessage: "Thank you! We will get back to you within 48 hours.",
    errorMessage: "Something went wrong. Please try again or email us directly.",
    directTitle: "Other Ways to Reach Us",
    emailLabel2: "Email",
    emailValue: "hello@mizan-invest.com",
    privacyEmail: "privacy@mizan-invest.com",
    legalEmail: "legal@mizan-invest.com",
    responseTime: "We respond within 48 hours",
    socialTitle: "Follow Us",
  },

  // ===== Not Found (404) =====
  notFound: {
    title: "Page Not Found",
    message: "Sorry, the page you are looking for does not exist or has been moved.",
    cta: "Back to Home",
    suggestTitle: "You might be looking for:",
    links: {
      sharia: "Sharia Checker",
      stocks: "Halal Stocks",
      learn: "Education Center",
    },
  },

};
