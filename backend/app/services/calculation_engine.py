"""
CalculationEngine — Core carbon calculation logic.

Converts raw user activity survey inputs into carbon emissions (kg CO₂e),
assigns a normalized carbon score, and stamps version metadata.
"""
import logging
from sqlalchemy.orm import Session
from app.models.carbon_factor import CarbonFactor
from app.models.enums import TransportMode, DietType, AssessmentPeriod

logger = logging.getLogger(__name__)

# Constants
CALCULATION_VERSION = "1.0.0"
DEFAULT_FACTOR_VERSION = "IPCC-2024"
BASELINE_MONTHLY_EMISSION = 1000.0  # kg CO₂e

TRANSPORT_FALLBACK_FACTORS = {
    "car": 0.18,          # kg CO₂e / km
    "motorcycle": 0.10,   # kg CO₂e / km
    "bus": 0.08,          # kg CO₂e / km
    "train": 0.04,         # kg CO₂e / km
    "flight": 0.25,        # kg CO₂e / km
    "bicycle": 0.00,       # kg CO₂e / km
}

COUNTRY_GRID_FACTORS = {
    "India": 0.70,
    "United States": 0.38,
    "United Kingdom": 0.23,
    "Germany": 0.35,
    "France": 0.06,
    "Australia": 0.65,
    "Canada": 0.12,
}


def _get_val(obj, key, default=None):
    """
    Helper to extract a field from a dictionary or object (ORM model / Pydantic schema).
    """
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _get_factor(
    db: Session | None,
    category: str,
    sub_category: str,
    fallback_value: float,
    version_tracker: dict | None = None
) -> float:
    """
    Query the database for an active carbon factor. Fallback if not found or DB is unavailable.
    """
    if version_tracker and "_factors" in version_tracker:
        factor = version_tracker["_factors"].get((category, sub_category))
        if factor is not None:
            if factor.version:
                version_tracker["factor_version"] = factor.version
            return float(factor.factor_value)
        return fallback_value

    if db is None:
        return fallback_value
    try:
        factor = (
            db.query(CarbonFactor)
            .filter(
                CarbonFactor.category == category,
                CarbonFactor.sub_category == sub_category
            )
            .first()
        )
        if factor is not None:
            if version_tracker is not None and factor.version:
                version_tracker["factor_version"] = factor.version
            return float(factor.factor_value)
    except Exception as e:
        logger.warning(
            f"Error querying carbon_factors for {category}/{sub_category}: {e}. "
            f"Falling back to {fallback_value}."
        )
    return fallback_value


def calculate_transport(
    transport_mode: str | TransportMode | None,
    distance_km: float | None,
    db: Session | None = None,
    version_tracker: dict | None = None
) -> float:
    """
    Calculate transportation emissions: distance_km * factor.
    """
    if not transport_mode or distance_km is None:
        return 0.0
    if distance_km < 0:
        distance_km = 0.0

    mode_str = (
        transport_mode.value
        if isinstance(transport_mode, TransportMode)
        else str(transport_mode)
    )

    fallback = TRANSPORT_FALLBACK_FACTORS.get(mode_str, 0.10)
    factor_val = _get_factor(db, "transport", mode_str, fallback, version_tracker)
    
    base_emission = float(distance_km * factor_val)
    return base_emission


