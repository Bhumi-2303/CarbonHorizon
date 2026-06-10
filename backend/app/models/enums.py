"""
Python Enum definitions for all ENUM columns used across models.
Centralised here so enums are shared between ORM models and Pydantic schemas.
"""
import enum


class AgeGroup(str, enum.Enum):
    child = "child"
    student = "student"
    adult = "adult"
    senior = "senior"


class LifestyleType(str, enum.Enum):
    student = "student"
    professional = "professional"
    homemaker = "homemaker"
    retired = "retired"


class Theme(str, enum.Enum):
    light = "light"
    dark = "dark"
    system = "system"


class MeasurementUnit(str, enum.Enum):
    metric = "metric"
    imperial = "imperial"


class AssessmentPeriod(str, enum.Enum):
    daily = "daily"
    monthly = "monthly"
    annual = "annual"


class TransportMode(str, enum.Enum):
    car = "car"
    motorcycle = "motorcycle"
    bus = "bus"
    train = "train"
    flight = "flight"
    bicycle = "bicycle"


class DietType(str, enum.Enum):
    vegetarian = "vegetarian"
    mixed = "mixed"
    non_vegetarian = "non_vegetarian"


class GoalStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    expired = "expired"


class ForecastType(str, enum.Enum):
    current_path = "current_path"
    recommended_path = "recommended_path"
    custom_path = "custom_path"


class HabitType(str, enum.Enum):
    public_transport = "public_transport"
    recycling = "recycling"
    save_electricity = "save_electricity"
    water_conservation = "water_conservation"
    plastic_reduction = "plastic_reduction"


class ConversationRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"
