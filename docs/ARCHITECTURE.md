# Carbon Horizon Architecture

Carbon Horizon is designed as a modern, decoupled web application. The frontend is a Single Page Application (SPA) built with React, TypeScript, and Vite. The backend is a high-performance RESTful API powered by FastAPI, interacting with a PostgreSQL database.

## System Architecture

The following diagram illustrates the high-level architecture of Carbon Horizon:

```mermaid
graph TD
    Client[Web Browser] -->|HTTPS / REST API| Proxy[Cloud Run Proxy / Nginx]
    
    subgraph Frontend [Frontend Container]
        UI[React UI]
        State[Redux State]
        Router[React Router]
        UI <--> State
        UI <--> Router
    end
    
    Proxy -->|Static Assets| Frontend
    Proxy -->|API Requests| Backend
    
    subgraph Backend [Backend Container]
        API[FastAPI Router]
        Services[Business Logic Services]
        Calculations[Calculation Engine]
        DB_Access[SQLAlchemy ORM]
        
        API --> Services
        Services --> Calculations
        Services --> DB_Access
    end
    
    Backend -->|SQL| Database[(PostgreSQL)]
    Backend -->|REST| Gemini[Google Gemini API]
```

## Database Entity-Relationship (ER) Diagram

The system stores users, carbon factors, assessments, and historical data. Below is the simplified ER diagram for the primary domain models:

```mermaid
erDiagram
    User ||--o{ UserPreferences : has
    User ||--o{ CarbonAssessment : completes
    User ||--o{ Goal : tracks
    User ||--o{ Habit : tracks
    User ||--o{ AIConversation : interacts_with
    
    CarbonAssessment ||--|{ EmissionInput : contains
    
    EmissionInput }|--|| CarbonFactor : references

    User {
        uuid id PK
        string email
        string password_hash
        string full_name
        string age_group
        string lifestyle_type
    }
    
    CarbonAssessment {
        int id PK
        uuid user_id FK
        float total_emissions
        string version
        timestamp created_at
    }
    
    EmissionInput {
        int id PK
        int assessment_id FK
        int factor_id FK
        string category
        float quantity
        float calculated_emissions
    }
    
    CarbonFactor {
        int id PK
        string category
        string name
        float emission_factor
        string unit
        string version
    }
    
    Goal {
        int id PK
        uuid user_id FK
        string target_category
        float target_reduction
        date deadline
    }
    
    Habit {
        int id PK
        uuid user_id FK
        string name
        int streak
        float carbon_savings
    }
```

## Component Interactions

1. **User Authentication**: JWT-based authentication. The React frontend stores the access token in memory (via AuthContext/Redux) and handles refreshing using an Axios interceptor to ensure seamless sessions.
2. **Carbon Calculation**: When a user submits an assessment form, the frontend passes raw input data to the FastAPI backend. The `CalculationEngine` fetches the corresponding `CarbonFactor`s and multiplies inputs by emission factors, returning an aggregate breakdown to the frontend.
3. **AI Coaching**: Real-time interactions are routed to the `coach_service`. This service appends the user's current context (age, recent footprint, active goals) into a system prompt before querying the Google Gemini API, ensuring highly personalized advice.

## Infrastructure & Deployment

The application is containerized using Docker. In production:
- **Google Cloud Run** serves both the Frontend (via Nginx or a static adapter) and the Backend API.
- **Cloud SQL** hosts the highly-available PostgreSQL instance.
- **GitHub Actions** automates continuous integration (running `flake8`, `pytest`, `vitest`) and deployment.
