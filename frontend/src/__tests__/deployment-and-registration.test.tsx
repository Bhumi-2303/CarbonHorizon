import { describe, it, expect } from 'vitest'
import vercelConfig from '../../vercel.json'
import { resolveApiBaseUrl, extractErrorMessage } from '@/api/client'
import { validateApiUrlAgainstCsp, DEFAULT_CSP_CONNECT_SRC } from '@/utils/csp'

describe('Deployment & Vercel Configuration Checks', () => {
  it('verifies frontend/vercel.json is valid', () => {
    expect(vercelConfig).toBeDefined()
    expect(typeof vercelConfig).toBe('object')
  })

  it('ensures cleanUrls is NOT enabled in vercel.json (prevents SPA /register 404)', () => {
    expect((vercelConfig as any).cleanUrls).toBeUndefined()
  })

  it('ensures SPA catch-all rewrite to /index.html is configured', () => {
    expect(vercelConfig.rewrites).toBeDefined()
    const spaRewrite = vercelConfig.rewrites.find(
      (r: any) => r.source === '/(.*)' && r.destination === '/index.html'
    )
    expect(spaRewrite).toBeDefined()
  })

  it('ensures Vercel CSP connect-src permits onrender.com backend', () => {
    const config = vercelConfig as any
    const rootHeader = config.headers?.find((h: any) => h.source === '/(.*)')
    const cspHeader = rootHeader?.headers?.find((h: any) => h.key === 'Content-Security-Policy')
    expect(cspHeader).toBeDefined()
    expect(cspHeader.value).toContain('https://*.onrender.com')
  })
})

describe('API Client URL & Error Handling', () => {
  it('correctly normalizes API base URLs with resolveApiBaseUrl', () => {
    expect(resolveApiBaseUrl(undefined)).toBe('/api/v1')
    expect(resolveApiBaseUrl('')).toBe('/api/v1')
    expect(resolveApiBaseUrl('   ')).toBe('/api/v1')
    expect(resolveApiBaseUrl('/api/v1')).toBe('/api/v1')
    expect(resolveApiBaseUrl('/api/v1/')).toBe('/api/v1')
    expect(resolveApiBaseUrl('https://api.example.com')).toBe('https://api.example.com/api/v1')
    expect(resolveApiBaseUrl('https://api.example.com/')).toBe('https://api.example.com/api/v1')
    expect(resolveApiBaseUrl('https://api.example.com/api/v1')).toBe('https://api.example.com/api/v1')
    expect(resolveApiBaseUrl('https://api.example.com/api/v1/')).toBe('https://api.example.com/api/v1')
  })

  it('extracts clear backend error messages from envelope', () => {
    const errWithMessage = { response: { status: 400, data: { success: false, message: 'Invalid credentials' } } }
    expect(extractErrorMessage(errWithMessage)).toBe('Invalid credentials')

    const errWithErrorDetail = {
      response: { status: 409, data: { success: false, error: { code: 'CONFLICT', message: 'Email in use' } } },
    }
    expect(extractErrorMessage(errWithErrorDetail)).toBe('Email in use')
  })

  it('safely intercepts Vercel platform 404 message to prevent user confusion', () => {
    const vercel404 = {
      response: {
        status: 404,
        data: { error: { code: 'not_found', message: 'The page could not be found.' } },
      },
    }
    expect(extractErrorMessage(vercel404)).toBe(
      'API endpoint not found (404). Please verify service configuration.'
    )
  })

  it('extracts formatted validation errors from FastAPI detail array', () => {
    const pydanticErr = {
      response: {
        status: 422,
        data: {
          detail: [
            { loc: ['body', 'email'], msg: 'value is not a valid email address' },
            { loc: ['body', 'age'], msg: 'ensure this value is greater than 0' },
          ],
        },
      },
    }
    expect(extractErrorMessage(pydanticErr)).toBe(
      'email: value is not a valid email address, age: ensure this value is greater than 0'
    )
  })

  it('handles network failure cleanly', () => {
    const networkErr = { request: {} }
    expect(extractErrorMessage(networkErr)).toContain('Unable to connect to the server')
  })

  it('handles HTML 404 responses safely without dumping HTML into UI', () => {
    const htmlErr = {
      response: {
        status: 404,
        data: '<!DOCTYPE html><html><head><title>404 Not Found</title></head><body>404</body></html>',
      },
    }
    expect(extractErrorMessage(htmlErr)).toBe(
      'API endpoint not found (404). Please verify service configuration.'
    )
  })
})

describe('CSP Wildcard & Render Origin Support', () => {
  it('permits onrender.com backend origin under DEFAULT_CSP_CONNECT_SRC', () => {
    expect(
      validateApiUrlAgainstCsp(
        'https://carbonhorizon-backend.onrender.com/api/v1',
        DEFAULT_CSP_CONNECT_SRC
      )
    ).toBe(true)
  })

  it('permits any custom onrender subdomain under DEFAULT_CSP_CONNECT_SRC', () => {
    expect(
      validateApiUrlAgainstCsp(
        'https://custom-carbon-api-prod.onrender.com/api/v1',
        DEFAULT_CSP_CONNECT_SRC
      )
    ).toBe(true)
  })

  it('still rejects unauthorized third-party origins', () => {
    expect(
      validateApiUrlAgainstCsp(
        'https://attacker-controlled-host.com/api/v1',
        DEFAULT_CSP_CONNECT_SRC
      )
    ).toBe(false)
  })
})

import { render, screen } from '@testing-library/react'
import { fireEvent, waitFor } from '@testing-library/dom'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '@/context/AuthContext'
import { ConsentProvider } from '@/context/ConsentContext'
import Register from '@/pages/Register'
import { loadGeoDataOnDemand } from '@/services/geoService'