def calculate_energy(
    electricity_kwh: float | None,
    ac_hours: float | None,
    lpg_usage: float | None,
    solar_usage: bool | None,
    db: Session | None = None,
    version_tracker: dict | None = None
) -> float:
    """
    Calculate energy emissions from grid electricity, AC hours, and LPG usage.
    Solar adoption offsets 100% of grid electricity emissions.
    """
    kwh = max(0.0, electricity_kwh) if electricity_kwh is not None else 0.0
    ac = max(0.0, ac_hours) if ac_hours is not None else 0.0
    lpg = max(0.0, lpg_usage) if lpg_usage is not None else 0.0
    solar = bool(solar_usage)

    electricity_factor = 0.50
    # Geographic check
    inp = version_tracker.get("_inp", {}) if version_tracker else {}
    country = _get_val(inp, "assessment_country")
    if country and country in COUNTRY_GRID_FACTORS:
        electricity_factor = COUNTRY_GRID_FACTORS[country]
        
    electricity_factor = _get_factor(db, "energy", "electricity", electricity_factor, version_tracker)
    ac_factor = _get_factor(db, "energy", "ac", 0.80, version_tracker)
    lpg_factor = _get_factor(db, "energy", "lpg", 3.00, version_tracker)

    electricity_emissions = 0.0 if solar else (kwh * electricity_factor)
    ac_emissions = ac * ac_factor
    lpg_emissions = lpg * lpg_factor

    return float(electricity_emissions + ac_emissions + lpg_emissions)


def calculate_food(
    diet_type: str | DietType | None,
    household_size: int | None,
    db: Session | None = None,
    version_tracker: dict | None = None,
    assessment_period: str | AssessmentPeriod | None = None
) -> float:
    """
    Calculate dietary emissions normalized per household size.
    Scaled based on assessment period (default is monthly = 30 days).
    """
    if not diet_type:
        return 0.0

    diet_str = (
        diet_type.value
        if isinstance(diet_type, DietType)
        else str(diet_type)
    )

    if diet_str == "vegetarian":
        fallback = 1.7
    elif diet_str == "non_vegetarian":
        fallback = 3.3
    else:
        fallback = 2.5  # mixed or other

    diet_factor = _get_factor(db, "food", diet_str, fallback, version_tracker)

    # Scale daily factor to period
    period_str = (
        assessment_period.value
        if isinstance(assessment_period, AssessmentPeriod)
        else str(assessment_period or "monthly")
    )

    if period_str == "daily":
        days = 1.0
    elif period_str == "annual":
        days = 365.0
    else:
        days = 30.0  # default monthly

    return float(diet_factor * days)


def calculate_waste(
    recycling_score: int | None,
    plastic_usage_score: int | None,
    db: Session | None = None,
    version_tracker: dict | None = None
) -> float:
    """
    Calculate waste emissions: based on plastic usage score offset by recycling score.
    """
    if recycling_score is None and plastic_usage_score is None:
        return 0.0

    r_score = max(0, recycling_score) if recycling_score is not None else 0
    p_score = max(0, plastic_usage_score) if plastic_usage_score is not None else 0

    plastic_factor = _get_factor(db, "waste", "plastic", 15.0, version_tracker)
    recycling_factor = _get_factor(db, "waste", "recycling", 5.0, version_tracker)

    waste_emissions = (p_score * plastic_factor) - (r_score * recycling_factor)
    return float(max(0.0, waste_emissions))

def calculate_housing(inp: dict) -> float:
    sqm = _get_val(inp, "house_size_sqm") or 0.0
    # Average 0.5 kg CO2 per sqm per month
    return float(sqm * 0.5)

def calculate_water(inp: dict) -> float:
    liters = _get_val(inp, "daily_water_liters") or 0.0
    # Energy to treat/pump water: 0.001 kg per liter per day -> * 30 for monthly
    return float((liters * 0.001) * 30.0)

def calculate_digital(inp: dict) -> float:
    screen = _get_val(inp, "screen_time_hours") or 0.0
    stream = _get_val(inp, "streaming_hours") or 0.0
    gaming = _get_val(inp, "gaming_hours") or 0.0
    # Rough estimate: streaming/gaming takes more bandwidth/server energy (~0.05 kg/hr)
    return float((screen * 0.01 + stream * 0.05 + gaming * 0.08) * 30.0)

def calculate_shopping(inp: dict) -> float:
    clothes = _get_val(inp, "new_clothes_monthly") or 0
    electronics = _get_val(inp, "electronics_purchases_yearly") or 0
    # Fast fashion avg 10 kg per item, electronics 50 kg per item (divided by 12 for monthly)
    return float((clothes * 10.0) + (electronics * 50.0 / 12.0))

