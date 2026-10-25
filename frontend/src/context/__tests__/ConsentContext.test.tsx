import { render, screen, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import {
  ConsentProvider,
  useConsent,
  CONSENT_STORAGE_KEY,
  CONSENT_VERSION,
} from '../ConsentContext'
import { CookieConsent } from '@/components/CookieConsent'

// Mock useAuth
const mockUseAuth = vi.fn()
vi.mock('../AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

const TestConsumer = () => {
  const {
    consent,
    hasConsented,
    isBannerOpen,
    canTrackAnalytics,
    canStorePreferences,
    acceptAll,
    rejectAll,
    saveCustom,
    revokeConsent,
    openSettings,
  } = useConsent()

  return (
    <div>
      <span data-testid="consented">{String(hasConsented)}</span>
      <span data-testid="banner-open">{String(isBannerOpen)}</span>
      <span data-testid="can-track">{String(canTrackAnalytics)}</span>
      <span data-testid="can-pref">{String(canStorePreferences)}</span>
      <span data-testid="analytics-val">{String(consent?.analytics)}</span>
      <span data-testid="prefs-val">{String(consent?.preferences)}</span>
      <button onClick={acceptAll} data-testid="accept-btn">Accept</button>
      <button onClick={rejectAll} data-testid="reject-btn">Reject</button>
      <button onClick={() => saveCustom({ analytics: true, preferences: false })} data-testid="custom-btn">Custom</button>
      <button onClick={revokeConsent} data-testid="revoke-btn">Revoke</button>
      <button onClick={openSettings} data-testid="settings-btn">Settings</button>
    </div>
  )
}

describe('ConsentContext & CookieConsent', () => {
  beforeEach(() => {
    localStorage.clear()
    mockUseAuth.mockReturnValue({ user: null })
  })

  it('initializes with unconsented state when no localStorage exists', () => {
    render(
      <ConsentProvider>
        <TestConsumer />
      </ConsentProvider>
    )

    expect(screen.getByTestId('consented').textContent).toBe('false')
    expect(screen.getByTestId('banner-open').textContent).toBe('true')
    expect(screen.getByTestId('can-track').textContent).toBe('false')
  })

  it('accepts all cookies, persists in localStorage with timestamp and version', async () => {
    render(
      <ConsentProvider>
        <TestConsumer />
      </ConsentProvider>
    )

    await act(async () => {
      screen.getByTestId('accept-btn').click()
    })

    expect(screen.getByTestId('consented').textContent).toBe('true')
    expect(screen.getByTestId('banner-open').textContent).toBe('false')
    expect(screen.getByTestId('can-track').textContent).toBe('true')
    expect(screen.getByTestId('can-pref').textContent).toBe('true')

    const stored = JSON.parse(localStorage.getItem(CONSENT_STORAGE_KEY) || '{}')
    expect(stored.version).toBe(CONSENT_VERSION)
    expect(stored.necessary).toBe(true)
    expect(stored.analytics).toBe(true)
    expect(stored.preferences).toBe(true)
    expect(stored.timestamp).toBeDefined()
  })

  it('rejects all optional cookies, persists necessary-only in localStorage', async () => {
    render(
      <ConsentProvider>
        <TestConsumer />
      </ConsentProvider>
    )

    await act(async () => {
      screen.getByTestId('reject-btn').click()
    })

    expect(screen.getByTestId('consented').textContent).toBe('true')
    expect(screen.getByTestId('can-track').textContent).toBe('false')
    expect(screen.getByTestId('can-pref').textContent).toBe('false')

    const stored = JSON.parse(localStorage.getItem(CONSENT_STORAGE_KEY) || '{}')
    expect(stored.necessary).toBe(true)
    expect(stored.analytics).toBe(false)
    expect(stored.preferences).toBe(false)
  })

  it('revokes consent correctly and clears localStorage', async () => {
    render(
      <ConsentProvider>
        <TestConsumer />
      </ConsentProvider>
    )

    await act(async () => {
      screen.getByTestId('accept-btn').click()
    })
    expect(screen.getByTestId('consented').textContent).toBe('true')

    await act(async () => {
      screen.getByTestId('revoke-btn').click()
    })

    expect(screen.getByTestId('consented').textContent).toBe('false')
    expect(screen.getByTestId('banner-open').textContent).toBe('true')
    expect(localStorage.getItem(CONSENT_STORAGE_KEY)).toBeNull()
  })

  it('never loads analytics for Little Explorer child profile regardless of consent', async () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: 'child-123',
        age: 8,
        age_group: 'child',
      },
    })

    render(
      <ConsentProvider>
        <TestConsumer />
      </ConsentProvider>
    )

    await act(async () => {
      screen.getByTestId('accept-btn').click()
    })

    // Consent record has analytics: true, but canTrackAnalytics must be strictly false
    expect(screen.getByTestId('analytics-val').textContent).toBe('true')
    expect(screen.getByTestId('can-track').textContent).toBe('false')
  })

  it('renders CookieConsent accessible dialog with role="dialog" and aria-labelledby', async () => {
    const user = userEvent.setup()

    render(
      <BrowserRouter>
        <ConsentProvider>
          <CookieConsent />
        </ConsentProvider>
      </BrowserRouter>
    )

    const dialog = screen.getByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(dialog).toHaveAttribute('aria-labelledby', 'cookie-consent-title')

    const rejectButton = screen.getByRole('button', { name: /Reject All/i })
    const acceptButton = screen.getByRole('button', { name: /Accept All/i })
    expect(rejectButton).toBeInTheDocument()
    expect(acceptButton).toBeInTheDocument()

    // Test rejecting via UI
    await user.click(rejectButton)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()

    const stored = JSON.parse(localStorage.getItem(CONSENT_STORAGE_KEY) || '{}')
    expect(stored.analytics).toBe(false)
  })
})
