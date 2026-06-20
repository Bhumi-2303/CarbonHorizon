# CarbonHorizon — Repository Audit

> Generated 2026-06-19. Read-only audit — no code was modified.

---

## 1. Frontend Stack

| Aspect | Detail |
|---|---|
| **Framework** | React 18.3 + TypeScript 5.6 |
| **Bundler** | Vite 5.4 (`@vitejs/plugin-react`) |
| **Routing** | `react-router-dom` 6.26 (BrowserRouter) |
| **State Management** | Redux Toolkit 2.3 (`@reduxjs/toolkit` + `react-redux` 9.1) — **4 slices exist but are all stubs** with empty reducers and TODO comments. Real auth state lives in `AuthContext`. |
| **Forms** | `react-hook-form` 7.78 + `zod` 4.4 + `@hookform/resolvers` 5.4 |
| **HTTP Client** | `axios` 1.7 (single instance in `src/api/client.ts`, baseURL `VITE_API_URL \|\| '/api/v1'`, 15 s timeout) |
| **Styling** | **TailwindCSS 3.4** + PostCSS + Autoprefixer. Dark-mode strategy: `class`. |
| **Icons** | `lucide-react` 1.21 + Tabler Icons webfont (CDN in `index.html`) |
| **Markdown** | `react-markdown` 10.1 (used in AI Coach) |

### Global Theme / Colors

Defined in two places:

1. **CSS custom properties** — [`frontend/src/index.css`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/index.css) (`:root` block)
   - `--color-bg-primary: #08121E`, `--color-bg-card: #0F172A`
   - `--color-green-primary: #2ECC71`, `--color-green-forest: #1B5E20`, `--color-green-accent: #A3E635`
   - `--color-success: #22C55E`, `--color-warning: #F59E0B`, `--color-danger: #EF4444`

2. **Tailwind config** — [`frontend/tailwind.config.js`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/tailwind.config.js)
   - Custom colors: `space-black`, `deep-ocean`, `earth-green`, `forest-green`, `eco-lime`, `muted`
   - Full custom `emerald` HSL scale (50–950), extra `slate-850` / `slate-950`
   - Fonts: **Inter** (body), **Poppins** (headings, 600/700), **Montserrat** (metrics/numbers, 600)

3. **ThemeContext** — [`frontend/src/context/ThemeContext.tsx`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/context/ThemeContext.tsx)
   - Supports `'light' | 'dark' | 'system'`; persisted in `localStorage` key `ch_theme`, defaults to `'dark'`

### Component-level CSS classes (index.css)

`.glass-surface`, `.glass-card` (glassmorphism), `.gradient-text`, `.btn-primary`, `.btn-outline`, `.heading-xl/lg/md`, `.metric`, `.body`. Custom scrollbar, autofill override for dark BG, skip-to-content link, `focus-visible` ring.

---

## 2. Backend Stack

