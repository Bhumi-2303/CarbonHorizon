import { PUBLIC_ROUTES, PublicRouteEntry } from './seo'

export const SITEMAP_ROUTES: readonly PublicRouteEntry[] = PUBLIC_ROUTES

export function generateSitemapXml(baseUrl: string, routes: readonly PublicRouteEntry[] = SITEMAP_ROUTES): string {
  const cleanBase = baseUrl.replace(/\/$/, '')
  const today = new Date().toISOString().split('T')[0]

  const urls = routes
    .map(
      (r) => `  <url>
    <loc>${cleanBase}${r.path === '/' ? '/' : r.path}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>${r.changefreq}</changefreq>
    <priority>${r.priority}</priority>
  </url>`
    )
    .join('\n')

  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls}
</urlset>
`
}

export function generateRobotsTxt(baseUrl: string): string {
  const cleanBase = baseUrl.replace(/\/$/, '')
  return `# https://www.robotstxt.org/robotstxt.html
User-agent: *
Allow: /
Allow: /privacy
Allow: /terms
Allow: /login
Allow: /register

# Disallow authenticated application areas and backend API
Disallow: /api/
Disallow: /dashboard
Disallow: /assessment
Disallow: /coach
Disallow: /emissions
Disallow: /reports
Disallow: /journey
Disallow: /profile
Disallow: /settings
Disallow: /goals
Disallow: /habits
Disallow: /simulator
Disallow: /forecast
Disallow: /organization

Sitemap: ${cleanBase}/sitemap.xml
`
}
