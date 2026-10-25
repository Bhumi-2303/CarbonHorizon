import { describe, it, expect } from 'vitest'
import { SITEMAP_ROUTES, generateSitemapXml, generateRobotsTxt } from '@/config/sitemap'
import { PUBLIC_ROUTES, PublicRouteEntry } from '@/config/seo'

// Registered public routes in App.tsx
const KNOWN_APP_ROUTES = new Set([
  '/',
  '/login',
  '/register',
  '/privacy',
  '/terms',
])

describe('Sitemap & Robots Generator (Task 9)', () => {
  it('ensures every sitemap route maps to a real registered route in the app', () => {
    for (const route of SITEMAP_ROUTES) {
      expect(KNOWN_APP_ROUTES.has(route.path)).toBe(true)
    }
  })

  it('matches PUBLIC_ROUTES definition in seo.ts', () => {
    const sitemapPaths = SITEMAP_ROUTES.map((r: PublicRouteEntry) => r.path).sort()
    const seoPaths = PUBLIC_ROUTES.map((r: PublicRouteEntry) => r.path).sort()
    expect(sitemapPaths).toEqual(seoPaths)
  })

  it('generates valid sitemap XML containing only public routes with lastmod and changefreq', () => {
    const xml = generateSitemapXml('https://carbonhorizon.app')
    expect(xml).toContain('<loc>https://carbonhorizon.app/</loc>')
    expect(xml).toContain('<loc>https://carbonhorizon.app/privacy</loc>')
    expect(xml).toContain('<loc>https://carbonhorizon.app/terms</loc>')
    expect(xml).toContain('<loc>https://carbonhorizon.app/login</loc>')
    expect(xml).toContain('<loc>https://carbonhorizon.app/register</loc>')
    expect(xml).toContain('<lastmod>')
    expect(xml).toContain('<changefreq>')

    // Must never contain authenticated routes
    expect(xml).not.toContain('/dashboard')
    expect(xml).not.toContain('/api')
    expect(xml).not.toContain('/settings')
  })

  it('generates robots.txt that allows public routes and disallows auth and api', () => {
    const robots = generateRobotsTxt('https://carbonhorizon.app')
    expect(robots).toContain('Allow: /')
    expect(robots).toContain('Allow: /privacy')
    expect(robots).toContain('Allow: /terms')
    expect(robots).toContain('Disallow: /api/')
    expect(robots).toContain('Disallow: /dashboard')
    expect(robots).toContain('Sitemap: https://carbonhorizon.app/sitemap.xml')
  })
})
