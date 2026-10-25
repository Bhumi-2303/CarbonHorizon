import { describe, it, expect } from 'vitest'
import { validateApiUrlAgainstCsp, DEFAULT_CSP_CONNECT_SRC } from '../utils/csp'

describe('CSP connect-src & VITE_API_URL Build Guards', () => {
  it('permits relative API URL /api/v1 (covered by self)', () => {
    expect(validateApiUrlAgainstCsp('/api/v1', DEFAULT_CSP_CONNECT_SRC)).toBe(true)
    expect(validateApiUrlAgainstCsp('/api/v1/auth/login', DEFAULT_CSP_CONNECT_SRC)).toBe(true)
  })

  it('permits absolute API URL when its origin is explicitly in connect-src', () => {
    const customConnectSrc = [...DEFAULT_CSP_CONNECT_SRC, 'https://api.carbonhorizon.app']
    expect(
      validateApiUrlAgainstCsp('https://api.carbonhorizon.app/api/v1', customConnectSrc)
    ).toBe(true)
  })

  it('rejects absolute API URL when its origin is NOT in connect-src', () => {
    expect(
      validateApiUrlAgainstCsp('https://malicious-or-unconfigured-api.com/v1', DEFAULT_CSP_CONNECT_SRC)
    ).toBe(false)
  })

  it('rejects empty or whitespace-only API URL', () => {
    expect(validateApiUrlAgainstCsp('', DEFAULT_CSP_CONNECT_SRC)).toBe(false)
    expect(validateApiUrlAgainstCsp('   ', DEFAULT_CSP_CONNECT_SRC)).toBe(false)
  })

  it('confirms DEFAULT_CSP_CONNECT_SRC covers self, Cloudflare, and Plausible', () => {
    expect(DEFAULT_CSP_CONNECT_SRC).toContain("'self'")
    expect(DEFAULT_CSP_CONNECT_SRC).toContain('https://challenges.cloudflare.com')
    expect(DEFAULT_CSP_CONNECT_SRC).toContain('https://plausible.io')
  })
})
