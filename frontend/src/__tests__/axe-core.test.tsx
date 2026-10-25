/**
 * Axe-core Accessibility Audit Test Suite
 *
 * Audits all primary application surfaces for WCAG 2.1 AA violations:
 * - LandingPage (hero, stats, CTA, trust features)
 * - Login (accessible inputs, error states, honeypot hidden, submit button)
 * - Register (accessible form fields, cascading location placeholders, disabled states)
 * - DashboardPage (glassmorphism cards, metrics, summary text)
 * - PrivacyPage (headings, document landmarks, external links)
 * - TermsPage (accessible terms sections, legal contact)
 * - NotFoundPage (404 illustration, accessible navigation links)
 */

import { render } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import axe from 'axe-core'
import { ConsentProvider } from '@/context/ConsentContext'
import LandingPage from '@/pages/LandingPage'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import DashboardPage from '@/pages/DashboardPage'
import PrivacyPage from '@/pages/PrivacyPage'
import TermsPage from '@/pages/TermsPage'
import NotFoundPage from '@/pages/NotFoundPage'

// Mock useAuth
vi.mock('@/context/AuthContext', () => ({
  useAuth: () => ({
    user: {
      id: 'test-user-id',
      email: 'test@carbonhorizon.app',
      full_name: 'Test Auditor',
      age_group: 'adult',
    },
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}))

// Mock dashboardApi
vi.mock('@/api/dashboard', () => ({
  dashboardApi: {
    getDashboard: vi.fn().mockResolvedValue({
      latest_assessment: {
        carbon_score: 4200,
        lifestyle_baseline: 5000,
        reduction_percentage: 16,
      },
      active_goals_count: 3,
      total_assessments: 2,
      tier: 'Adult',
    }),
  },
}))

describe('Axe-core Accessibility Audits (Task 6)', () => {
  it('audits LandingPage for 0 axe-core violations', async () => {
    const { container } = render(
      <BrowserRouter>
        <ConsentProvider>
          <LandingPage />
        </ConsentProvider>
      </BrowserRouter>
    )

    const results = await axe.run(container, {
      rules: {
        // In jsdom environment, color-contrast cannot compute full layout computed styles;
        // axe-core color contrast is verified via computed luminance tests
        'color-contrast': { enabled: false },
      },
    })

    expect(results.violations).toEqual([])
  })

  it('audits Login page for 0 axe-core violations', async () => {
    const { container } = render(
      <BrowserRouter>
        <ConsentProvider>
          <Login />
        </ConsentProvider>
      </BrowserRouter>
    )

    const results = await axe.run(container, {
      rules: {
        'color-contrast': { enabled: false },
      },
    })

    expect(results.violations).toEqual([])
  })

  it('audits Register page for 0 axe-core violations', async () => {
    const { container } = render(
      <BrowserRouter>
        <ConsentProvider>
          <Register />
        </ConsentProvider>
      </BrowserRouter>
    )

    const results = await axe.run(container, {
      rules: {
        'color-contrast': { enabled: false },
      },
    })

    expect(results.violations).toEqual([])
  })

  it('audits DashboardPage for 0 axe-core violations', async () => {
    const { container } = render(
      <BrowserRouter>
        <ConsentProvider>
          <DashboardPage />
        </ConsentProvider>
      </BrowserRouter>
    )

    const results = await axe.run(container, {
      rules: {
        'color-contrast': { enabled: false },
      },
    })

    expect(results.violations).toEqual([])
  })

  it('audits PrivacyPage for 0 axe-core violations', async () => {
    const { container } = render(
      <BrowserRouter>
        <ConsentProvider>
          <PrivacyPage />
        </ConsentProvider>
      </BrowserRouter>
    )

    const results = await axe.run(container, {
      rules: {
        'color-contrast': { enabled: false },
      },
    })

    expect(results.violations).toEqual([])
  })

  it('audits TermsPage for 0 axe-core violations', async () => {
    const { container } = render(
      <BrowserRouter>
        <ConsentProvider>
          <TermsPage />
        </ConsentProvider>
      </BrowserRouter>
    )

    const results = await axe.run(container, {
      rules: {
        'color-contrast': { enabled: false },
      },
    })

    expect(results.violations).toEqual([])
  })

  it('audits NotFoundPage for 0 axe-core violations', async () => {
    const { container } = render(
      <BrowserRouter>
        <ConsentProvider>
          <NotFoundPage />
        </ConsentProvider>
      </BrowserRouter>
    )

    const results = await axe.run(container, {
      rules: {
        'color-contrast': { enabled: false },
      },
    })

    expect(results.violations).toEqual([])
  })
})
