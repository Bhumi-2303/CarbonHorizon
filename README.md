# Carbon Horizon
> Learn Your Impact. Shape the Future.

## Problem Statement
Global carbon literacy is low. Individuals lack accessible, personalized tools to understand their environmental impact and make actionable changes in their daily lives to combat climate change.

## Project Vision
Carbon Horizon is a personal sustainability intelligence platform designed to empower individuals by providing an accurate assessment of their carbon footprint, personalized AI-driven coaching, and tools to track sustainable habits and future impact.

## Competition Vertical
Sustainability & Climate Technology

## Architecture
React + TypeScript frontend → FastAPI backend → PostgreSQL → Gemini AI → Google Cloud Run

```text
+-------------------+       +--------------------+       +-------------------+
|   React + Vite    |       |    FastAPI         |       |    PostgreSQL     |
|   (TypeScript)    | <---> |    Backend         | <---> |    Database       |
+-------------------+       +--------------------+       +-------------------+
                                   ^     ^
                                   |     |
                       +-----------+     +-----------+
                       v                             v
               +---------------+             +----------------+
               |  Gemini AI    |             |  Google Cloud  |
               |  (Coach)      |             |  Run           |
               +---------------+             +----------------+
```

## Security & Privacy Architecture
1. **HTTPS Enforcement Everywhere**:
   - Backend `HTTPSRedirectMiddleware` enforces HTTPS by inspecting `X-Forwarded-Proto` (terminating proxy safe for Cloud Run).
   - Nginx reverse-proxy redirects HTTP to HTTPS when `X-Forwarded-Proto = "http"`.
2. **Security Headers**:
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY` / `frame-ancestors 'none'`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Permissions-Policy: camera=(), microphone=(), geolocation=()`
   - `Content-Security-Policy`: restrictive CSP allowing self, fonts, and consent-gated telemetry.
3. **Session & Cookie Security**:
   - Cookies are `Secure`, `HttpOnly`, and `SameSite=Lax`.
   - Redis-backed JTI blocklist for immediate session revocation upon logout or password change.
4. **Bot Protection & Anti-Abuse (Task 18)**:
   - Cloudflare Turnstile token validation server-side on sensitive routes (`/register`, `/login`, `/coach/chat`).
   - Hidden honeypot fields on all client and server authentication/chat models.
   - Sliding-window login lockout (5 failures in 15 min triggers 15-minute 429 lockout).
   - Per-IP and per-user rate limiting via `slowapi` (`5/minute` on auth, `10/minute` on coach).
5. **Form Validation & Accessibility (Task 17)**:
   - Client-side: Schema validation with Zod + `react-hook-form`, accessible inline errors (`aria-describedby`, `aria-invalid`, `role="alert"`), password strength indicator, and disabled-submit/loading states.
   - Server-side: Strict Pydantic models with bounded ranges (`ge`, `le` on distance, kWh, household size, age), enums for age group/lifestyle, and XSS output sanitization (`sanitize_html_output`) stripping `<script>` and `on*` event handlers from LLM coach responses.
6. **Privacy-Friendly Analytics (Task 19)**:
   - Powered by Plausible Analytics (< 1 KB, zero cookies, no persistent cross-site tracking, 100% anonymized IPs, GDPR & DPDP compliant).
   - Gated by cookie consent (`useConsent()`).
   - **Little Explorer Exemption**: Strictly and permanently disabled for child profiles (`user.age_group === 'child'` or age 4–12).
   - Typed events: `signup_started`, `assessment_completed`, `forecast_viewed`, `habit_logged`, `coach_question_asked`, `cta_clicked`.
   - Never transmits conversation text, passwords, or personal identifying information.
7. **Landing Page Conversion & Clarity (Task 20)**:
   - Single prominent primary CTA: **"Calculate my carbon footprint"** *(Free, takes about 5 minutes)* in the hero and repeated at the bottom.
   - One-line value proposition: *"Measure your environmental footprint and cut emissions with tailored AI coaching."*
   - 3 short benefit points (Regional Precision, Tailored AI Coaching, Privacy-First Design) and trust line (*Free forever • No credit card required • Privacy-first*).

## Carbon Methodology
- Sources: IPCC, EPA, IEA
- Formula: Carbon Emission = Activity Data × Emission Factor
- Example: 100 km car travel × 0.192 kg CO₂e/km = 19.2 kg CO₂e
- All calculations are version-tracked (`calculation_version` + `factor_version` stored per assessment).

## AI Coach Design
- Powered by Google Gemini API proxied server-to-server (browser never touches AI credentials).
- Scope: sustainability topics only — out-of-scope queries are gracefully redirected.
- Personalization: responses adapt to user's age group, city, country, diet, and current footprint.
- Little Explorer mode: cheerful, positive habit guidance completely free of CO₂ terminology and without tracking.

## Environment Variables

### Runtime vs. Build-Time Variables
- **Build-Time (`VITE_*`)**: Injected during `vite build` and baked into the static HTML/JS bundles. In production mode, `VITE_APP_URL` is mandatory; Vite will fail the build if it is missing. In Google Cloud Build, these are supplied via `--build-arg` in `Dockerfile.frontend`.
- **Runtime Variables**: Evaluated dynamically by the server process (FastAPI or Nginx container startup). In production, missing required runtime variables (`SECRET_KEY`, `REDIS_URL`, `ALLOWED_ORIGINS`, `BACKEND_URL`) will cause immediate startup termination.

