"""
Agro-meteorological and crop reference data based on FAO-56 Irrigation and Drainage guidelines,
specifically tailored for smallholder farming climate resilience.
"""

# Crop hydrological and thermal properties
CROP_DATABASE = {
    "Maize (Corn)": {
        "scientific_name": "Zea mays",
        "category": "Cereal",
        "kc": {"initial": 0.40, "mid": 1.20, "end": 0.60},
        "rooting_depth_m": {"initial": 0.3, "mid": 1.0, "max": 1.2},
        "depletion_fraction_p": 0.55,
        "critical_temp_max_c": 36.0,  # Anthesis / pollen sterility risk above 35-36°C
        "optimal_temp_range": (18.0, 32.0),
        "drought_tolerance": "Moderate",
        "resilience_interventions": [
            "Apply 5-8 cm organic crop residue mulch to preserve topsoil moisture",
            "Implement deficit irrigation during vegetative phase; prioritize water during tasseling/silking",
            "Plant heat-tolerant / short-duration hybrid varieties (e.g., DTMA cultivars)",
            "Practice tied-ridge planting or conservation tillage to capture localized runoff"
        ]
    },
    "Sorghum": {
        "scientific_name": "Sorghum bicolor",
        "category": "Cereal (Climate Hardy)",
        "kc": {"initial": 0.35, "mid": 1.05, "end": 0.55},
        "rooting_depth_m": {"initial": 0.3, "mid": 1.2, "max": 1.5},
        "depletion_fraction_p": 0.65,
        "critical_temp_max_c": 40.0,
        "optimal_temp_range": (24.0, 35.0),
        "drought_tolerance": "High",
        "resilience_interventions": [
            "Dig Zai pits or half-moon water-retention basins before sowing",
            "Thin seedlings early if prolonged early-season drought occurs",
            "Apply localized micro-dose compost in seed basins"
        ]
    },
    "Pearl Millet": {
        "scientific_name": "Pennisetum glaucum",
        "category": "Cereal (Extreme Dryland)",
        "kc": {"initial": 0.30, "mid": 1.00, "end": 0.45},
        "rooting_depth_m": {"initial": 0.25, "mid": 1.0, "max": 1.4},
        "depletion_fraction_p": 0.68,
        "critical_temp_max_c": 42.0,
        "optimal_temp_range": (26.0, 38.0),
        "drought_tolerance": "Very High",
        "resilience_interventions": [
            "Use contour stone bunds to trap intermittent rainfall",
            "Intercrop with drought-hardy legumes (e.g., cowpea or pigeon pea) to retain nitrogen and groundcover",
            "Store early-harvest biomass as silage if severe terminal drought prevents grain filling"
        ]
    },
    "Wheat": {
        "scientific_name": "Triticum aestivum",
        "category": "Cereal",
        "kc": {"initial": 0.35, "mid": 1.15, "end": 0.40},
        "rooting_depth_m": {"initial": 0.3, "mid": 1.0, "max": 1.3},
        "depletion_fraction_p": 0.55,
        "critical_temp_max_c": 32.0,  # Terminal heat stress in late reproductive phase
        "optimal_temp_range": (15.0, 24.0),
        "drought_tolerance": "Moderate",
        "resilience_interventions": [
            "Apply light evening sprinkler/flood irrigation during heading stage to reduce canopy temperature",
            "Adopt Zero-Tillage (ZT) seeding to retain residual soil moisture from previous crop",
            "Use potassium nitrate (1%) foliar spray to bolster membrane stability against terminal heatwave"
        ]
    },
    "Rice (Lowland / Paddy)": {
        "scientific_name": "Oryza sativa",
        "category": "Cereal (Wetland)",
        "kc": {"initial": 1.05, "mid": 1.25, "end": 0.90},
        "rooting_depth_m": {"initial": 0.2, "mid": 0.5, "max": 0.7},
        "depletion_fraction_p": 0.20,
        "critical_temp_max_c": 35.0,
        "optimal_temp_range": (22.0, 32.0),
        "drought_tolerance": "Low",
        "resilience_interventions": [
            "Transition to Alternate Wetting and Drying (AWD) irrigation to save up to 30% water",
            "Strengthen paddy field bunds to prevent runoff loss from sudden unseasonal downpours",
            "Use direct-seeded rice (DSR) techniques in drought-prone upland zones"
        ]
    },
    "Chickpea (Gram)": {
        "scientific_name": "Cicer arietinum",
        "category": "Pulses / Legume",
        "kc": {"initial": 0.40, "mid": 1.00, "end": 0.35},
        "rooting_depth_m": {"initial": 0.25, "mid": 0.8, "max": 1.0},
        "depletion_fraction_p": 0.60,
        "critical_temp_max_c": 35.0,
        "optimal_temp_range": (18.0, 28.0),
        "drought_tolerance": "High",
        "resilience_interventions": [
            "Utilize deep furrow planting to reach residual subsoil moisture",
            "Apply straw mulch to mitigate soil cracking and moisture vaporization in clay soils",
            "Schedule single supplemental protective irrigation at pre-flowering"
        ]
    },
    "Groundnut (Peanut)": {
        "scientific_name": "Arachis hypogaea",
        "category": "Oilseed / Legume",
        "kc": {"initial": 0.40, "mid": 1.15, "end": 0.60},
        "rooting_depth_m": {"initial": 0.3, "mid": 0.8, "max": 1.0},
        "depletion_fraction_p": 0.50,
        "critical_temp_max_c": 37.0,
        "optimal_temp_range": (22.0, 32.0),
        "drought_tolerance": "Moderate to High",
        "resilience_interventions": [
            "Apply gypsum at pegging stage to ensure pod filling even under moisture stress",
            "Implement broad bed and furrow (BBF) systems for dual drainage and moisture conservation",
            "Avoid excessive nitrogen fertilization during high heat"
        ]
    },
    "Tomato": {
        "scientific_name": "Solanum lycopersicum",
        "category": "Horticultural / Vegetable",
        "kc": {"initial": 0.60, "mid": 1.15, "end": 0.80},
        "rooting_depth_m": {"initial": 0.25, "mid": 0.7, "max": 1.0},
        "depletion_fraction_p": 0.40,
        "critical_temp_max_c": 34.0,  # Blossom drop occurs above 34°C
        "optimal_temp_range": (20.0, 30.0),
        "drought_tolerance": "Low",
        "resilience_interventions": [
            "Erect 30% agro-shade net canopy over nursery beds during severe heatwaves",
            "Use drip irrigation with localized plastic or organic straw mulch",
            "Harvest breaker-stage fruit early if extreme heatwave (>38°C) is forecasted"
        ]
    }
}