describe('Register Page Location Cascade & Form Validation', () => {
  const renderRegister = () =>
    render(
      <BrowserRouter>
        <AuthProvider>
          <ConsentProvider>
            <Register />
          </ConsentProvider>
        </AuthProvider>
      </BrowserRouter>
    )

  it('initially disables State and City before a country is selected', async () => {
    renderRegister()
    await loadGeoDataOnDemand()

    const countrySelect = screen.getByLabelText(/country/i)
    const stateSelect = screen.getByLabelText(/state \/ province/i)
    const cityField = screen.getByLabelText(/city/i)

    expect(countrySelect).toBeInTheDocument()
    expect(stateSelect).toBeDisabled()
    expect(cityField).toBeDisabled()
  })

  it('enables State dropdown when country is selected, and keeps City disabled until state is selected', async () => {
    renderRegister()
    await loadGeoDataOnDemand()

    const countrySelect = screen.getByLabelText(/country/i) as HTMLSelectElement
    fireEvent.focus(countrySelect)

    await waitFor(() => {
      expect(countrySelect.options.length).toBeGreaterThan(1)
    })

    // Select United States (US)
    fireEvent.change(countrySelect, { target: { value: 'US' } })

    const stateSelect = screen.getByLabelText(/state \/ province/i) as HTMLSelectElement
    expect(stateSelect).not.toBeDisabled()

    const cityField = screen.getByLabelText(/city/i)
    expect(cityField).toBeDisabled()
  })

  it('enables City dropdown when a state with cities is selected', async () => {
    renderRegister()
    await loadGeoDataOnDemand()

    const countrySelect = screen.getByLabelText(/country/i) as HTMLSelectElement
    fireEvent.focus(countrySelect)

    await waitFor(() => {
      expect(countrySelect.options.length).toBeGreaterThan(1)
    })

    fireEvent.change(countrySelect, { target: { value: 'US' } })

    const stateSelect = screen.getByLabelText(/state \/ province/i) as HTMLSelectElement
    // Select California (CA)
    fireEvent.change(stateSelect, { target: { value: 'CA' } })

    const citySelect = screen.getByLabelText(/city/i) as HTMLSelectElement
    expect(citySelect).not.toBeDisabled()
    expect(citySelect.tagName).toBe('SELECT')
    expect(citySelect.options.length).toBeGreaterThan(1)
  })

  it('switches City to text input with helpful message when state has no cities in dataset', async () => {
    renderRegister()
    await loadGeoDataOnDemand()

    const countrySelect = screen.getByLabelText(/country/i) as HTMLSelectElement
    fireEvent.focus(countrySelect)

    await waitFor(() => {
      expect(countrySelect.options.length).toBeGreaterThan(1)
    })

    // Select United Kingdom (GB)
    fireEvent.change(countrySelect, { target: { value: 'GB' } })

    const stateSelect = screen.getByLabelText(/state \/ province/i) as HTMLSelectElement
    // Select Aberdeen (ABE) which has 0 cities in country-state-city
    fireEvent.change(stateSelect, { target: { value: 'ABE' } })

    // City should switch to an accessible input field instead of empty dropdown
    const cityInput = screen.getByLabelText(/city/i) as HTMLInputElement
    expect(cityInput.tagName).toBe('INPUT')
    expect(cityInput).not.toBeDisabled()
    expect(screen.getByText(/no predefined cities for this region/i)).toBeInTheDocument()

    // User can type city and value is captured
    fireEvent.change(cityInput, { target: { value: 'Aberdeen' } })
    expect(cityInput.value).toBe('Aberdeen')
  })

  it('resets dependent state and city selections when country changes', async () => {
    renderRegister()
    await loadGeoDataOnDemand()

    const countrySelect = screen.getByLabelText(/country/i) as HTMLSelectElement
    fireEvent.focus(countrySelect)

    await waitFor(() => {
      expect(countrySelect.options.length).toBeGreaterThan(1)
    })

    // Select US -> CA
    fireEvent.change(countrySelect, { target: { value: 'US' } })
    const stateSelect = screen.getByLabelText(/state \/ province/i) as HTMLSelectElement
    fireEvent.change(stateSelect, { target: { value: 'CA' } })

    expect(stateSelect.value).toBe('CA')

    // Change country to India (IN)
    fireEvent.change(countrySelect, { target: { value: 'IN' } })

    // State should be reset
    expect(stateSelect.value).toBe('')
    const cityField = screen.getByLabelText(/city/i)
    expect(cityField).toBeDisabled()
  })

  it('handles countries with no states (e.g. Puerto Rico) without permanently disabling City', async () => {
    renderRegister()
    await loadGeoDataOnDemand()

    const countrySelect = screen.getByLabelText(/country/i) as HTMLSelectElement
    fireEvent.focus(countrySelect)

    await waitFor(() => {
      expect(countrySelect.options.length).toBeGreaterThan(1)
    })

    // Select Puerto Rico (PR) which has 0 states in ISO dataset
    fireEvent.change(countrySelect, { target: { value: 'PR' } })

    // State select should show Not Applicable
    const stateSelect = screen.getByLabelText(/state \/ province/i) as HTMLSelectElement
    expect(stateSelect.value).toBe('N/A')

    // City should be immediately enabled as an input field
    const cityInput = screen.getByLabelText(/city/i) as HTMLInputElement
    expect(cityInput.tagName).toBe('INPUT')
    expect(cityInput).not.toBeDisabled()

    fireEvent.change(cityInput, { target: { value: 'San Juan' } })
    expect(cityInput.value).toBe('San Juan')
  })
})

