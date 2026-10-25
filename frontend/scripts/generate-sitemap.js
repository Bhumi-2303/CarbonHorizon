#!/usr/bin/env node
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const ROOT_DIR = path.resolve(__dirname, '..')
const PUBLIC_DIR = path.resolve(ROOT_DIR, 'public')

const BASE_URL = (process.env.VITE_APP_URL || 'https://carbonhorizon.app').replace(/\/$/, '')
const TODAY = new Date().toISOString().split('T')[0]

export const SITEMAP_ROUTES = [
  { path: '/', changefreq: 'daily', priority: '1.0' },
  { path: '/privacy', changefreq: 'monthly', priority: '0.5' },
  { path: '/terms', changefreq: 'monthly', priority: '0.5' },
  { path: '/login', changefreq: 'monthly', priority: '0.8' },
  { path: '/register', changefreq: 'monthly', priority: '0.9' },
]

export function generateSitemapXml(baseUrl = BASE_URL, routes = SITEMAP_ROUTES) {
  const cleanBase = baseUrl.replace(/\/$/, '')
  const urls = routes
    .map(
      (r) => `  <url>
    <loc>${cleanBase}${r.path === '/' ? '/' : r.path}</loc>
    <lastmod>${TODAY}</lastmod>
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

export function generateRobotsTxt(baseUrl = BASE_URL) {
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

function main() {
  if (!fs.existsSync(PUBLIC_DIR)) {
    fs.mkdirSync(PUBLIC_DIR, { recursive: true })
  }

  const sitemapPath = path.join(PUBLIC_DIR, 'sitemap.xml')
  const robotsPath = path.join(PUBLIC_DIR, 'robots.txt')

  fs.writeFileSync(sitemapPath, generateSitemapXml(BASE_URL), 'utf-8')
  fs.writeFileSync(robotsPath, generateRobotsTxt(BASE_URL), 'utf-8')

  console.log(`Generated: ${sitemapPath}`)
  console.log(`Generated: ${robotsPath}`)
}

if (process.argv[1] === __filename) {
  main()
}