| Aspect | Detail |
|---|---|
| **Framework** | FastAPI 0.136 (Starlette 1.2, Uvicorn 0.49) |
| **Database** | PostgreSQL (default URL `postgresql://postgres:password@localhost:5432/carbonhorizon`). A local `carbonhorizon.db` SQLite file also exists in `/backend/`. |
| **ORM** | SQLAlchemy 2.0.50 (mapped_column / Mapped style). Sync engine with `QueuePool`, pool_size=10. |
| **Migrations** | Alembic 1.18 (config in [`backend/alembic.ini`](file:///home/bhumi/GitHub/CarbonHorizon/backend/alembic.ini)) |
| **Schema/Validation** | Pydantic 2.13 + pydantic-settings 2.14 |
| **Auth** | `bcrypt` 5.0 (direct, not passlib), `python-jose` 3.5 (HS256 JWT) |
| **AI** | `google-genai` 0.3.0 (Google Gemini) |
| **Rate Limiting** | `slowapi` 0.1.9 |
| **Settings** | [`backend/app/core/config.py`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/core/config.py) — Pydantic `BaseSettings` loading from env / `.env` file |

### ORM Model files

All in [`backend/app/models/`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/models):

| Model | File | Table |
|---|---|---|
| `User` | `user.py` | `users` |
| `UserPreferences` | `user_preferences.py` | `user_preferences` |
| `CarbonAssessment` | `carbon_assessment.py` | `carbon_assessments` |
| `EmissionInputs` | `emission_inputs.py` | `emission_inputs` |
| `CarbonFactor` | `carbon_factor.py` | `carbon_factors` |
| `Goal` | `goal.py` | `goals` |
| `Simulation` | `simulation.py` | `simulations` |
| `Forecast` | `forecast.py` | `forecasts` |
| `ForecastPoint` | `forecast_point.py` | `forecast_points` |
| `Habit` | `habit.py` | `habits` |
| `HabitDefinition` | `habit_definition.py` | `habit_definitions` |
| `AIConversation` | `ai_conversation.py` | `ai_conversations` |

---

## 3. Current User / Profile Schema

### User model ([`backend/app/models/user.py`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/models/user.py))

| Column | Type | Constraints |
|---|---|---|
| `id` | `UUID` | PK, default `uuid4` |
| `full_name` | `String(100)` | NOT NULL |
| `email` | `String(255)` | UNIQUE, NOT NULL, indexed |
| `password_hash` | `String(255)` | NOT NULL |
| `age_group` | `String(20)` | Nullable. Enum: `child / student / adult / senior` |
| `lifestyle_type` | `String(20)` | Nullable. Enum: `student / professional / homemaker / retired` |
| `city` | `String(100)` | Nullable |
| `country` | `String(100)` | Nullable, indexed |
| `email_verified` | `Boolean` | NOT NULL, default `False` |
| `last_login` | `DateTime(tz)` | Nullable |
| `created_at` | `DateTime(tz)` | NOT NULL, server_default=now() (TimestampMixin) |
| `updated_at` | `DateTime(tz)` | NOT NULL, server_default=now(), onupdate=now() (TimestampMixin) |
| `deleted_at` | `DateTime(tz)` | Nullable, indexed (SoftDeleteMixin) |

> **Note:** There is no `occupation` field. The closest are `age_group` and `lifestyle_type`.

### UserPreferences model ([`backend/app/models/user_preferences.py`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/models/user_preferences.py))

| Column | Type | Default |
|---|---|---|
| `id` | `UUID` | PK |
| `user_id` | `UUID` | FK → users.id, UNIQUE (1:1) |
| `theme` | `String(10)` | `'system'` (light/dark/system) |
| `language` | `String(20)` | `'en'` |
| `notifications_enabled` | `Boolean` | `True` |
| `measurement_unit` | `String(10)` | `'metric'` (metric/imperial) |

### Pydantic schemas ([`backend/app/schemas/user.py`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/schemas/user.py), [`auth.py`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/schemas/auth.py))

- `RegisterRequest`: full_name, email, password (min 8, not all digits), age_group?, lifestyle_type?, city?, country?
- `ProfileResponse`: id, full_name, email, age_group, lifestyle_type, city, country, email_verified, last_login, created_at, updated_at
- `TokenResponse`: access_token, refresh_token, token_type="bearer", expires_in=1800

---

## 4. Authentication Flow

### Files involved

| Layer | File |
|---|---|
| **Backend routes** | [`backend/app/routes/auth.py`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/routes/auth.py) |
| **Backend service** | [`backend/app/services/auth_service.py`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/services/auth_service.py) |
| **Backend security** | [`backend/app/core/security.py`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/core/security.py) |
| **Backend dependencies** | [`backend/app/core/dependencies.py`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/core/dependencies.py) |
| **Backend schemas** | [`backend/app/schemas/auth.py`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/schemas/auth.py) |
| **Frontend context** | [`frontend/src/context/AuthContext.tsx`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/context/AuthContext.tsx) |
| **Frontend API** | [`frontend/src/api/auth.ts`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/api/auth.ts) |
| **Frontend client** | [`frontend/src/api/client.ts`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/api/client.ts) |
| **Login page** | [`frontend/src/pages/Login.tsx`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/pages/Login.tsx) |
| **Register page** | [`frontend/src/pages/Register.tsx`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/pages/Register.tsx) |
| **Route guard** | [`frontend/src/components/ProtectedRoute.tsx`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/components/ProtectedRoute.tsx) |

### Flow summary

1. **Registration** (`POST /api/v1/auth/register`): validates email uniqueness (case-insensitive), hashes password with `bcrypt.hashpw`, creates User with `email_verified=False`. Returns profile (no tokens).
2. **Login** (`POST /api/v1/auth/login`, rate-limited 5/min): verifies password with `bcrypt.checkpw`, stamps `last_login`, returns `TokenResponse` with JWT access (30 min) + refresh (7 days) tokens signed with HS256.
3. **Frontend auto-login after register**: Register page calls register → login → stores tokens in React state (no localStorage for tokens — XSS mitigation).
4. **Axios interceptor**: reads `accessTokenRef.current` and sets `Authorization: Bearer <token>` on every request.
5. **Auto-refresh**: `setTimeout` at `(expires_in - 60)s` → `POST /api/v1/auth/refresh` → new token pair.
6. **Logout**: Stateless (204 No Content). Client clears timer + state. No server-side token blocklist (TODO noted in code).
7. **Protected routes**: `ProtectedRoute` checks `isAuthenticated` from `useAuth()`. Unauthenticated → redirect to `/login` with `state.from` for post-login redirect.

---

## 5. Carbon Assessment Flow

### Where questions are defined

- **Frontend**: [`frontend/src/pages/AssessmentForm.tsx`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/pages/AssessmentForm.tsx) — 4-step wizard with hardcoded emission factors in-component:

| Step | Fields |
|---|---|
| **1. Transport** | `transport_mode` (car/motorcycle/bus/train/flight/bicycle), `distance_km` (0–100,000) |
| **2. Energy** | `electricity_kwh` (0–10,000), `ac_hours` (0–744), `lpg_usage` (0–500 kg), `solar_usage` (boolean toggle) |
| **3. Food & Waste** | `diet_type` (vegetarian/mixed/non_vegetarian), `recycling_score` (1–5), `plastic_usage_score` (1–5), `household_size` (1–20) |
| **4. Review** | Read-only summary → submit |

### Where calculation logic lives

- **Backend**: [`backend/app/services/calculation_engine.py`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/services/calculation_engine.py)
- Constants: `CALCULATION_VERSION = "1.0.0"`, `DEFAULT_FACTOR_VERSION = "IPCC-2024"`, `BASELINE_MONTHLY_EMISSION = 1000.0 kg CO₂e`
- Factor lookup: queries `carbon_factors` DB table first, falls back to hardcoded values

| Category | Formula | Hardcoded factors |
|---|---|---|
| **Transport** | `distance_km × factor` | car=0.18, motorcycle=0.10, bus=0.08, train=0.04, flight=0.25, bicycle=0.00 |
| **Energy** | `(0 if solar else kwh×0.50) + ac_hours×0.80 + lpg_kg×3.00` | — |
| **Food** | `(diet_factor × period_days) / household_size` | vegetarian=1.7, mixed=2.5, non_veg=3.3 kg/day |
| **Waste** | `plastic_score × 15.0 − recycling_score × 5.0` (floor 0) | — |
| **Score** | `round(100 − (total / 1000) × 100)`, clamped [0, 100] | Higher = better |

### Where score is stored

- **Backend model**: [`backend/app/models/carbon_assessment.py`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/models/carbon_assessment.py) — table `carbon_assessments`, columns: `transport_emission`, `energy_emission`, `food_emission`, `waste_emission`, `total_emission`, `carbon_score`, `calculation_version`, `factor_version`, `assessment_period`
- Raw inputs stored in: [`backend/app/models/emission_inputs.py`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/models/emission_inputs.py) — table `emission_inputs` (1:1 with assessment)

### Files involved

| Layer | File |
|---|---|
| **Frontend form** | [`frontend/src/pages/AssessmentForm.tsx`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/pages/AssessmentForm.tsx) |
| **Frontend API** | [`frontend/src/api/assessment.ts`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/api/assessment.ts) |
| **Frontend result** | [`frontend/src/pages/AssessmentResult.tsx`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/pages/AssessmentResult.tsx) |
| **Frontend history** | [`frontend/src/pages/AssessmentHistory.tsx`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/pages/AssessmentHistory.tsx) |
| **Backend route** | [`backend/app/routes/assessment.py`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/routes/assessment.py) |
| **Backend service** | [`backend/app/services/assessment_service.py`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/services/assessment_service.py) |
| **Calculation engine** | [`backend/app/services/calculation_engine.py`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/services/calculation_engine.py) |
| **Backend schemas** | [`backend/app/schemas/assessment.py`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/schemas/assessment.py) |

---

## 6. AI Coach Integration

### Confirmed: Uses Google Gemini

- SDK: `google-genai` 0.3.0 (`from google import genai`)
- Primary model: `gemini-2.5-flash`, fallback: `gemini-2.0-flash` (on 503 errors)
- API key: `settings.GEMINI_API_KEY` or `os.environ["GEMINI_API_KEY"]`

### Prompt template file

**System prompt** — [`backend/app/services/coach_service.py`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/services/coach_service.py#L21-L37), lines 21–37:

```
You are the Carbon Horizon Sustainability Coach. You are a focused sustainability AI.
You ONLY answer questions about: [sustainability topics list]
If the user asks about ANYTHING else, respond EXACTLY with:
"That falls outside my area of expertise..."
```

**Context builder** — same file, `get_coach_context()` function (lines 50–90):
- Age-group audience adaptation (child → simple language, student → budget-friendly, etc.)
- Country-aware localization (India → solar subsidies/LPG; EU → carbon offsets; US → EV tax credits)
- Injects: latest annual footprint, largest emission source, diet type, transport mode, active goals

### API call location

- **Backend service**: [`backend/app/services/coach_service.py`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/services/coach_service.py#L92-L231), `chat()` function (lines 92–231)
  - Creates `genai.Client(api_key=...)` 
  - Builds chat history from `ai_conversations` DB table
  - Calls `client.chats.create(model=..., config=..., history=...).send_message(context_prompt)`
  - Retry logic: 3 attempts, delays [0, 2, 5]s, retryable codes: 429, 500, 502, 503, 504
- **Backend route**: [`backend/app/routes/coach.py`](file:///home/bhumi/GitHub/CarbonHorizon/backend/app/routes/coach.py)
- **Frontend API**: [`frontend/src/api/coach.ts`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/api/coach.ts)
- **Frontend page**: [`frontend/src/pages/AICoach.tsx`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/pages/AICoach.tsx)

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/coach/chat` | Send message, get AI response |
| GET | `/api/v1/coach/history?conversation_id=X` | Retrieve conversation history |

---

## 7. Analytics / Dashboard — Charts

### Chart libraries in use

Both **Chart.js** (via `react-chartjs-2`) and **Recharts** are used:

| Page | Library | Chart Type(s) |
|---|---|---|
| [`DashboardPage.tsx`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/pages/DashboardPage.tsx) | `chart.js` + `react-chartjs-2` | **Doughnut** (Footprint Breakdown: Transport/Energy/Food/Waste) + **Line** (Emissions Trend over time) |
| [`AssessmentResult.tsx`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/pages/AssessmentResult.tsx) | `chart.js` + `react-chartjs-2` | **Doughnut** (Assessment result breakdown) |
| [`Simulator.tsx`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/pages/Simulator.tsx) | `recharts` | **BarChart** (Current vs Projected emissions by category) |
| [`EmissionsPage.tsx`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/pages/EmissionsPage.tsx) | `recharts` | **Stacked BarChart** (Historical emissions by Scope 1/2/3) |
| [`Forecast.tsx`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/pages/Forecast.tsx) | `chart.js` + `react-chartjs-2` | **Line** (3 forecast paths: Current/Recommended/Custom over 3/6/12 months) |

### Dashboard metric cards

1. **Annual Carbon Footprint** — `(total_emission × 12 / 1000)` tons CO₂e
2. **Carbon Score** — out of 100, with SVG circular progress ring
3. **Reduction Potential** — `dashboard.trend_delta` percentage
4. **Largest Source** — max of transport/energy/food/waste

---

## 8. Emoji Characters in Source Files

### Search methodology

Searched all `.js`, `.jsx`, `.ts`, `.tsx`, `.html`, `.py` files for Unicode ranges:
- U+1F300–1FAFF (Miscellaneous Symbols and Pictographs, Emoticons, Transport, etc.)
- U+2600–27BF (Misc Symbols, Dingbats)
- U+2B50, U+2713–2718 (checkmarks, crosses)
- U+FE00–FE0F (variation selectors)

### Results

| File | Line | Character | Context |
|---|---|---|---|
| [`Simulator.tsx`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/pages/Simulator.tsx#L839) | 839 | `✓` (U+2713) | `<><span>✓</span><span>Saved!</span></>` — "Saved" confirmation button state |

**Total: 1 emoji character** across the entire codebase.

> **Note:** The Simulator page also has properties named `emoji` (e.g., `TRANSPORT_OPTIONS`, `DIET_OPTIONS`, `ToggleCard` props), but these render **Lucide React icon components** (`<Car />`, `<Bus />`, `<Zap />`, etc.), not Unicode emoji characters.

---

## 9. Routing Structure

All routes defined in [`frontend/src/App.tsx`](file:///home/bhumi/GitHub/CarbonHorizon/frontend/src/App.tsx).

### Public routes

| Path | Component | Purpose |
|---|---|---|
| `/login` | `Login` | Login form |
| `/register` | `Register` | Registration form |

### Protected routes (require authentication, wrapped in `<ProtectedRoute>` → `<AppLayout>`)

| Path | Component | Purpose |
|---|---|---|
| `/dashboard` | `DashboardPage` | Main dashboard with charts & metrics |
| `/assessment` | `AssessmentForm` | 4-step carbon assessment wizard |
| `/assessment/history` | `AssessmentHistory` | Past assessment list |
| `/assessment/history/:id` | `AssessmentResult` | View specific past assessment |
| `/assessment/result` | `AssessmentResult` | View just-completed assessment |
| `/simulator` | `Simulator` | What-If scenario simulator |
| `/simulator/history` | `SimulatorHistory` | Past simulation list |
| `/forecast` | `Forecast` | Future emission projections |
| `/profile` | `Profile` | User profile & preferences |
| `/settings` | `SettingsPage` | App settings |
| `/coach` | `AICoach` | AI sustainability coach chat |
| `/goals` | `Goals` | Goal setting & tracking |
| `/habits` | `HabitTracker` | Daily habit tracker |
| `/emissions` | `EmissionsPage` | Emissions scope dashboard |
| `/reports` | `ReportsPage` | Report generation |
| `/organization` | `OrganizationPage` | Organization management |

### Special routes

| Path | Behavior |
|---|---|
| `/` | Redirects to `/dashboard` |
| `*` | `NotFoundPage` (404 catch-all) |

### Backend API routes (all prefixed with `/api/v1`)

| Prefix | Tag | Status |
|---|---|---|
| `/auth` | Auth | ✅ Fully implemented |
| `/assessment` | Assessment | ✅ Fully implemented |
| `/coach` | Coach | ✅ Fully implemented |
| `/simulator` | Simulator | ✅ Implemented |
| `/forecast` | Forecast | ✅ Implemented |
| `/goals` | Goals | ✅ Implemented |
| `/habits` | Habits | ✅ Implemented |
| `/dashboard` | Dashboard | ⬜ Stub (all endpoints return "not implemented") |

---

## Key Observations

1. **Dual chart libraries**: Both `chart.js`/`react-chartjs-2` and `recharts` are installed and used — potential consolidation opportunity.
2. **Redux is effectively unused**: All 4 slices (`auth`, `emissions`, `reports`, `organization`) are stubs with empty reducers and TODO comments. Real auth lives entirely in `AuthContext`.
3. **JWT tokens stored in-memory only**: No localStorage/sessionStorage for tokens (XSS mitigation), but tabs don't share sessions.
4. **Soft-delete pattern**: User model uses `deleted_at` timestamp with `is_deleted` property.
5. **No occupation field**: The user model has `lifestyle_type` (student/professional/homemaker/retired) instead.
6. **Profile page inconsistency**: Missing `child` option in age_group select that exists in the Register form schema.
7. **Dashboard backend stubs**: The `/dashboard/summary`, `/dashboard/history`, `/dashboard/breakdown` endpoints all return "not implemented" — the frontend fetches dashboard data by composing assessment + goals + habits API calls instead.
8. **Single emoji**: Only `✓` (U+2713) in `Simulator.tsx:839`.
