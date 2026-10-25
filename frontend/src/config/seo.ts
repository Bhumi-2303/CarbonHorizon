export interface PublicRouteEntry {
  path: string
  changefreq: 'always' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'never'
  priority: string
}

export const PUBLIC_ROUTES: readonly PublicRouteEntry[] = [
  { path: '/', changefreq: 'daily', priority: '1.0' },
  { path: '/privacy', changefreq: 'monthly', priority: '0.5' },
  { path: '/terms', changefreq: 'monthly', priority: '0.5' },
  { path: '/login', changefreq: 'monthly', priority: '0.8' },
  { path: '/register', changefreq: 'monthly', priority: '0.9' },
] as const

export interface PageSeoConfig {
  title: string
  description: string
  path: string
  noindex?: boolean
}

export const SITE_METADATA = {
  siteName: 'Carbon Horizon',
  defaultTitle: 'Carbon Horizon | Personal Carbon Footprint Tracker',
  defaultDescription:
    'Track your personal carbon footprint, simulate reductions, build eco-habits, and chat with an AI climate coach.',
  baseUrl: (import.meta.env.VITE_APP_URL || 'https://carbonhorizon.app').replace(/\/$/, ''),
  defaultOgImage: '/og-image.png',
  defaultOgImageAlt:
    'Carbon Horizon - Personal Climate Intelligence & AI Sustainability Coach',
  themeColor: '#0F172A',
  locale: 'en_US',
  twitterCard: 'summary_large_image',
} as const

export const SEO_PAGES: Record<string, PageSeoConfig> = {
  landing: {
    title: 'Carbon Horizon | Personal Carbon Footprint Tracker',
    description:
      'Calculate your carbon footprint across transport, energy, food, and waste. Get tailored reduction advice from our AI sustainability coach.',
    path: '/',
  },
  login: {
    title: 'Sign In | Carbon Horizon',
    description:
      'Sign in to your Carbon Horizon account to view your carbon footprint dashboard, goal progress, and AI coach history.',
    path: '/login',
  },
  signup: {
    title: 'Create an Account | Carbon Horizon',
    description:
      'Join Carbon Horizon to track, forecast, and cut your personal carbon emissions with guided AI climate coaching.',
    path: '/register',
  },
  privacy: {
    title: 'Privacy Policy | Carbon Horizon',
    description:
      'Learn how Carbon Horizon protects your personal data under DPDP and GDPR, with strict privacy safeguards for child accounts.',
    path: '/privacy',
  },
  terms: {
    title: 'Terms of Service | Carbon Horizon',
    description:
      'Read the terms of service governing your use of Carbon Horizon, including eligibility, acceptable use, and carbon estimates.',
    path: '/terms',
  },
  notFound: {
    title: 'Page Not Found | Carbon Horizon',
    description:
      'The requested page could not be found. Return to Carbon Horizon to continue tracking your sustainability journey.',
    path: '/404',
    noindex: true,
  },
  // Authenticated pages — default noindex
  dashboard: {
    title: 'Dashboard | Carbon Horizon',
    description: 'Your sustainability analytics and footprint tracking dashboard.',
    path: '/dashboard',
    noindex: true,
  },
  assessment: {
    title: 'Carbon Assessment | Carbon Horizon',
    description: 'Assess your monthly or annual greenhouse gas emissions.',
    path: '/assessment',
    noindex: true,
  },
  simulator: {
    title: 'Reduction Simulator | Carbon Horizon',
    description: 'Simulate climate reduction scenarios and evaluate impact.',
    path: '/simulator',
    noindex: true,
  },
  forecast: {
    title: 'Emission Forecast | Carbon Horizon',
    description: 'View projected future carbon trajectories and reduction milestones.',
    path: '/forecast',
    noindex: true,
  },
  goals: {
    title: 'Sustainability Goals | Carbon Horizon',
    description: 'Set and track personal carbon reduction goals.',
    path: '/goals',
    noindex: true,
  },
  habits: {
    title: 'Eco-Habit Tracker | Carbon Horizon',
    description: 'Build and monitor daily sustainable habits.',
    path: '/habits',
    noindex: true,
  },
  coach: {
    title: 'AI Climate Coach | Carbon Horizon',
    description: 'Chat with our AI climate coach for personalized eco advice.',
    path: '/coach',
    noindex: true,
  },
} as const