# Soil hydraulic characteristics (volumetric moisture content %: m3 water / m3 soil * 100)
SOIL_PROPERTIES = {
    "Sandy Soil": {
        "field_capacity_pct": 12.0,
        "permanent_wilting_point_pct": 4.0,
        "available_water_capacity_mm_per_m": 80.0,
        "infiltration_rate": "Very Rapid",
        "drought_vulnerability": "Extreme",
        "management_tip": "High leaching risk. Frequent, small-volume irrigations with abundant organic manure."
    },
    "Sandy Loam": {
        "field_capacity_pct": 18.0,
        "permanent_wilting_point_pct": 8.0,
        "available_water_capacity_mm_per_m": 100.0,
        "infiltration_rate": "Rapid",
        "drought_vulnerability": "High",
        "management_tip": "Good drainage but quick drying. Retain stubble mulch and add compost."
    },
    "Loam": {
        "field_capacity_pct": 27.0,
        "permanent_wilting_point_pct": 12.0,
        "available_water_capacity_mm_per_m": 150.0,
        "infiltration_rate": "Moderate",
        "drought_vulnerability": "Moderate",
        "management_tip": "Balanced water holding capacity and aeration. Ideal for standard deficit scheduling."
    },
    "Clay Loam": {
        "field_capacity_pct": 32.0,
        "permanent_wilting_point_pct": 16.0,
        "available_water_capacity_mm_per_m": 160.0,
        "infiltration_rate": "Moderately Slow",
        "drought_vulnerability": "Moderate to Low",
        "management_tip": "High water retention; prone to surface crusting if dried abruptly after heavy rain."
    },
    "Clay / Black Cotton Soil (Vertisol)": {
        "field_capacity_pct": 40.0,
        "permanent_wilting_point_pct": 22.0,
        "available_water_capacity_mm_per_m": 180.0,
        "infiltration_rate": "Slow",
        "drought_vulnerability": "Low to Moderate",
        "management_tip": "Expansive clay prone to deep shrinking cracks during drought; mulching is essential to avoid root shearing."
    },
    "Silt Loam": {
        "field_capacity_pct": 30.0,
        "permanent_wilting_point_pct": 13.0,
        "available_water_capacity_mm_per_m": 170.0,
        "infiltration_rate": "Moderate",
        "drought_vulnerability": "Low",
        "management_tip": "High water holding capacity; avoid compaction by heavy tillage."
    }
}
