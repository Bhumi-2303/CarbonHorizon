#!/usr/bin/env node
/**
 * scripts/check-links.mjs
 *
 * Comprehensive link, route, anchor, import, and asset integrity checker for Carbon Horizon.
 * Verifies:
 * 1. Internal React Router routes (Links, NavLinks, navigate() calls).
 * 2. In-page anchor targets (#id exists in target page/component).
 * 3. Placeholder href prohibition (#, javascript:void(0)).
 * 4. External links and target="_blank" use rel="noopener noreferrer".
 * 5. Dead imports across frontend/src (relative and @/ alias).
 * 6. Missing static asset references (public/ icons, images, favicons).
 */

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const ROOT_DIR = path.resolve(__dirname, '..')
const FRONTEND_DIR = path.resolve(ROOT_DIR, 'frontend')
const SRC_DIR = path.resolve(FRONTEND_DIR, 'src')
const PUBLIC_DIR = path.resolve(FRONTEND_DIR, 'public')

const REGISTERED_ROUTES = [
  '/',
  '/login',
  '/register',
  '/privacy',
  '/terms',
  '/dashboard',
  '/assessment',
  '/assessment/history',
  '/assessment/history/:id',
  '/assessment/result',
  '/simulator',
  '/simulator/history',
  '/forecast',
  '/profile',
  '/settings',
  '/coach',
  '/goals',
  '/habits',
  '/journey',
  '/emissions',
  '/reports',
  '/organization',
]

function routeMatches(targetPath, registeredRoutes = REGISTERED_ROUTES) {
  const clean = targetPath.split('?')[0].split('#')[0]
  if (registeredRoutes.includes(clean)) return true

  for (const r of registeredRoutes) {
    if (r.includes(':')) {
      const regexPattern = '^' + r.replace(/:[a-zA-Z0-9_]+/g, '[^/]+') + '$'
      if (new RegExp(regexPattern).test(clean)) {
        return true
      }
    }
  }
  return false
}

function getAllFiles(dir, extensions = ['.ts', '.tsx', '.html', '.css']) {
  let results = []
  if (!fs.existsSync(dir)) return results

  const entries = fs.readdirSync(dir, { withFileTypes: true })
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      if (['node_modules', 'dist', '.git', '.venv'].includes(entry.name)) continue
      results = results.concat(getAllFiles(fullPath, extensions))
    } else if (entry.isFile()) {
      if (extensions.some((ext) => entry.name.endsWith(ext))) {
        results.push(fullPath)
      }
    }
  }
  return results
}

function getLineNumber(content, index) {
  return content.substring(0, index).split('\n').length
}

