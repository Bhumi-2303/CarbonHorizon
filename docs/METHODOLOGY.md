# Carbon Horizon Methodology

This document outlines the scientific methodology and data sources used to calculate the personal carbon footprints in the Carbon Horizon platform. 

The core philosophy of Carbon Horizon is **transparency and accuracy**. To ensure our numbers reflect reality, all emission factors are drawn from reputable international bodies.

## Core Sources

Our emission factors and calculations are derived from the following sources:
1. **IPCC (Intergovernmental Panel on Climate Change)** - 2006 IPCC Guidelines for National Greenhouse Gas Inventories.
2. **EPA (Environmental Protection Agency)** - Greenhouse Gas Equivalencies Calculator and Emission Factors Hub (2023).
3. **IEA (International Energy Agency)** - Emissions per kWh of electricity by country/region.
4. **DEFRA (UK Department for Environment, Food & Rural Affairs)** - Transportation emission factors.

## Calculation Engine

The formula applied across all categories is a standard activity-based calculation:
```
Carbon Emissions (kg CO₂e) = Activity Data × Emission Factor
```

### 1. Energy & Utilities
We calculate emissions based on typical household usage and grid averages.
* **Electricity**: Calculated using EPA/IEA grid averages. (e.g., ~0.385 kg CO₂e per kWh globally, varying by region).
* **Heating/Gas**: Calculated per therm or per kWh of natural gas/oil combusted in the household.

### 2. Transportation
Transportation is divided into commuting and air travel.
* **Car Commute**: Depends on fuel efficiency (MPG / L/100km). Average ICE (Internal Combustion Engine) vehicle: `0.192 kg CO₂e / km`. EV: Depends on local grid emissions.
* **Public Transit**: Defra averages used (e.g., Bus: `0.105 kg CO₂e / km`, Train: `0.041 kg CO₂e / km`).
* **Air Travel**: Short-haul vs long-haul flights use distinct emission factors to account for takeoff/landing ratios and high-altitude radiative forcing.

### 3. Diet & Food
Food emissions use lifecycle analyses (LCA) from sources like the *Poore & Nemecek (2018) Science* study.
* **Meat-Heavy Diet**: ~3.3 kg CO₂e per day
* **Average/Balanced Diet**: ~2.5 kg CO₂e per day
* **Vegetarian Diet**: ~1.7 kg CO₂e per day
* **Vegan Diet**: ~1.5 kg CO₂e per day

### 4. Shopping & Lifestyle
This category captures indirect (Scope 3-like) emissions.
* **Clothing & Goods**: Averages based on purchasing frequency (e.g., fast fashion vs sustainable purchasing).
* **Waste & Recycling**: Credit given for recycling and composting based on EPA waste reduction models.

## Future Iterations
Currently, global averages are heavily utilized. In future updates, the application will integrate granular location-based grid emission factors to improve accuracy for individual regions.
