/**
 * Automated Playwright + Axe-Core Accessibility & Contrast Suite.
 *
 * Audits the production build (dist) against WCAG 2.1 AA:
 * Pages (Authenticated):
 *   - Adult: Dashboard, Assessment, Forecast, Habit Tracker, AI Coach, Profile
 *   - Little Explorer (Child): Dashboard, Assessment, Coach
 * Themes: Light, Dark
 * Viewports: 320px (Mobile), 1280px (Desktop)
 *
 * Mocked API responses ensure all authenticated components render their actual content.
 * Prints all axe `incomplete` results per page and fails on any unapproved incomplete
 * color-contrast items or WCAG violations.
 */
import { chromium } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import http from 'http';
import fs from 'fs';
import path from 'path';

const PORT = 4173;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const distDir = path.resolve(process.cwd(), 'dist');

const MIME_TYPES = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2',
  '.ico': 'image/x-icon',
};

function createStaticServer() {
  return http.createServer((req, res) => {
    const urlPath = req.url.split('?')[0];
    let filePath = path.join(distDir, urlPath);

    if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
      const ext = path.extname(filePath);
      res.writeHead(200, {
        'Content-Type': MIME_TYPES[ext] || 'application/octet-stream',
        'Cache-Control': 'no-cache',
      });
      fs.createReadStream(filePath).pipe(res);
    } else {
      // SPA fallback
      const indexPath = path.join(distDir, 'index.html');
      res.writeHead(200, {
        'Content-Type': 'text/html',
        'Cache-Control': 'no-cache',
      });
      fs.createReadStream(indexPath).pipe(res);
    }
  });
}

async function measureNodeContrast(page, targetSelector) {
  try {
    return await page.evaluate((sel) => {
      const el = document.querySelector(sel);
      if (!el) return null;

      function parseRgb(colorStr) {
        if (!colorStr) return null;
        const m = colorStr.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
        if (m) {
          return {
            r: parseInt(m[1], 10),
            g: parseInt(m[2], 10),
            b: parseInt(m[3], 10),
            a: m[4] !== undefined ? parseFloat(m[4]) : 1.0,
          };
        }
        return null;
      }

      function getLuminance(r, g, b) {
        const a = [r, g, b].map((v) => {
          v /= 255;
          return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
        });
        return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
      }

      function getContrast(rgb1, rgb2) {
        const lum1 = getLuminance(rgb1.r, rgb1.g, rgb1.b);
        const lum2 = getLuminance(rgb2.r, rgb2.g, rgb2.b);
        const brightest = Math.max(lum1, lum2);
        const darkest = Math.min(lum1, lum2);
        return (brightest + 0.05) / (darkest + 0.05);
      }

      const cs = window.getComputedStyle(el);
      const fgRgb = parseRgb(cs.color) || { r: 15, g: 23, b: 42, a: 1 };

      // Find background color traversing upwards
      let bgRgb = { r: 255, g: 255, b: 255, a: 1 };
      let bgDesc = 'canvas/surface';
      let curr = el;
      while (curr) {
        const pCs = window.getComputedStyle(curr);
        const parsed = parseRgb(pCs.backgroundColor);
        if (parsed && parsed.a > 0.1) {
          bgRgb = parsed;
          bgDesc = `rgb(${parsed.r}, ${parsed.g}, ${parsed.b})`;
          break;
        }
        if (pCs.backgroundImage && pCs.backgroundImage.includes('linear-gradient')) {
          const isDark = document.documentElement.classList.contains('dark');
          bgRgb = isDark ? { r: 15, g: 23, b: 42, a: 1 } : { r: 240, g: 253, b: 250, a: 1 };
          bgDesc = isDark ? 'dark gradient #0f172a' : 'light gradient #f0fdfa';
          break;
        }
        curr = curr.parentElement;
      }

      const ratio = getContrast(fgRgb, bgRgb);
      const fontSize = parseFloat(cs.fontSize) || 14;
      const isBold = parseInt(cs.fontWeight, 10) >= 700 || cs.fontWeight === 'bold';
      const isLarge = fontSize >= 18 || (fontSize >= 14 && isBold);
      const threshold = isLarge ? 3.0 : 4.5;
      const pass = ratio >= threshold;

      return {
        fg: `rgb(${fgRgb.r}, ${fgRgb.g}, ${fgRgb.b})`,
        bg: bgDesc,
        ratio: ratio.toFixed(2),
        threshold,
        pass,
        text: el.innerText ? el.innerText.trim().slice(0, 30) : '',
      };
    }, targetSelector);
  } catch {
    return null;
  }
}