export function runLinkCheck() {
  const issues = []
  const files = getAllFiles(SRC_DIR)
  const htmlFiles = getAllFiles(FRONTEND_DIR, ['.html'])
  const allFiles = [...files, ...htmlFiles]

  // Pre-load all contents for fast anchor lookup
  const fileContents = allFiles.map((f) => ({
    file: f,
    relFile: path.relative(ROOT_DIR, f),
    content: fs.readFileSync(f, 'utf-8'),
  }))

  for (const { relFile, content } of fileContents) {
    // 1. Check all <a ...> and <Link ...> tags (multi-line aware)
    const tagRegex = /<(?:a|Link|NavLink)\b([^>]*?)>/gis
    let tagMatch
    while ((tagMatch = tagRegex.exec(content)) !== null) {
      const tagAttrs = tagMatch[1]
      const lineNum = getLineNumber(content, tagMatch.index)

      // A. Disallow placeholder hrefs like "#", "javascript:void(0)"
      const placeholderMatch = tagAttrs.match(/href\s*=\s*["'](#|javascript:void\(0\)|javascript:;)["']/i)
      if (placeholderMatch) {
        issues.push({
          type: 'PLACEHOLDER_HREF',
          file: relFile,
          line: lineNum,
          detail: `Found forbidden placeholder href: "${placeholderMatch[1]}"`,
        })
      }

      // B. External link or target="_blank" must have rel="noopener noreferrer"
      if (/target\s*=\s*["']_blank["']/i.test(tagAttrs)) {
        const hasRel = /rel\s*=\s*["'][^"']*(?:noopener|noreferrer)[^"']*["']/i.test(tagAttrs)
        if (!hasRel) {
          issues.push({
            type: 'MISSING_REL_NOOPENER',
            file: relFile,
            line: lineNum,
            detail: `Link with target="_blank" lacks rel="noopener noreferrer" attribute`,
          })
        }
      }

      // C. In-page anchors e.g. href="#about"
      const anchorMatch = tagAttrs.match(/href\s*=\s*["']#([a-zA-Z0-9_-]+)["']/i)
      if (anchorMatch) {
        const anchorId = anchorMatch[1]
        const idRegex = new RegExp(`id\\s*=\\s*["']${anchorId}["']`, 'i')
        const foundGlobally = fileContents.some((fc) => idRegex.test(fc.content))
        if (!foundGlobally) {
          issues.push({
            type: 'BROKEN_ANCHOR',
            file: relFile,
            line: lineNum,
            detail: `In-page anchor #${anchorId} does not match any element with id="${anchorId}"`,
          })
        }
      }

      // D. Internal route checking in to="..."
      const toMatch = tagAttrs.match(/\bto\s*=\s*["'](\/[^"'?#]*)["']/i)
      if (toMatch) {
        const routePath = toMatch[1]
        if (!routeMatches(routePath)) {
          issues.push({
            type: 'BROKEN_INTERNAL_ROUTE',
            file: relFile,
            line: lineNum,
            detail: `Target route "${routePath}" is not registered in App.tsx`,
          })
        }
      }
    }

    // 2. Check navigate() calls
    const navigateRegex = /navigate\(\s*["'](\/[^"'?#]*)["']/g
    let navMatch
    while ((navMatch = navigateRegex.exec(content)) !== null) {
      const routePath = navMatch[1]
      const lineNum = getLineNumber(content, navMatch.index)
      if (!routeMatches(routePath)) {
        issues.push({
          type: 'BROKEN_INTERNAL_ROUTE',
          file: relFile,
          line: lineNum,
          detail: `navigate("${routePath}") target is not registered in App.tsx`,
        })
      }
    }

    // 3. Static Assets Validation in src/href
    const assetRegex = /(?:src|href)\s*=\s*['"](\/[^'"]+\.(?:svg|png|jpg|jpeg|webp|ico|css|js))['"]/g
    let assetMatch
    while ((assetMatch = assetRegex.exec(content)) !== null) {
      const assetPath = assetMatch[1].slice(1)
      const lineNum = getLineNumber(content, assetMatch.index)
      const inPublic = path.resolve(PUBLIC_DIR, assetPath)
      const inFrontend = path.resolve(FRONTEND_DIR, assetPath)

      if (!fs.existsSync(inPublic) && !fs.existsSync(inFrontend)) {
        issues.push({
          type: 'MISSING_ASSET',
          file: relFile,
          line: lineNum,
          detail: `Referenced static asset "/${assetPath}" was not found in public/ or frontend/`,
        })
      }
    }
  }

  // 4. Dead Imports Validation across frontend/src
  const importRegex = /(?:import|from)\s+['"]([^'"]+)['"]/g
  for (const { file, relFile, content } of fileContents) {
    if (!file.endsWith('.ts') && !file.endsWith('.tsx')) continue

    let match
    while ((match = importRegex.exec(content)) !== null) {
      const spec = match[1]
      let resolvedPath = null

      if (spec.startsWith('.')) {
        resolvedPath = path.resolve(path.dirname(file), spec)
      } else if (spec.startsWith('@/')) {
        resolvedPath = path.resolve(SRC_DIR, spec.slice(2))
      }

      if (resolvedPath) {
        const candidateExtensions = ['', '.ts', '.tsx', '.d.ts', '.json', '/index.ts', '/index.tsx']
        const exists = candidateExtensions.some((ext) => {
          const p = resolvedPath + ext
          return fs.existsSync(p) && fs.statSync(p).isFile()
        })
        if (!exists) {
          issues.push({
            type: 'DEAD_IMPORT',
            file: relFile,
            detail: `Cannot resolve import "${spec}" -> target does not exist on disk`,
          })
        }
      }
    }
  }

  return issues
}

function main() {
  console.log('🔍 Running Carbon Horizon Link, Route, Anchor & Asset Integrity Check...')
  const issues = runLinkCheck()

  if (issues.length > 0) {
    console.error(`\n❌ Found ${issues.length} issue(s):`)
    issues.forEach((iss, idx) => {
      console.error(
        `  ${idx + 1}. [${iss.type}] ${iss.file}${iss.line ? `:${iss.line}` : ''} - ${iss.detail}`
      )
    })
    process.exit(1)
  }

  console.log('✅ All internal routes, anchors, external links, imports, and assets are valid!')
}

if (process.argv[1] === __filename) {
  main()
}
