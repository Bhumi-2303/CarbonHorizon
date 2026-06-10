"""
Models package — imports all 12 ORM models so that:
  1. Alembic autogenerate can detect the full schema
  2. SQLAlchemy relationship back-references resolve correctly
  3. Consumers can `from app.models import User, CarbonAssessment, …`

Import order respects FK dependencies (referenced tables first).
"""

# Enums and mixins (no ORM tables)
from app.models.enums import (  # noqa: F401
    AgeGroup, LifestyleType, Theme, MeasurementUnit,
    AssessmentPeriod, TransportMode, DietType, GoalStatus,
    ForecastType, HabitType, ConversationRole,
)

# ── Reference / lookup tables (no FK to user) ──────────────────────────────
from app.models.carbon_factor import CarbonFactor          # noqa: F401
from app.models.habit_definition import HabitDefinition    # noqa: F401

# ── Core user table ─────────────────────────────────────────────────────────
from app.models.user import User                           # noqa: F401

# ── User-dependent tables ────────────────────────────────────────────────────
from app.models.user_preferences import UserPreferences    # noqa: F401
from app.models.carbon_assessment import CarbonAssessment  # noqa: F401
from app.models.emission_inputs import EmissionInputs      # noqa: F401
from app.models.goal import Goal                           # noqa: F401
from app.models.simulation import Simulation               # noqa: F401
from app.models.forecast import Forecast                   # noqa: F401
from app.models.forecast_point import ForecastPoint        # noqa: F401
from app.models.habit import Habit                         # noqa: F401
from app.models.ai_conversation import AIConversation      # noqa: F401
