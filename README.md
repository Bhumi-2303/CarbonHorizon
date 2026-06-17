<div align="center">
  <h1>🌍 Carbon Horizon</h1>
  <p><strong>Intelligent Carbon Footprint Tracking & AI-Powered Sustainability Coaching</strong></p>
  <p>
    <a href="https://github.com/Bhumi-2303/CarbonHorizon/actions/workflows/deploy.yml">
      <img src="https://github.com/Bhumi-2303/CarbonHorizon/actions/workflows/deploy.yml/badge.svg" alt="Build Status" />
    </a>
    <img src="https://img.shields.io/badge/Coverage-91%25-success?style=flat-square" alt="Test Coverage" />
    <a href="LICENSE">
      <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License" />
    </a>
  </p>
  <p>
    <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React" />
    <img src="https://img.shields.io/badge/Gemini_AI-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini" />
  </p>
</div>

---

## 1. Project Overview

### The Business Problem
Climate change mitigation requires individual and organizational action, but understanding one's carbon footprint is often complex, abstract, and demotivating. Existing tools provide generic numbers without actionable context, leaving users unsure of *how* to realistically reduce their emissions without drastic lifestyle overhauls.

### The AI Solution
**Carbon Horizon** bridges the gap between raw data and actionable sustainability. By combining standardized emission factors (IPCC/EPA) with Google's powerful **Gemini AI**, the platform acts as a personalized sustainability coach. It doesn't just calculate your footprint; it analyzes your specific habits, forecasts your future impact, and engages in dynamic, context-aware conversations to help you build sustainable routines.

### Architecture Highlights
- **Microservice-ready Monolith:** A fast, typed, and scalable backend powered by FastAPI.
- **Reactive Frontend:** A rich Single Page Application built with React 18, Redux Toolkit, and TailwindCSS.
- **AI Integration:** Seamless, rate-limited, and secure communication with the Gemini API to provide real-time coaching and automated sustainability reports.

---

## 2. Approach & Methodology

### Why This Architecture?
- **FastAPI + SQLAlchemy:** Provides high performance, automatic OpenAPI documentation, and strict type validation via Pydantic. It ensures data integrity before it ever reaches the AI models or the database.
- **React + TailwindCSS:** Allows for rapid prototyping and deployment of a highly responsive, modern, and accessible user interface, visualizing complex data through Recharts and Chart.js.
- **Decoupled AI Layer:** The AI logic is abstracted into dedicated service layers (`coach_service`, `report_service`), allowing us to swap models, adjust prompt engineering, and enforce strict payload limits without touching the core routing logic.

### AI Workflow
1. **Data Ingestion:** User inputs daily habits, transport, energy use, and waste output.
2. **Deterministic Calculation:** The backend applies strictly verified IPCC/EPA carbon factors to calculate an absolute baseline (no AI hallucinations here).
3. **Contextualization:** The user's baseline, historical data, and active goals are securely bundled and sent to the Gemini API.
4. **Actionable Output:** The AI returns structured JSON recommendations, conversational coaching, or comprehensive markdown reports tailored to the user's specific constraints.

### Assumptions
- Calculations assume baseline averages provided by standard environmental agencies (e.g., standard grid emission factors).
- Users have consistent reporting behavior for accurate forecasting.

---

## 3. Technical Stack

### Backend
- **Framework:** Python 3.14+, FastAPI
- **ORM & DB:** SQLAlchemy, SQLite (Development) / PostgreSQL (Production)
- **Validation:** Pydantic v2
- **Testing:** Pytest (91%+ Test Coverage), pytest-cov
- **Auth:** JWT (JSON Web Tokens), Passlib (bcrypt)

### Frontend
- **Framework:** React 18, Vite, TypeScript
- **State Management:** Redux Toolkit
- **Styling:** TailwindCSS
- **Forms & Validation:** React Hook Form, Zod
- **Charting:** Recharts, Chart.js

### AI Services
- **LLM:** Google Gemini API (`google-genai` SDK)

### Deployment
- **Containerization:** Docker, Docker Compose
- **CI/CD:** Google Cloud Build (`cloudbuild.yaml`)
- **Proxy/Gateway:** Nginx

---

## 4. Quick Start

### Clone the Repository
```bash
git clone https://github.com/your-org/CarbonHorizon.git
cd CarbonHorizon
```

### Environment Setup
Create a `.env` file in the `backend/` directory:
```env
# backend/.env
ENVIRONMENT=development
SECRET_KEY=generate_a_secure_32_byte_string_here
DATABASE_URL=postgresql://postgres:password@localhost:5432/carbonhorizon
GEMINI_API_KEY=your_google_gemini_api_key
```

### Run Backend (Local)
Ensure you have the PostgreSQL database running first:
```bash
docker-compose up -d db
```

Then start the backend server:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run migrations to set up the PostgreSQL schema
alembic upgrade head

# Start the dev server
fastapi dev app/main.py
```
*The backend will be available at `http://localhost:8000`. Swagger UI at `http://localhost:8000/docs`.*