### Backend Runtime Variables (`backend/.env` / Cloud Run)
| Variable | Description | Required in Production | Default | Notes / Startup Check |
|---|---|---|---|---|
| `ENVIRONMENT` | Environment name | Optional | `production` | If set to `production`, docs/OpenAPI are disabled and strict checks apply. |
| `DATABASE_URL` | PostgreSQL connection string | Yes | - | Must point to Cloud SQL / managed Postgres. |
| `SECRET_KEY` | JWT signing secret key (≥ 32 chars) | **Yes (Refuses startup)** | - | Cannot be default placeholder or empty. |
| `REDIS_URL` | Redis connection URL | **Yes (Refuses startup)** | - | Required for login lockout & token revocation across Cloud Run instances. |
| `ALLOWED_ORIGINS` | Permitted CORS origins | **Yes (Refuses startup)** | `https://carbonhorizon.app` | Refuses startup if containing `localhost`, `127.0.0.1`, or `*` in production. |
| `TURNSTILE_SECRET_KEY` | Cloudflare Turnstile secret key | **Yes (Refuses startup)** | - | Bot verification rejects bypass in production. |
| `GEMINI_API_KEY` | Google Gemini API key for AI Coach | Yes | - | Proxied server-side to prevent browser exposure. |
| `BACKEND_URL` | Nginx reverse-proxy upstream target | **Yes (Nginx startup check)** | - | Validated in container CMD; exits immediately if unset. |

### Frontend Build-Time Variables (`frontend/.env` / Cloud Build `--build-arg`)
| Variable | Description | Required in Production | Default | Notes / Build Check |
|---|---|---|---|---|
| `VITE_APP_URL` | Canonical app URL (e.g. `https://carbonhorizon.app`) | **Yes (Build fails if unset)** | `https://carbonhorizon.app` | Used for sitemaps, canonical tags, and OpenGraph URLs. |
| `VITE_API_URL` | Backend API base path | Optional | `/api/v1` | Relative path proxied by Nginx in production. |
| `VITE_ANALYTICS_DOMAIN` | Plausible Analytics domain | Optional | `carbonhorizon.app` | Used for privacy-friendly telemetry with user consent. |
| `VITE_TURNSTILE_SITE_KEY` | Cloudflare Turnstile public site key | Optional in Dev | `""` | Rendered on auth forms for bot verification. |

## Local Development Setup

### Option 1: Docker Compose (Recommended)
```bash
cp .env.example .env
docker compose up -d
```

### Option 2: Manual Setup

#### 1. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run migrations and seed factors
alembic upgrade head
python -m app.db.init_db

# Run backend development server
uvicorn main:app --reload --port 8000
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Running Tests & Quality Verification

### 1. Link & Route Integrity Check
```bash
node scripts/check-links.mjs
```

### 2. Frontend Tests & Type Checking
```bash
cd frontend
npm run type-check
npm test -- --run
npm run build
```

### 3. Backend Tests & Linting
```bash
cd backend
flake8 app tests main.py
pytest tests/ -v
```

### 4. Secret Scan
```bash
bash scripts/check-secrets.sh
git diff | grep -E "API_KEY|SECRET|TOKEN|PASSWORD|PRIVATE_KEY"
```

## Production Deployment (Google Cloud Run)
1. **Build and push container images**:
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```
2. **Deploy Backend Service**:
   ```bash
   gcloud run deploy carbon-horizon-backend \
     --image gcr.io/PROJECT_ID/carbon-horizon-backend \
     --platform managed \
     --allow-unauthenticated \
     --set-secrets="GEMINI_API_KEY=gemini-key:latest,SECRET_KEY=jwt-secret:latest,DATABASE_URL=db-url:latest"
   ```
3. **Deploy Frontend Service**:
   ```bash
   gcloud run deploy carbon-horizon-frontend \
     --image gcr.io/PROJECT_ID/carbon-horizon-frontend \
     --platform managed \
     --allow-unauthenticated \
     --set-env-vars="BACKEND_URL=https://carbon-horizon-backend-xxx.a.run.app"
   ```

## Definition of Done Verification
- [x] All broken links, dead routes, and invalid anchors resolved (`scripts/check-links.mjs` passed).
- [x] Strict client & server form validation on all inputs (Zod + Pydantic range & enum checks).
- [x] XSS output sanitization on LLM coach responses.
- [x] Bot protection (Turnstile validation, honeypot fields, login lockout, rate limiting).
- [x] Privacy-friendly cookieless analytics (Plausible) gated by `useConsent()`, 0 tracking on child profiles.
- [x] Landing page single primary CTA ("Calculate my carbon footprint") with trust line and 3 benefit points.
- [x] Zero secrets in code, `.env.example` placeholders only, gitleaks CI scanner configured.
- [x] 100% test pass rate across backend pytest (380+ tests) and frontend vitest (29+ tests).

## License
MIT
