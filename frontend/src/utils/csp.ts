/**
 * Content Security Policy (CSP) validation helpers.
 */

export const DEFAULT_CSP_CONNECT_SRC = [
  "'self'",
  'https://challenges.cloudflare.com',
  'https://plausible.io',
  'https://*.onrender.com',
]

/**
 * Validates whether an API URL is covered by the CSP connect-src directives.
 * - Relative paths (e.g. /api/v1) use the same origin ('self') and are always allowed.
 * - Absolute URLs must have their origin explicitly listed in connect-src or covered by a wildcard rule.
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
    const url = new URL(trimmed)
    const origin = url.origin
    if (cspConnectSrc.includes(origin) || cspConnectSrc.includes('*')) {
      return true
    }

    // Check wildcard host entries like https://*.onrender.com
    for (const entry of cspConnectSrc) {
      if (entry.startsWith('https://*.') || entry.startsWith('http://*.')) {
        const protocol = entry.split('://')[0]
        const baseDomain = entry.split('://*.')[1]
        if (
          url.protocol === `${protocol}:` &&
          (url.hostname === baseDomain || url.hostname.endsWith(`.${baseDomain}`))
        ) {
          return true
        }
      }
    }

    return false
  } catch {
    return false
  }
}
