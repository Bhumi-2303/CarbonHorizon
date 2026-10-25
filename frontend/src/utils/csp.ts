/**
 * Content Security Policy (CSP) validation helpers.
 */

export const DEFAULT_CSP_CONNECT_SRC = [
  "'self'",
  'https://challenges.cloudflare.com',
  'https://plausible.io',
]

/**
 * Validates whether an API URL is covered by the CSP connect-src directives.
 * - Relative paths (e.g. /api/v1) use the same origin ('self') and are always allowed.
 * - Absolute URLs must have their origin explicitly listed in connect-src.
 */
export function validateApiUrlAgainstCsp(
  apiUrl: string,
  cspConnectSrc: string[] = DEFAULT_CSP_CONNECT_SRC
): boolean {
  if (!apiUrl || !apiUrl.trim()) return false
  const trimmed = apiUrl.trim()
  if (trimmed.startsWith('/') || trimmed.startsWith('.')) {
    return true
  }
  try {
    const origin = new URL(trimmed).origin
    return cspConnectSrc.includes(origin) || cspConnectSrc.includes('*')
  } catch {
    return false
  }
}