// Explicitly authorized incomplete contrast selectors approved by the user/design
// (e.g., brand decorative gradients or canvas charts where axe cannot determine text contrast)
const APPROVED_INCOMPLETE_CONTRAST = new Set([
  // Any element specifically approved by user
]);

const PAGES = [
  // Authenticated Adult pages
  { path: '/dashboard', name: 'Dashboard (Adult)', tier: 'adult' },
  { path: '/assessment', name: 'Assessment (Adult)', tier: 'adult' },
  { path: '/forecast', name: 'Forecast (Adult)', tier: 'adult' },
  { path: '/habits', name: 'Habit Tracker (Adult)', tier: 'adult' },
  { path: '/coach', name: 'AI Coach (Adult)', tier: 'adult' },
  { path: '/profile', name: 'Profile (Adult)', tier: 'adult' },

  // Little Explorer pages
  { path: '/dashboard', name: 'Little Explorer Dashboard', tier: 'child' },
  { path: '/assessment', name: 'Little Explorer Assessment', tier: 'child' },
  { path: '/coach', name: 'Little Explorer Coach', tier: 'child' },
];

const THEMES = ['light', 'dark'];
const VIEWPORTS = [
  { width: 320, height: 640, label: '320px (Mobile)' },
  { width: 1280, height: 800, label: '1280px (Desktop)' },
];

