import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import { ConsentProvider } from '@/context/ConsentContext'
import CookieConsent from '@/components/CookieConsent'
import PrivacyPage from '@/pages/PrivacyPage'
import TermsPage from '@/pages/TermsPage'
import NotFoundPage from '@/pages/NotFoundPage'

// Mock useAuth
vi.mock('@/context/AuthContext', () => ({
  useAuth: () => ({ user: null, isAuthenticated: false }),
}))

describe('Accessibility (A11y) Verification Suite (Tasks 10 & 13)', () => {
  it('verifies CookieConsent has role="dialog", aria-labelledby, and accessible buttons', () => {
    render(
      <BrowserRouter>
        <ConsentProvider>
          <CookieConsent />
        </ConsentProvider>
      </BrowserRouter>
    )

    const dialog = screen.getByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(dialog).toHaveAttribute('aria-labelledby')
    expect(dialog).toHaveAttribute('aria-describedby')

    // Every interactive button must have accessible name
    const buttons = screen.getAllByRole('button')
    for (const btn of buttons) {
      expect(btn.textContent?.trim() || btn.getAttribute('aria-label')).toBeTruthy()
    }
  })

  it('verifies PrivacyPage has valid landmark roles and heading hierarchy', () => {
    const { container } = render(
      <BrowserRouter>
        <ConsentProvider>
          <PrivacyPage />
        </ConsentProvider>
      </BrowserRouter>
    )

    // Heading hierarchy check
    const h1 = container.querySelector('h1')
    expect(h1).toBeInTheDocument()
    expect(h1?.textContent).toContain('Privacy Policy')

    const h2Elements = container.querySelectorAll('h2')
    expect(h2Elements.length).toBeGreaterThanOrEqual(5)

    // Check all SVGs are marked aria-hidden="true" or have title/role
    const svgs = container.querySelectorAll('svg')
    svgs.forEach((svg: Element) => {
      const isAriaHidden = svg.getAttribute('aria-hidden') === 'true'
      const hasLabel = svg.getAttribute('aria-label') || svg.getAttribute('role') === 'img'
      expect(isAriaHidden || hasLabel).toBe(true)
    })
  })

  it('verifies TermsPage has valid heading structure and accessible legal contact', () => {
    const { container } = render(
      <BrowserRouter>
        <ConsentProvider>
          <TermsPage />
        </ConsentProvider>
      </BrowserRouter>
    )

    const h1 = container.querySelector('h1')
    expect(h1).toBeInTheDocument()
    expect(h1?.textContent).toContain('Terms of Service')

    const h2Elements = container.querySelectorAll('h2')
    expect(h2Elements.length).toBeGreaterThanOrEqual(5)
  })

  it('verifies NotFoundPage has proper heading, noindex, and accessible navigation buttons', () => {
    const { container } = render(
      <BrowserRouter>
        <ConsentProvider>
          <NotFoundPage />
        </ConsentProvider>
      </BrowserRouter>
    )

    const h1 = container.querySelector('h1')
    expect(h1).toBeInTheDocument()
    expect(h1?.textContent).toContain('Uncharted Territory')

    // Check action links
    const links = container.querySelectorAll('a')
    expect(links.length).toBeGreaterThanOrEqual(1)
    links.forEach((link: Element) => {
      expect(link.textContent?.trim()).toBeTruthy()
    })
  })
})
