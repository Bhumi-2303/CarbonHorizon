import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { ShieldCheck, Cookie, Settings, Check, X } from 'lucide-react'
import { useConsent } from '@/hooks/useConsent'
import { useAuth } from '@/context/AuthContext'

export function CookieConsent() {
  const {
    consent,
    isBannerOpen,
    isSettingsOpen,
    acceptAll,
    rejectAll,
    saveCustom,
    openSettings,
    closeSettings,
  } = useConsent()

  const { user } = useAuth()
  const isChild = user?.age_group === 'child' || (typeof user?.age === 'number' && user.age >= 4 && user.age <= 12)

  // Local state for customize modal
  const [analyticsEnabled, setAnalyticsEnabled] = useState(consent ? consent.analytics : false)
  const [preferencesEnabled, setPreferencesEnabled] = useState(consent ? consent.preferences : false)

  const dialogRef = useRef<HTMLDivElement>(null)
  const firstFocusableRef = useRef<HTMLButtonElement>(null)
  const firstInputRef = useRef<HTMLInputElement>(null)

  // Sync state when consent updates or settings opens
  useEffect(() => {
    if (consent) {
      setAnalyticsEnabled(consent.analytics)
      setPreferencesEnabled(consent.preferences)
    }
  }, [consent, isSettingsOpen])

  // Focus management
  useEffect(() => {
    if (isBannerOpen) {
      const timer = setTimeout(() => {
        firstFocusableRef.current?.focus()
      }, 50)
      return () => clearTimeout(timer)
    } else if (isSettingsOpen) {
      const timer = setTimeout(() => {
        firstInputRef.current?.focus()
      }, 50)
      return () => clearTimeout(timer)
    }
  }, [isBannerOpen, isSettingsOpen])

  // Keyboard navigation: Escape key closes settings if already consented
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isSettingsOpen && consent) {
        closeSettings()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isSettingsOpen, consent, closeSettings])

  if (!isBannerOpen && !isSettingsOpen) {
    return null
  }

  const handleSaveCustom = () => {
    saveCustom({
      analytics: isChild ? false : analyticsEnabled,
      preferences: preferencesEnabled,
    })
  }

  return (
    <div
      role="dialog"
      aria-modal="false"
      aria-labelledby="cookie-consent-title"
      aria-describedby="cookie-consent-desc"
      ref={dialogRef}
      className="fixed bottom-4 left-4 right-4 md:left-auto md:right-6 md:max-w-xl z-50 animate-fade-in"
    >
      <div className="glass-panel p-6 shadow-2xl border border-white/15 bg-bg-card-solid/95 backdrop-blur-xl rounded-2xl text-primary">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-earth-green/20 text-earth-green flex items-center justify-center shrink-0">
              <Cookie className="w-5 h-5" aria-hidden="true" />
            </div>
            <div>
              <h2 id="cookie-consent-title" className="font-poppins font-semibold text-base text-primary">
                {isSettingsOpen ? 'Cookie & Privacy Preferences' : 'We value your privacy'}
              </h2>
              <span className="text-xs text-slate-400">Compliance with DPDP & GDPR</span>
            </div>
          </div>
          {isSettingsOpen && consent && (
            <button
              onClick={closeSettings}
              className="p-1 rounded-lg text-slate-400 hover:text-primary hover:bg-white/5 transition-colors"
              aria-label="Close cookie settings dialog"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Description or Preferences panel */}
        {!isSettingsOpen ? (
          <div>
            <p id="cookie-consent-desc" className="text-sm text-slate-300 leading-relaxed mb-4">
              We use necessary cookies to make our platform function securely. With your consent, we also use optional cookies to analyze usage and remember your preferences. Little Explorer (child) profiles never receive analytics or tracking cookies. Learn more in our{' '}
              <Link to="/privacy" className="text-emerald-700 dark:text-emerald-300 underline hover:text-emerald-600 dark:hover:text-emerald-200 font-semibold">
                Privacy Policy
              </Link>.
            </p>

            {/* Reject-all and Accept-all must be equally prominent */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1">
              <button
                ref={firstFocusableRef}
                type="button"
                onClick={rejectAll}
                className="py-2.5 px-4 rounded-xl font-semibold text-sm border-2 border-white/20 bg-white/5 text-primary hover:bg-white/10 hover:border-white/30 transition-all text-center focus:outline-none focus:ring-2 focus:ring-earth-green"
              >
                Reject All
              </button>
              <button
                type="button"
                onClick={openSettings}
                className="py-2.5 px-4 rounded-xl font-semibold text-sm border border-white/10 bg-white/5 text-slate-300 hover:text-primary hover:bg-white/10 transition-all flex items-center justify-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-earth-green"
              >
                <Settings className="w-4 h-4" aria-hidden="true" />
                Customize
              </button>
              <button
                type="button"
                onClick={acceptAll}
                className="py-2.5 px-4 rounded-xl font-bold text-sm border-2 border-earth-green bg-earth-green text-white dark:text-slate-950 hover:bg-emerald-400 hover:border-emerald-400 transition-all text-center focus:outline-none focus:ring-2 focus:ring-earth-green"
              >
                Accept All
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <p id="cookie-consent-desc" className="text-xs text-slate-300 leading-relaxed">
              Manage your cookie preferences. Essential cookies cannot be disabled as they are required for security and core navigation.
            </p>

            {/* Categories */}
            <div className="space-y-3 pt-1">
              {/* Category 1: Necessary */}
              <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 flex items-start justify-between gap-3">
                <div className="text-xs">
                  <div className="flex items-center gap-1.5 font-semibold text-primary">
                    <ShieldCheck className="w-4 h-4 text-earth-green" aria-hidden="true" />
                    <span>Necessary (Always Active)</span>
                  </div>
                  <p className="text-slate-400 mt-1">
                    Essential for secure authentication, session management, and routing. Cannot be turned off.
                  </p>
                </div>
                <span className="text-[11px] font-semibold text-earth-green bg-earth-green/10 px-2 py-1 rounded-md shrink-0">
                  Required
                </span>
              </div>

              {/* Category 2: Analytics */}
              <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 flex items-start justify-between gap-3">
                <div className="text-xs">
                  <label htmlFor="analytics-toggle" className="font-semibold text-primary cursor-pointer">
                    Analytics & Performance
                  </label>
                  <p className="text-slate-400 mt-1">
                    Helps us understand platform usage to improve feature performance. Anonymized data only.
                  </p>
                  {isChild && (
                    <p className="text-emerald-400 text-[11px] mt-1 font-medium">
                      ✓ Disabled automatically for Little Explorer child profile.
                    </p>
                  )}
                </div>
                <input
                  id="analytics-toggle"
                  type="checkbox"
                  ref={firstInputRef}
                  disabled={isChild}
                  checked={isChild ? false : analyticsEnabled}
                  onChange={(e) => setAnalyticsEnabled(e.target.checked)}
                  className="w-5 h-5 rounded border-white/20 bg-white/5 text-earth-green focus:ring-earth-green shrink-0 mt-0.5 cursor-pointer disabled:cursor-not-allowed"
                />
              </div>

              {/* Category 3: Preferences */}
              <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 flex items-start justify-between gap-3">
                <div className="text-xs">
                  <label htmlFor="preferences-toggle" className="font-semibold text-primary cursor-pointer">
                    Preferences & Customization
                  </label>
                  <p className="text-slate-400 mt-1">
                    Remembers your UI settings, theme choices, and local calculator presets.
                  </p>
                </div>
                <input
                  id="preferences-toggle"
                  type="checkbox"
                  checked={preferencesEnabled}
                  onChange={(e) => setPreferencesEnabled(e.target.checked)}
                  className="w-5 h-5 rounded border-white/20 bg-white/5 text-earth-green focus:ring-earth-green shrink-0 mt-0.5 cursor-pointer"
                />
              </div>
            </div>

            {/* Modal Actions */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2">
              <button
                type="button"
                onClick={rejectAll}
                className="py-2 px-3 rounded-xl font-semibold text-xs border border-white/20 bg-white/5 text-primary hover:bg-white/10 transition-colors text-center"
              >
                Reject All
              </button>
              <button
                type="button"
                onClick={handleSaveCustom}
                className="py-2 px-3 rounded-xl font-semibold text-xs border border-earth-green/60 bg-earth-green/10 text-earth-green hover:bg-earth-green/20 transition-colors flex items-center justify-center gap-1"
              >
                <Check className="w-3.5 h-3.5" aria-hidden="true" />
                Save Choices
              </button>
              <button
                type="button"
                onClick={acceptAll}
                className="py-2 px-3 rounded-xl font-bold text-xs border border-earth-green bg-earth-green text-white dark:text-slate-950 hover:bg-emerald-400 transition-colors text-center"
              >
                Accept All
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export function CookieSettingsButton({ className = '' }: { className?: string }) {
  const { openSettings } = useConsent()
  return (
    <button
      type="button"
      onClick={openSettings}
      className={`text-slate-400 hover:text-earth-green transition-colors text-left ${className}`}
    >
      Cookie settings
    </button>
  )
}

export default CookieConsent
