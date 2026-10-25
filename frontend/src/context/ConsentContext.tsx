import React, { createContext, useContext, useEffect, useState, useMemo, useCallback } from 'react'
import { useAuth } from './AuthContext'
import { initAnalytics } from '@/analytics'

export const CONSENT_STORAGE_KEY = 'carbon_horizon_cookie_consent'
export const CONSENT_VERSION = '2026-v1'

export interface ConsentPreferences {
  necessary: true
  analytics: boolean
  preferences: boolean
}

export interface ConsentRecord extends ConsentPreferences {
  version: string
  timestamp: string
}

export interface ConsentContextValue {
  consent: ConsentRecord | null
  hasConsented: boolean
  isBannerOpen: boolean
  isSettingsOpen: boolean
  canTrackAnalytics: boolean
  canStorePreferences: boolean
  acceptAll: () => void
  rejectAll: () => void
  saveCustom: (custom: { analytics: boolean; preferences: boolean }) => void
  openSettings: () => void
  closeSettings: () => void
  revokeConsent: () => void
}

const ConsentContext = createContext<ConsentContextValue | undefined>(undefined)

export const ConsentProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth()

  const [consent, setConsent] = useState<ConsentRecord | null>(() => {
    try {
      const stored = localStorage.getItem(CONSENT_STORAGE_KEY)
      if (!stored) return null
      const parsed: ConsentRecord = JSON.parse(stored)
      // Invalidate if version has changed
      if (parsed.version !== CONSENT_VERSION) {
        return null
      }
      return parsed
    } catch {
      return null
    }
  })

  const [isBannerOpen, setIsBannerOpen] = useState<boolean>(() => consent === null)
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false)

  // Listen to custom event so any footer/button can trigger openSettings without passing props
  useEffect(() => {
    const handleOpenEvent = () => setIsSettingsOpen(true)
    window.addEventListener('ch:open-cookie-settings', handleOpenEvent)
    return () => window.removeEventListener('ch:open-cookie-settings', handleOpenEvent)
  }, [])

  const persistConsent = useCallback((record: ConsentRecord) => {
    try {
      localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(record))
    } catch (e) {
      console.error('Failed to store cookie consent in localStorage', e)
    }
    setConsent(record)
    setIsBannerOpen(false)
    setIsSettingsOpen(false)
  }, [])

  const acceptAll = useCallback(() => {
    const record: ConsentRecord = {
      version: CONSENT_VERSION,
      timestamp: new Date().toISOString(),
      necessary: true,
      analytics: true,
      preferences: true,
    }
    persistConsent(record)
  }, [persistConsent])

  const rejectAll = useCallback(() => {
    const record: ConsentRecord = {
      version: CONSENT_VERSION,
      timestamp: new Date().toISOString(),
      necessary: true,
      analytics: false,
      preferences: false,
    }
    persistConsent(record)
  }, [persistConsent])

  const saveCustom = useCallback(
    ({ analytics, preferences }: { analytics: boolean; preferences: boolean }) => {
      const record: ConsentRecord = {
        version: CONSENT_VERSION,
        timestamp: new Date().toISOString(),
        necessary: true,
        analytics: Boolean(analytics),
        preferences: Boolean(preferences),
      }
      persistConsent(record)
    },
    [persistConsent]
  )

  const openSettings = useCallback(() => {
    setIsSettingsOpen(true)
  }, [])

  const closeSettings = useCallback(() => {
    setIsSettingsOpen(false)
  }, [])

  const revokeConsent = useCallback(() => {
    try {
      localStorage.removeItem(CONSENT_STORAGE_KEY)
    } catch (e) {
      console.error('Failed to clear cookie consent from localStorage', e)
    }
    setConsent(null)
    setIsBannerOpen(true)
    setIsSettingsOpen(false)
  }, [])

  // Never track analytics for Little Explorer / child profiles regardless of user consent
  const isChildProfile = useMemo(() => {
    if (!user) return false
    if (user.age_group === 'child') return true
    if (typeof user.age === 'number' && user.age >= 4 && user.age <= 12) return true
    return false
  }, [user])

  const canTrackAnalytics = Boolean(!isChildProfile && consent?.analytics)
  const canStorePreferences = Boolean(consent?.preferences)

  // Initialize or teardown analytics according to user consent and child profile rule
  useEffect(() => {
    initAnalytics(canTrackAnalytics, isChildProfile)
  }, [canTrackAnalytics, isChildProfile])

  const value = useMemo(
    () => ({
      consent,
      hasConsented: consent !== null,
      isBannerOpen,
      isSettingsOpen,
      canTrackAnalytics,
      canStorePreferences,
      acceptAll,
      rejectAll,
      saveCustom,
      openSettings,
      closeSettings,
      revokeConsent,
    }),
    [
      consent,
      isBannerOpen,
      isSettingsOpen,
      canTrackAnalytics,
      canStorePreferences,
      acceptAll,
      rejectAll,
      saveCustom,
      openSettings,
      closeSettings,
      revokeConsent,
    ]
  )

  return <ConsentContext.Provider value={value}>{children}</ConsentContext.Provider>
}

export function useConsent(): ConsentContextValue {
  const context = useContext(ConsentContext)
  if (!context) {
    throw new Error('useConsent must be used within a ConsentProvider')
  }
  return context
}
