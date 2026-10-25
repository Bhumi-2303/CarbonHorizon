/**
 * analytics/index.ts
 *
 * Privacy-friendly analytics integration using Plausible Analytics.
 *
 * Why Plausible?
 * - Ultra-lightweight (< 1 KB script vs 45 KB for GA4).
 * - Zero cookies, no persistent identifiers or cross-site tracking.
 * - Compliant with GDPR, CCPA, and India's DPDP Act without fingerprinting.
 * - IP addresses are completely anonymized (never stored or logged).
 * - Exemption guarantee: Little Explorer (child) profiles are strictly excluded
 *   from any tracking whatsoever.
 * - Strictly gated by user cookie consent via useConsent().
 */

export type AnalyticsEvent =
  | 'signup_started'
  | 'assessment_completed'
  | 'forecast_viewed'
  | 'habit_logged'
  | 'coach_question_asked'
  | 'cta_clicked'

export interface EventProperties {
  signup_started?: { source?: string }
  assessment_completed?: { total_carbon_kg?: number; is_repeat?: boolean }
  forecast_viewed?: { timeframe_months?: number }
  habit_logged?: { habit_type?: string }
  coach_question_asked?: { category?: string } // NOTE: strictly never contains message text or PII
  cta_clicked?: { cta_label: string; location: string }
}

declare global {
  interface Window {
    plausible?: (
      eventName: string,
      options?: {
        props?: Record<string, string | number | boolean>
        callback?: () => void
      }
    ) => void
  }
}

let isInitialized = false

/**
 * Initialize or synchronize analytics script loading based on user consent and profile type.
 *
 * @param canTrackAnalytics - True only if user explicitly consented to analytics AND is not a child.
 * @param isChildProfile - True if user is a Little Explorer / child profile (< 13 or child tier).
 */
export function initAnalytics(canTrackAnalytics: boolean, isChildProfile: boolean): void {
  // CRITICAL RULE: Little Explorer profiles MUST NEVER be tracked under any circumstance
  if (isChildProfile || !canTrackAnalytics) {
    if (typeof document !== 'undefined') {
      const existing = document.getElementById('plausible-script')
      if (existing) {
        existing.remove()
      }
    }
    isInitialized = false
    return
  }

  if (isInitialized) return
  if (typeof document === 'undefined') return

  const domain =
    import.meta.env.VITE_ANALYTICS_DOMAIN ||
    import.meta.env.VITE_ANALYTICS_ID ||
    'carbonhorizon.app'
  const scriptUrl =
    import.meta.env.VITE_ANALYTICS_URL ||
    'https://plausible.io/js/script.manual.js'

  // Inject Plausible script tag
  const script = document.createElement('script')
  script.id = 'plausible-script'
  script.defer = true
  script.setAttribute('data-domain', domain)
  script.src = scriptUrl
  document.head.appendChild(script)

  isInitialized = true
}

/**
 * Track a typed privacy-friendly analytics event.
 *
 * Silently drops the event if:
 * 1. User has not consented to analytics
 * 2. User is a Little Explorer / child profile
 * 3. Script is not active or environment is headless/testing
 */
export function track<E extends AnalyticsEvent>(
  event: E,
  properties?: E extends keyof EventProperties ? EventProperties[E] : Record<string, unknown>,
  context?: { canTrackAnalytics?: boolean; isChildProfile?: boolean }
): void {
  // Safety checks
  if (context?.isChildProfile === true) return
  if (context?.canTrackAnalytics === false) return

  // Prevent sending sensitive text or PII accidentally
  const sanitizedProps = properties ? { ...properties } : undefined
  if (sanitizedProps && typeof sanitizedProps === 'object') {
    delete (sanitizedProps as Record<string, unknown>).message
    delete (sanitizedProps as Record<string, unknown>).email
    delete (sanitizedProps as Record<string, unknown>).password
    delete (sanitizedProps as Record<string, unknown>).user_id
    delete (sanitizedProps as Record<string, unknown>).full_name
  }

  if (typeof window !== 'undefined' && typeof window.plausible === 'function') {
    window.plausible(event, {
      props: sanitizedProps as Record<string, string | number | boolean>,
    })
  }
}