### Run Frontend (Local)
```bash
cd frontend
npm install
npm run dev
```
*The frontend will be available at `http://localhost:5173`.*

### Run Tests
The backend features an extremely robust, production-quality test suite with >91% coverage.
```bash
cd backend
.venv/bin/pytest --cov=app tests/
```

### Run with Docker Compose
```bash
docker-compose up --build
```

---

## 5. API Documentation

Carbon Horizon provides a fully documented RESTful API. Once the backend is running, navigate to `/docs` for the interactive Swagger UI.

**Core Namespaces:**
- `POST /api/v1/auth/register` - User registration.
- `POST /api/v1/auth/login` - JWT generation.
- `GET /api/v1/assessment/` - Fetch historical carbon assessments.
- `POST /api/v1/coach/chat` - Interact with the Gemini-powered sustainability coach.
- `POST /api/v1/simulator/run` - Run AI-assisted emission reduction simulations.
- `GET /api/v1/reports/generate` - Generate a comprehensive AI sustainability report.

---

## 6. Architecture Diagram

```mermaid
graph TD
    %% Frontend
    subgraph Client [Frontend SPA]
        UI[React 18 + Tailwind]
        State[Redux Toolkit]
        Charts[Recharts / Chart.js]
        UI <--> State
        State <--> Charts
    end

    %% Backend API
    subgraph Server [FastAPI Backend]
        Router[API Routers]
        Auth[JWT Security / Rate Limiting]
        Services[Business Logic & AI Services]
        CalcEngine[Deterministic Calc Engine]
        
        Router --> Auth
        Auth --> Services
        Services <--> CalcEngine
    end

    %% External & DB
    subgraph Persistence [Data Layer]
        DB[(SQLite / PostgreSQL)]
    end

    subgraph External [AI Provider]
        Gemini[Google Gemini API]
    end

    %% Connections
    Client -- REST API / JSON --> Router
    Services -- Read/Write --> DB
    Services -- Secured Context/Prompts --> Gemini
```

---

## 7. Folder Structure

```text
CarbonHorizon/
├── backend/                  # Python FastAPI Application
│   ├── app/
│   │   ├── api/              # Route dependencies
│   │   ├── core/             # Config, security, dependencies, rate limits
│   │   ├── db/               # Session management, seed scripts
│   │   ├── models/           # SQLAlchemy ORM definitions
│   │   ├── routes/           # API endpoints (auth, coach, simulator, etc.)
│   │   ├── schemas/          # Pydantic validation models
│   │   └── services/         # Core business and AI interaction logic
│   ├── tests/                # Pytest suite (>91% coverage)
│   ├── pytest.ini            # Pytest configuration
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React SPA
│   ├── src/                  
│   ├── package.json          
│   ├── tailwind.config.js    
│   └── vite.config.ts        
├── docker-compose.yml        # Multi-container orchestration
└── cloudbuild.yaml           # Google Cloud Build pipeline
```

---

## 8. Security Considerations

- **Stateless Authentication:** All protected endpoints require short-lived JWTs. Passwords are never stored in plaintext (hashed via bcrypt).
- **Rate Limiting:** The AI endpoints (like `/api/v1/coach/chat`) are aggressively rate-limited using in-memory or Redis limits to prevent API abuse and control LLM costs.
- **Payload Validation:** Pydantic strictly validates all incoming JSON. Maximum payload lengths (e.g., `max_length=4000` on coach messages) ensure the system is immune to excessively large prompt injection attempts.
- **Environment Separation:** The architecture supports strict `ENVIRONMENT` checks, instantly failing startup if a `production` environment is missing a cryptographically secure `SECRET_KEY`.

---

## 9. Future Improvements

- **B2B / Organization Scopes:** Expand the current user model to support Teams/Organizations for corporate ESG tracking.
- **IoT & Real-time Integrations:** Connect directly to smart home APIs (e.g., smart thermostats, smart meters) for automated, real-time energy usage ingestion.
- **Gamification Enhancements:** Introduce leaderboards and achievement badges directly tied to verified emission reductions.
- **Multi-language Support:** Leverage Gemini's translation capabilities to automatically offer the coaching experience in multiple global languages.

---

## 10. Screenshots

*(Replace these placeholders with actual screenshots of your application before submitting)*

| Dashboard Overview | AI Coach Interaction |
| :---: | :---: |
| <img src="https://via.placeholder.com/600x400.png?text=Dashboard+Overview" alt="Dashboard" width="400"/> | <img src="https://via.placeholder.com/600x400.png?text=AI+Coach+Interaction" alt="AI Coach" width="400"/> |
| *Interactive emission breakdowns and tracking.* | *Context-aware advice from the Gemini coach.* |

| Goal Setting | Automated Reports |
| :---: | :---: |
| <img src="https://via.placeholder.com/600x400.png?text=Goal+Setting" alt="Goals" width="400"/> | <img src="https://via.placeholder.com/600x400.png?text=Automated+Reports" alt="Reports" width="400"/> |
| *Setting and forecasting targeted emission reductions.* | *Generated sustainability reports.* |

---
<div align="center">
  <i>Built for the future. 🌿</i>
</div>