def calculate_offsets(inp: dict) -> float:
    total_offset = 0.0
    if _get_val(inp, "composting_active"):
        total_offset += 15.0 # saves 15 kg/mo
    trees = _get_val(inp, "tree_planting_count") or 0
    total_offset += trees * 2.0 # 2 kg per tree per month 
    if _get_val(inp, "green_transport_choices"):
        total_offset += 10.0
    return float(total_offset)


def calculate_total_emissions(
    db: Session | None,
    emission_input=None
) -> dict:
    """
    Main footprint calculation engine entrypoint.
    Supports signature as:
      - calculate_total_emissions(db, emission_input)
      - calculate_total_emissions(emission_input) (with db defaulting to None)
    """
    # Parse signature overload
    if emission_input is None:
        inp = db
        db = None
    else:
        inp = emission_input

    # Extract fields from the emission input
    transport_mode = _get_val(inp, "transport_mode")
    distance_km = _get_val(inp, "distance_km")
    electricity_kwh = _get_val(inp, "electricity_kwh")
    ac_hours = _get_val(inp, "ac_hours")
    lpg_usage = _get_val(inp, "lpg_usage")
    solar_usage = _get_val(inp, "solar_usage")
    diet_type = _get_val(inp, "diet_type")
    recycling_score = _get_val(inp, "recycling_score")
    plastic_usage_score = _get_val(inp, "plastic_usage_score")
    household_size = _get_val(inp, "household_size")
    assessment_period = _get_val(inp, "assessment_period", "monthly")

    # Tracking factors database version + passing inputs to extensions
    version_tracker = {"factor_version": DEFAULT_FACTOR_VERSION, "_inp": inp}
    
    if db is not None:
        try:
            factors = db.query(CarbonFactor).all()
            version_tracker["_factors"] = {(f.category, f.sub_category): f for f in factors}
        except Exception as e:
            logger.warning(f"Failed to prefetch carbon factors: {e}")

    # Calculations
    transport_emission = calculate_transport(
        transport_mode=transport_mode,
        distance_km=distance_km,
        db=db,
        version_tracker=version_tracker
    )

    energy_emission = calculate_energy(
        electricity_kwh=electricity_kwh,
        ac_hours=ac_hours,
        lpg_usage=lpg_usage,
        solar_usage=solar_usage,
        db=db,
        version_tracker=version_tracker
    )

    food_emission = calculate_food(
        diet_type=diet_type,
        household_size=household_size,
        db=db,
        version_tracker=version_tracker,
        assessment_period=assessment_period
    )

    waste_emission = calculate_waste(
        recycling_score=recycling_score,
        plastic_usage_score=plastic_usage_score,
        db=db,
        version_tracker=version_tracker
    )

    housing_emission = calculate_housing(inp)
    water_emission = calculate_water(inp)
    digital_emission = calculate_digital(inp)
    shopping_emission = calculate_shopping(inp)
    offsets_total = calculate_offsets(inp)

    raw_total = (
        transport_emission + energy_emission + food_emission + waste_emission
        + housing_emission + water_emission + digital_emission + shopping_emission
    )
    total_emission = float(max(0.0, raw_total - offsets_total))

    # Score calculation
    normalized_impact = (total_emission / BASELINE_MONTHLY_EMISSION) * 100.0
    carbon_score = int(round(100.0 - normalized_impact))
    carbon_score = max(0, min(100, carbon_score))

    return {
        "transport_emission": transport_emission,
        "energy_emission": energy_emission,
        "food_emission": food_emission,
        "waste_emission": waste_emission,
        "housing_emission": housing_emission,
        "water_emission": water_emission,
        "digital_emission": digital_emission,
        "shopping_emission": shopping_emission,
        "offsets_total": offsets_total,
        "total_emission": total_emission,
        "carbon_score": carbon_score,
        "calculation_version": CALCULATION_VERSION,
        "factor_version": version_tracker["factor_version"],
    }