async function main() {
  if (!fs.existsSync(path.join(distDir, 'index.html'))) {
    console.error(`dist/index.html not found! Run npm run build first.`);
    process.exit(1);
  }

  const server = createStaticServer();
  await new Promise((resolve) => server.listen(PORT, '127.0.0.1', resolve));
  console.log(`Static server running on ${BASE_URL}\n`);

  let browser;
  const allResults = [];
  let totalViolations = 0;
  let totalContrastIssues = 0;
  let totalIncompleteContrast = 0;
  let totalUnapprovedIncompleteContrast = 0;

  try {
    browser = await chromium.launch({
      headless: true,
      executablePath: '/home/bhumi/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome',
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
    });

    const context = await browser.newContext();

    for (const pageDef of PAGES) {
      for (const theme of THEMES) {
        for (const vp of VIEWPORTS) {
          const page = await context.newPage();
          await page.setViewportSize({ width: vp.width, height: vp.height });

          const isChild = pageDef.tier === 'child';
          const isAuth = true;

          const userProfile = isChild
            ? {
                id: '00000000-0000-0000-0000-000000000002',
                email: 'child@carbonhorizon.app',
                full_name: 'Leo the Explorer',
                age: 8,
                age_group: 'child',
                lifestyle_type: 'student',
                city: 'Seattle',
                country: 'United States',
                created_at: '2026-01-01T00:00:00Z',
              }
            : {
                id: '00000000-0000-0000-0000-000000000001',
                email: 'alex@carbonhorizon.app',
                full_name: 'Alex Rivera',
                age: 28,
                age_group: 'adult',
                lifestyle_type: 'professional',
                city: 'San Francisco',
                country: 'United States',
                created_at: '2026-01-01T00:00:00Z',
              };

          // ── Mock Auth APIs ────────────────────────────────────────────────
          await page.route('**/api/v1/auth/refresh', (route) => {
            route.fulfill({
              status: 200,
              contentType: 'application/json',
              body: JSON.stringify({
                success: true,
                data: {
                  access_token: 'mock-access-token-jwt',
                  refresh_token: 'mock-refresh-token-jwt',
                  expires_in: 3600,
                },
              }),
            });
          });

          await page.route('**/api/v1/auth/profile', (route) => {
            route.fulfill({
              status: 200,
              contentType: 'application/json',
              body: JSON.stringify({ success: true, data: userProfile }),
            });
          });

          await page.route('**/api/v1/users/me**', (route) => {
            route.fulfill({
              status: 200,
              contentType: 'application/json',
              body: JSON.stringify({ success: true, data: userProfile }),
            });
          });

          await page.route('**/api/v1/organization/me**', (route) => {
            route.fulfill({
              status: 200,
              contentType: 'application/json',
              body: JSON.stringify({
                success: true,
                data: { id: 'org-1', name: 'Planet Stewards', tier: 'standard' },
              }),
            });
          });

          // ── Mock Dashboard & Goals APIs ──────────────────────────────────
          await page.route('**/api/v1/dashboard**', (route) => {
            route.fulfill({
              status: 200,
              contentType: 'application/json',
              body: JSON.stringify({
                success: true,
                data: {
                  total_co2: 4.2,
                  target_co2: 3.0,
                  breakdown: { transport: 1.5, housing: 1.2, food: 1.0, secondary: 0.5 },
                  streak_days: 12,
                  points: 340,
                },
              }),
            });
          });

          await page.route('**/api/v1/goals**', (route) => {
            route.fulfill({
              status: 200,
              contentType: 'application/json',
              body: JSON.stringify({ success: true, data: [] }),
            });
          });

          // ── Mock Habits API ───────────────────────────────────────────────
          await page.route('**/api/v1/habits**', (route) => {
            route.fulfill({
              status: 200,
              contentType: 'application/json',
              body: JSON.stringify({
                success: true,
                data: [
                  { id: 'h1', name: 'Cold Shower', category: 'energy', points: 15, logged_today: true },
                  { id: 'h2', name: 'Bike to Work', category: 'transport', points: 30, logged_today: false },
                  { id: 'h3', name: 'Meatless Meal', category: 'food', points: 20, logged_today: true },
                ],
              }),
            });
          });

          // ── Mock Assessment APIs ──────────────────────────────────────────
          await page.route('**/api/v1/assessment/history**', (route) => {
            route.fulfill({
              status: 200,
              contentType: 'application/json',
              body: JSON.stringify({
                success: true,
                data: [
                  {
                    assessment_id: '00000000-0000-0000-0000-000000000010',
                    total_emission: 4.5,
                    transport: 1.5,
                    energy: 1.2,
                    food: 1.0,
                    waste: 0.5,
                    carbon_score: 78,
                    assessment_period: 'monthly',
                    created_at: '2026-10-24T00:00:00Z',
                  },
                ],
              }),
            });
          });

          await page.route('**/api/v1/assessment/**', (route) => {
            route.fulfill({
              status: 200,
              contentType: 'application/json',
              body: JSON.stringify({
                success: true,
                data: {
                  assessment_id: '00000000-0000-0000-0000-000000000010',
                  total_emission: 4.5,
                  transport: 1.5,
                  energy: 1.2,
                  food: 1.0,
                  waste: 0.5,
                  carbon_score: 78,
                  assessment_period: 'monthly',
                  created_at: '2026-10-24T00:00:00Z',
                },
              }),
            });
          });

          // ── Mock Forecast APIs ────────────────────────────────────────────
          await page.route('**/api/v1/forecast/history**', (route) => {
            route.fulfill({
              status: 200,
              contentType: 'application/json',
              body: JSON.stringify({
                success: true,
                data: [
                  {
                    id: 'fc-1',
                    forecast_type: 'recommended_path',
                    point_count: 6,
                    created_at: '2026-10-24T00:00:00Z',
                  },
                ],
              }),
            });
          });

          await page.route('**/api/v1/forecast/**', (route) => {
            route.fulfill({
              status: 200,
              contentType: 'application/json',
              body: JSON.stringify({
                success: true,
                data: {
                  id: 'fc-1',
                  forecast_type: 'recommended_path',
                  created_at: '2026-10-24T00:00:00Z',
                  updated_at: '2026-10-24T00:00:00Z',
                  forecast_points: [
                    { id: 'p1', month_offset: 1, predicted_emission: 4.2, created_at: '2026-10-24T00:00:00Z' },
                    { id: 'p2', month_offset: 2, predicted_emission: 3.9, created_at: '2026-10-24T00:00:00Z' },
                    { id: 'p3', month_offset: 3, predicted_emission: 3.6, created_at: '2026-10-24T00:00:00Z' },
                    { id: 'p4', month_offset: 4, predicted_emission: 3.4, created_at: '2026-10-24T00:00:00Z' },
                    { id: 'p5', month_offset: 5, predicted_emission: 3.2, created_at: '2026-10-24T00:00:00Z' },
                    { id: 'p6', month_offset: 6, predicted_emission: 3.0, created_at: '2026-10-24T00:00:00Z' },
                  ],
                },
              }),
            });
          });

          // ── Mock AI Coach APIs ────────────────────────────────────────────
          await page.route('**/api/v1/coach/history**', (route) => {
            route.fulfill({
              status: 200,
              contentType: 'application/json',
              body: JSON.stringify({
                success: true,
                data: {
                  conversation_id: '00000000-0000-0000-0000-000000000001',
                  history: [
                    {
                      id: 'm1',
                      role: 'assistant',
                      message: 'Hello! I am your AI Carbon Coach. Let us explore ways to lower your carbon footprint!',
                      created_at: '2026-10-24T00:00:00Z',
                    },
                  ],
                },
              }),
            });
          });

          await page.route('**/api/v1/coach/chat**', (route) => {
            route.fulfill({
              status: 200,
              contentType: 'application/json',
              body: JSON.stringify({
                success: true,
                data: {
                  conversation_id: '00000000-0000-0000-0000-000000000001',
                  message: 'Keep up the good work! Small daily changes accumulate to large carbon savings.',
                },
              }),
            });
          });

          // ── Set Theme, Auth State, and Consent ────────────────────────────
          await page.addInitScript(
            ({ th, auth }) => {
              window.localStorage.setItem('ch_theme', th);
              window.localStorage.setItem(
                'carbon_horizon_cookie_consent',
                JSON.stringify({
                  analytics: true,
                  preferences: true,
                  version: '2026-v1',
                  timestamp: new Date().toISOString(),
                })
              );
              if (auth) {
                window.localStorage.setItem('refreshToken', 'mock-valid-refresh-token');
              } else {
                window.localStorage.removeItem('refreshToken');
              }
              const root = document.documentElement;
              root.classList.remove('light', 'dark', 'high-contrast');
              root.classList.add(th);
            },
            { th: theme, auth: isAuth }
          );

          const fullUrl = `${BASE_URL}${pageDef.path}`;
          await page.goto(fullUrl, { waitUntil: 'domcontentloaded' });
          await page.waitForTimeout(600); // allow UI and charts to render

          // Run axe accessibility analysis
          const axeResults = await new AxeBuilder({ page })
            .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
            .analyze();

          const violations = axeResults.violations || [];
          const incomplete = axeResults.incomplete || [];

          const contrastViolations = violations.filter((v) => v.id === 'color-contrast');
          const contrastIncomplete = incomplete.filter((v) => v.id === 'color-contrast');

          // Check if any incomplete contrast node is NOT in the approved whitelist
          const unapprovedIncompleteContrast = contrastIncomplete.filter((inc) => {
            const hasUnapprovedNode = inc.nodes.some((node) => {
              const targetStr = node.target.join(' ');
              return !APPROVED_INCOMPLETE_CONTRAST.has(targetStr);
            });
            return hasUnapprovedNode;
          });

          totalViolations += violations.length;
          totalContrastIssues += contrastViolations.length;
          totalIncompleteContrast += contrastIncomplete.length;
          totalUnapprovedIncompleteContrast += unapprovedIncompleteContrast.length;

          const testCase = {
            page: pageDef.name,
            path: pageDef.path,
            tier: pageDef.tier,
            theme,
            viewport: vp.label,
            totalViolations: violations.length,
            contrastViolations: contrastViolations.length,
            incompleteCount: incomplete.length,
            incompleteContrastCount: contrastIncomplete.length,
            unapprovedIncompleteContrast: unapprovedIncompleteContrast.length,
          };

          allResults.push(testCase);

          const isPassed = violations.length === 0 && unapprovedIncompleteContrast.length === 0;
          const passStatus = isPassed
            ? '✓ PASS'
            : `✗ FAIL (${violations.length} v, ${unapprovedIncompleteContrast.length} unapproved inc contrast)`;

          console.log(
            `[${passStatus}] ${pageDef.name.padEnd(28)} | Theme: ${theme.padEnd(5)} | Viewport: ${vp.label.padEnd(16)} | Incomplete: ${incomplete.length} (Contrast: ${contrastIncomplete.length})`
          );

          // Always print axe incomplete results per page
          if (incomplete.length > 0) {
            console.log(`    ── Incomplete Checks (${incomplete.length} rules):`);
            for (const inc of incomplete) {
              const isContrast = inc.id === 'color-contrast';
              const prefix = isContrast ? '⚠️ [CONTRAST INCOMPLETE]' : 'ℹ️ [INCOMPLETE]';
              console.log(`       ${prefix} ${inc.id}: ${inc.description} (${inc.nodes.length} nodes)`);
              for (const node of inc.nodes.slice(0, 3)) {
                console.log(`          target: ${node.target.join(' ')}`);
                console.log(`          html:   ${node.html.slice(0, 90)}...`);
                if (isContrast) {
                  const measured = await measureNodeContrast(page, node.target[0]);
                  if (measured) {
                    const statusIcon = measured.pass ? '✓ PASS' : '✗ FAIL';
                    console.log(
                      `          measured: FG: ${measured.fg} on BG: ${measured.bg} -> Ratio: ${measured.ratio}:1 (WCAG AA min ${measured.threshold}:1) [${statusIcon}]`
                    );
                  }
                }
              }
            }
          }

          if (violations.length > 0) {
            console.log(`    ── Violations (${violations.length} rules):`);
            for (const v of violations) {
              console.log(`       ✗ [VIOLATION: ${v.impact || 'info'}] ${v.id}: ${v.description} (${v.nodes.length} nodes)`);
              for (const node of v.nodes.slice(0, 3)) {
                console.log(`          target: ${node.target.join(' ')}`);
                console.log(`          html:   ${node.html.slice(0, 90)}...`);
              }
            }
          }

          await page.close();
        }
      }
    }

    console.log('\n======================================================');
    console.log('   PLAYWRIGHT + AXE-CORE AUDIT SUMMARY');
    console.log('======================================================');
    console.log(`Total Page Scenarios Tested:              ${allResults.length}`);
    console.log(`Total WCAG AA Violations:                ${totalViolations}`);
    console.log(`Total Color Contrast Violations:         ${totalContrastIssues}`);
    console.log(`Total Incomplete Contrast Checks:        ${totalIncompleteContrast}`);
    console.log(`Total Unapproved Incomplete Contrast:    ${totalUnapprovedIncompleteContrast}`);
    console.log('======================================================\n');

    if (totalViolations > 0 || totalUnapprovedIncompleteContrast > 0) {
      console.error(
        `Audit failed: ${totalViolations} violations, ${totalUnapprovedIncompleteContrast} unapproved incomplete color-contrast items.`
      );
      process.exit(1);
    } else {
      console.log('All authenticated page scenarios passed WCAG 2.1 AA with zero violations and zero unapproved incomplete contrast items!');
    }
  } finally {
    if (browser) await browser.close();
    server.close();
  }
}

main().catch((err) => {
  console.error('Fatal audit failure:', err);
  process.exit(1);
});
