"""create_initial_schema

Creates all 12 MVP tables for Carbon Horizon with their indexes.

Tables (in FK dependency order):
  1. carbon_factors       — emission factor reference data (no FK)
  2. habit_definitions    — habit carbon-saving factors (no FK)
  3. users                — accounts + soft delete
  4. ai_conversations     — chat history  (FK → users)
  5. carbon_assessments   — emission totals (FK → users)
  6. forecasts            — forecast sessions (FK → users)
  7. goals                — sustainability goals (FK → users)
  8. habits               — daily habit completions (FK → users)
  9. simulations          — what-if scenarios (FK → users)
  10. user_preferences    — display/notification settings (FK → users)
  11. emission_inputs     — raw survey data 1-to-1 (FK → carbon_assessments)
  12. forecast_points     — time-series rows (FK → forecasts)

Notes:
  • UUID primary keys throughout.
  • All timestamps are timezone-aware UTC.
  • Soft delete on users via deleted_at.
  • render_as_batch=True in env.py handles SQLite ALTER TABLE limitations.
  • simulation_data uses sa.JSON (portable) — PostgreSQL stores it as JSONB
    when the column is declared with postgresql.JSONB in the ORM model;
    this migration uses the portable sa.JSON so SQLite also works.

Revision ID: 8e881f34c5ec
Revises:
Create Date: 2026-06-10 05:51:16.018822+00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy import Text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8e881f34c5ec"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all 12 tables and their indexes."""

    # ── 1. carbon_factors ────────────────────────────────────────────────────
    op.create_table(
        "carbon_factors",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("sub_category", sa.String(length=100), nullable=True),
        sa.Column("factor_value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("source_reference", sa.Text(), nullable=True),
        sa.Column("source_name", sa.String(length=255), nullable=True),
        sa.Column("version", sa.String(length=20), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("carbon_factors", schema=None) as batch_op:
        batch_op.create_index("ix_carbon_factors_category", ["category"], unique=False)
        batch_op.create_index("ix_carbon_factors_sub_category", ["sub_category"], unique=False)
        batch_op.create_index("ix_carbon_factors_version", ["version"], unique=False)
        batch_op.create_index("ix_carbon_factors_effective_date", ["effective_date"], unique=False)

    # ── 2. habit_definitions ─────────────────────────────────────────────────
    op.create_table(
        "habit_definitions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("habit_type", sa.String(length=100), nullable=False),
        sa.Column("carbon_saving_factor", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("habit_definitions", schema=None) as batch_op:
        batch_op.create_index("ix_habit_definitions_habit_type", ["habit_type"], unique=False)

    # ── 3. users ─────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("age_group", sa.String(length=20), nullable=True),
        sa.Column("lifestyle_type", sa.String(length=20), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("email_verified", sa.Boolean(), nullable=False),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_users_email"), ["email"], unique=True)
        batch_op.create_index("ix_users_deleted_at", ["deleted_at"], unique=False)
        batch_op.create_index("ix_users_country", ["country"], unique=False)

    # ── 4. ai_conversations ──────────────────────────────────────────────────
    op.create_table(
        "ai_conversations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(length=10), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("ai_conversations", schema=None) as batch_op:
        batch_op.create_index(
            "ix_ai_conversations_conversation_id", ["conversation_id"], unique=False
        )
        batch_op.create_index("ix_ai_conversations_user_id", ["user_id"], unique=False)
        batch_op.create_index(
            "ix_ai_conversations_user_conversation",
            ["user_id", "conversation_id"],
            unique=False,
        )
        batch_op.create_index("ix_ai_conversations_created_at", ["created_at"], unique=False)

    # ── 5. carbon_assessments ────────────────────────────────────────────────
    op.create_table(
        "carbon_assessments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("transport_emission", sa.Float(), nullable=True),
        sa.Column("energy_emission", sa.Float(), nullable=True),
        sa.Column("food_emission", sa.Float(), nullable=True),
        sa.Column("waste_emission", sa.Float(), nullable=True),
        sa.Column("total_emission", sa.Float(), nullable=True),
        sa.Column("carbon_score", sa.Integer(), nullable=True),
        sa.Column("calculation_version", sa.String(length=20), nullable=True),
        sa.Column("factor_version", sa.String(length=20), nullable=True),
        sa.Column("assessment_period", sa.String(length=10), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("carbon_assessments", schema=None) as batch_op:
        batch_op.create_index("ix_carbon_assessments_user_id", ["user_id"], unique=False)
        batch_op.create_index(
            "ix_carbon_assessments_period", ["assessment_period"], unique=False
        )
        batch_op.create_index("ix_carbon_assessments_created_at", ["created_at"], unique=False)

    # ── 6. forecasts ─────────────────────────────────────────────────────────
    op.create_table(
        "forecasts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("forecast_type", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("forecasts", schema=None) as batch_op:
        batch_op.create_index("ix_forecasts_user_id", ["user_id"], unique=False)
        batch_op.create_index("ix_forecasts_type", ["forecast_type"], unique=False)

    # ── 7. goals ─────────────────────────────────────────────────────────────
    op.create_table(
        "goals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("goal_name", sa.String(length=255), nullable=False),
        sa.Column("goal_description", sa.Text(), nullable=True),
        sa.Column("target_reduction_percentage", sa.Float(), nullable=True),
        sa.Column("target_emission_value", sa.Float(), nullable=True),
        sa.Column("current_progress", sa.Float(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=15), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("goals", schema=None) as batch_op:
        batch_op.create_index("ix_goals_user_id", ["user_id"], unique=False)
        batch_op.create_index("ix_goals_status", ["status"], unique=False)
        batch_op.create_index("ix_goals_target_date", ["target_date"], unique=False)

    # ── 8. habits ────────────────────────────────────────────────────────────
    op.create_table(
        "habits",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("habit_type", sa.String(length=30), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("carbon_saved", sa.Float(), nullable=True),
        sa.Column("activity_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("habits", schema=None) as batch_op:
        batch_op.create_index("ix_habits_user_id", ["user_id"], unique=False)
        batch_op.create_index("ix_habits_activity_date", ["activity_date"], unique=False)
        batch_op.create_index(
            "ix_habits_user_date", ["user_id", "activity_date"], unique=False
        )
        batch_op.create_index("ix_habits_habit_type", ["habit_type"], unique=False)

    # ── 9. simulations ───────────────────────────────────────────────────────
    # simulation_data: use portable sa.JSON — works on both SQLite and PostgreSQL.
    # The ORM model declares it as JSONB (PostgreSQL-native) which is fine because
    # JSONB is a superset of JSON; this migration uses JSON for cross-DB portability.
    op.create_table(
        "simulations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("scenario_name", sa.String(length=255), nullable=False),
        sa.Column("scenario_description", sa.Text(), nullable=True),
        sa.Column("current_emission", sa.Float(), nullable=True),
        sa.Column("projected_emission", sa.Float(), nullable=True),
        sa.Column("reduction_percentage", sa.Float(), nullable=True),
        sa.Column("estimated_carbon_saved", sa.Float(), nullable=True),
        sa.Column("simulation_data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("simulations", schema=None) as batch_op:
        batch_op.create_index("ix_simulations_user_id", ["user_id"], unique=False)
        batch_op.create_index("ix_simulations_created_at", ["created_at"], unique=False)

    # ── 10. user_preferences ─────────────────────────────────────────────────
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("theme", sa.String(length=10), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=False),
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False),
        sa.Column("measurement_unit", sa.String(length=10), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),  # enforces 1-to-1 with users
    )
    with op.batch_alter_table("user_preferences", schema=None) as batch_op:
        batch_op.create_index("ix_user_preferences_user_id", ["user_id"], unique=False)

    # ── 11. emission_inputs ──────────────────────────────────────────────────
    op.create_table(
        "emission_inputs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("assessment_id", sa.UUID(), nullable=False),
        sa.Column("transport_mode", sa.String(length=15), nullable=True),
        sa.Column("distance_km", sa.Float(), nullable=True),
        sa.Column("electricity_kwh", sa.Float(), nullable=True),
        sa.Column("ac_hours", sa.Float(), nullable=True),
        sa.Column("lpg_usage", sa.Float(), nullable=True),
        sa.Column("solar_usage", sa.Boolean(), nullable=True),
        sa.Column("diet_type", sa.String(length=20), nullable=True),
        sa.Column("recycling_score", sa.Integer(), nullable=True),
        sa.Column("plastic_usage_score", sa.Integer(), nullable=True),
        sa.Column("household_size", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["assessment_id"], ["carbon_assessments.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assessment_id"),  # enforces 1-to-1 with carbon_assessments
    )
    with op.batch_alter_table("emission_inputs", schema=None) as batch_op:
        batch_op.create_index(
            "ix_emission_inputs_assessment_id", ["assessment_id"], unique=False
        )

    # ── 12. forecast_points ──────────────────────────────────────────────────
    op.create_table(
        "forecast_points",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("forecast_id", sa.UUID(), nullable=False),
        sa.Column("month_offset", sa.Integer(), nullable=False),
        sa.Column("predicted_emission", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["forecast_id"], ["forecasts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("forecast_points", schema=None) as batch_op:
        batch_op.create_index(
            "ix_forecast_points_forecast_id", ["forecast_id"], unique=False
        )
        batch_op.create_index(
            "ix_forecast_points_month_offset",
            ["forecast_id", "month_offset"],
            unique=False,
        )


def downgrade() -> None:
    """Drop all 12 tables in reverse FK dependency order."""

    # Leaf tables first (depend on others)
    with op.batch_alter_table("forecast_points", schema=None) as batch_op:
        batch_op.drop_index("ix_forecast_points_month_offset")
        batch_op.drop_index("ix_forecast_points_forecast_id")
    op.drop_table("forecast_points")

    with op.batch_alter_table("emission_inputs", schema=None) as batch_op:
        batch_op.drop_index("ix_emission_inputs_assessment_id")
    op.drop_table("emission_inputs")

    with op.batch_alter_table("user_preferences", schema=None) as batch_op:
        batch_op.drop_index("ix_user_preferences_user_id")
    op.drop_table("user_preferences")

    with op.batch_alter_table("simulations", schema=None) as batch_op:
        batch_op.drop_index("ix_simulations_created_at")
        batch_op.drop_index("ix_simulations_user_id")
    op.drop_table("simulations")

    with op.batch_alter_table("habits", schema=None) as batch_op:
        batch_op.drop_index("ix_habits_habit_type")
        batch_op.drop_index("ix_habits_user_date")
        batch_op.drop_index("ix_habits_activity_date")
        batch_op.drop_index("ix_habits_user_id")
    op.drop_table("habits")

    with op.batch_alter_table("goals", schema=None) as batch_op:
        batch_op.drop_index("ix_goals_target_date")
        batch_op.drop_index("ix_goals_status")
        batch_op.drop_index("ix_goals_user_id")
    op.drop_table("goals")

    with op.batch_alter_table("forecasts", schema=None) as batch_op:
        batch_op.drop_index("ix_forecasts_type")
        batch_op.drop_index("ix_forecasts_user_id")
    op.drop_table("forecasts")

    with op.batch_alter_table("carbon_assessments", schema=None) as batch_op:
        batch_op.drop_index("ix_carbon_assessments_created_at")
        batch_op.drop_index("ix_carbon_assessments_period")
        batch_op.drop_index("ix_carbon_assessments_user_id")
    op.drop_table("carbon_assessments")

    with op.batch_alter_table("ai_conversations", schema=None) as batch_op:
        batch_op.drop_index("ix_ai_conversations_created_at")
        batch_op.drop_index("ix_ai_conversations_user_conversation")
        batch_op.drop_index("ix_ai_conversations_user_id")
        batch_op.drop_index("ix_ai_conversations_conversation_id")
    op.drop_table("ai_conversations")

    # Root user table
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index("ix_users_country")
        batch_op.drop_index("ix_users_deleted_at")
        batch_op.drop_index(batch_op.f("ix_users_email"))
    op.drop_table("users")

    # Standalone reference tables
    with op.batch_alter_table("habit_definitions", schema=None) as batch_op:
        batch_op.drop_index("ix_habit_definitions_habit_type")
    op.drop_table("habit_definitions")

    with op.batch_alter_table("carbon_factors", schema=None) as batch_op:
        batch_op.drop_index("ix_carbon_factors_effective_date")
        batch_op.drop_index("ix_carbon_factors_sub_category")
        batch_op.drop_index("ix_carbon_factors_category")
        batch_op.drop_index("ix_carbon_factors_version")
    op.drop_table("carbon_factors")
