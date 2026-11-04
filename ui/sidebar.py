"""
Sidebar input controls and profile configuration for FarmGuard AI.
Collects location, crop, observed temperature, rainfall, soil moisture, and language choice.
"""
import streamlit as st
from typing import Tuple, Dict, Any
from farmguard.data.crop_knowledge import CROP_DATABASE, SOIL_PROPERTIES
from farmguard.data.telugu_translations import TELUGU_CROPS, TELUGU_SOILS, TELUGU_STAGES

BENCHMARKS = {
    "Mahabubnagar, Telangana (Semi-Arid Dryland - Maize)": {"lat": 16.74, "lon": 78.00, "crop": "Maize (Corn)", "soil": "Clay / Black Cotton Soil (Vertisol)", "temp": 37.0, "rain": 2.5, "sm": 18.0},
    "Warangal, Telangana (Northern Telangana - Paddy/Rice)": {"lat": 17.96, "lon": 79.59, "crop": "Rice (Lowland / Paddy)", "soil": "Loam", "temp": 34.0, "rain": 12.0, "sm": 32.0},
    "Nalgonda, Telangana (Dryland / Red Chalkas - Groundnut/Cotton)": {"lat": 17.05, "lon": 79.27, "crop": "Groundnut (Peanut)", "soil": "Sandy Loam", "temp": 36.5, "rain": 0.0, "sm": 14.0},
    "Anantapur, Andhra Pradesh (Arid Rayalaseema - Groundnut)": {"lat": 14.68, "lon": 77.60, "crop": "Groundnut (Peanut)", "soil": "Sandy Loam", "temp": 36.5, "rain": 0.0, "sm": 14.0},
    "Guntur, Andhra Pradesh (Coastal/Krishna Basin - Chickpea)": {"lat": 16.30, "lon": 80.44, "crop": "Chickpea (Gram)", "soil": "Clay Loam", "temp": 35.0, "rain": 0.0, "sm": 20.0},
    "Vidarbha, Maharashtra (Semi-Arid Dryland - Chickpea/Cotton)": {"lat": 20.93, "lon": 77.75, "crop": "Chickpea (Gram)", "soil": "Clay / Black Cotton Soil (Vertisol)", "temp": 38.0, "rain": 0.0, "sm": 16.0},
    "Custom Location (స్వంత స్థానం)": {"lat": 17.38, "lon": 78.48, "crop": "Maize (Corn)", "soil": "Loam", "temp": 34.0, "rain": 5.0, "sm": 20.0}
}

def render_sidebar() -> Tuple[Dict[str, Any], bool]:
    """Render the sidebar inputs and return (profile_dict, analyze_button_clicked)."""
    st.sidebar.image("https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=400&q=80", use_container_width=True)
    st.sidebar.markdown("## 🌾 ఫామ్‌గార్డ్ | Farm Profile")

    # 1. English / Telugu Selection
    lang_choice = st.sidebar.radio(
        "🌐 Language / భాష:",
        ["English", "తెలుగు (Telugu)"],
        index=0,
        horizontal=True
    )
    lang_code = "te" if "తెలుగు" in lang_choice else "en"
    is_te = (lang_code == "te")

    st.sidebar.markdown("---")

    # 2. Regional Benchmark Selector
    preset_label = "📍 Regional Benchmarks / ప్రాంతీయ నమూనాలు:" if is_te else "📍 Regional Benchmarks:"
    selected_preset = st.sidebar.selectbox(preset_label, list(BENCHMARKS.keys()), index=0)
    preset_data = BENCHMARKS[selected_preset]

    # 3. Location Inputs
    loc_label = "Location / ప్రాంతం పేరు:" if is_te else "Farmer / Village Location:"
    location_name = st.sidebar.text_input(loc_label, value=selected_preset.split(" (")[0])

    col_lat, col_lon = st.sidebar.columns(2)
    with col_lat:
        lat = st.number_input("Latitude (°N):", value=preset_data["lat"], format="%.4f")
    with col_lon:
        lon = st.number_input("Longitude (°E):", value=preset_data["lon"], format="%.4f")

    # 4. Crop Selection
    crop_list = list(CROP_DATABASE.keys())
    crop_display = [f"{c} ({TELUGU_CROPS.get(c, '')})" if is_te else c for c in crop_list]
    default_crop_idx = crop_list.index(preset_data["crop"]) if preset_data["crop"] in crop_list else 0
    selected_crop_str = st.sidebar.selectbox("Cultivated Crop / సాగు చేస్తున్న పంట:", crop_display, index=default_crop_idx)
    crop_name = crop_list[crop_display.index(selected_crop_str)]

    # 5. Phenological Stage
    stages = ["Germination/Seedling", "Vegetative", "Flowering/Anthesis", "Grain Filling/Tuber Bulking", "Maturity/Harvest"]
    stage_display = [f"{s} ({TELUGU_STAGES.get(s, '')})" if is_te else s for s in stages]
    selected_stage_str = st.sidebar.selectbox("Growth Stage / పంట దశ:", stage_display, index=2)
    growth_stage = stages[stage_display.index(selected_stage_str)]

    # 6. Soil Texture
    soils = list(SOIL_PROPERTIES.keys())
    soil_display = [f"{s} ({TELUGU_SOILS.get(s, '')})" if is_te else s for s in soils]
    default_soil_idx = soils.index(preset_data["soil"]) if preset_data["soil"] in soils else 0
    selected_soil_str = st.sidebar.selectbox("Soil Type / నేల రకం:", soil_display, index=default_soil_idx)
    soil_type = soils[soil_display.index(selected_soil_str)]

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🌡️ Field Telemetry Observations")
    st.sidebar.caption("Override with your actual farm meter readings, or let live satellite/weather telemetry populate them automatically.")

    # 7. Temperature Input
    temp_label = "Current Observed Max Temp (°C) / గరిష్ట ఉష్ణోగ్రత:" if is_te else "Observed Peak Temp (°C):"
    temp_input = st.sidebar.slider(temp_label, min_value=15.0, max_value=50.0, value=preset_data["temp"], step=0.5)

    # 8. Rainfall Input
    rain_label = "Observed 7-Day Rainfall (mm) / 7 రోజుల వర్షపాతం:" if is_te else "Observed 7-Day Rain (mm):"
    rain_input = st.sidebar.number_input(rain_label, min_value=0.0, max_value=500.0, value=preset_data["rain"], step=1.0)

    # 9. Soil Moisture Input
    sm_label = "Measured Soil Moisture (%) / నేల తేమ శాతం:" if is_te else "Observed Soil Moisture (%):"
    sm_input = st.sidebar.slider(sm_label, min_value=2.0, max_value=60.0, value=preset_data["sm"], step=0.5)

    irrigation_options = [
        "Rainfed Only (వర్షాధారం మాత్రమే)",
        "Borewell / Tube-well (బోరుబావి)",
        "Drip System (బిందు సేద్యం)",
        "Canal / Furrow Flood (కాలువ నీరు)",
        "Water Harvesting Farm Pond (రైతు కుంట)"
    ]
    irr_selected = st.sidebar.selectbox("Water Source / నీటి వసతి:", irrigation_options, index=0)
    irrigation_access = irr_selected.split(" (")[0]

    st.sidebar.markdown("---")

    # 10. Demonstration Mode Toggle
    demo_mode = st.sidebar.checkbox(
        "🧪 Demonstration Mode / డెమో మోడ్",
        value=False,
        help="Check this ONLY to test simulated dryland conditions offline. Uncheck for real Open-Meteo live satellite weather."
    )

    # 11. Analyze Button
    btn_label = "🚀 Analyze Climate Risk | వాతావరణ ముప్పును విశ్లేషించండి" if is_te else "🚀 Analyze Climate Risk"
    analyze_btn = st.sidebar.button(btn_label, use_container_width=True, type="primary")

    st.sidebar.markdown("---")
    with st.sidebar.expander("☁️ AWS Bedrock Integration Status", expanded=False):
        from farmguard.aws_bedrock import check_aws_credentials_safe, get_bedrock_model_id
        safe_info = check_aws_credentials_safe()
        if safe_info["configured"]:
            st.success(f"🟢 AWS Connected ({safe_info['auth_method']})")
        else:
            st.warning("🟡 AWS Credentials Not Configured")
            st.caption("FarmGuard AI operates in high-reliability Agronomic Science & Tools fallback mode.")
            st.caption("To connect Amazon Bedrock Claude 3.5 Sonnet, configure `.env` (see `.env.example`).")
        st.markdown(f"**Region:** `{safe_info['region']}`")
        st.markdown(f"**Model:** `{get_bedrock_model_id().split('-2024')[0]}`")

    profile = {
        "farmer_name": "Smallholder Farmer",
        "location_name": location_name,
        "latitude": lat,
        "longitude": lon,
        "crop_name": crop_name,
        "growth_stage": growth_stage,
        "soil_type": soil_type,
        "irrigation_access": irrigation_access,
        "observed_temp_c": temp_input,
        "observed_rain_mm": rain_input,
        "observed_sm_pct": sm_input,
        "language": lang_code,
        "demo_mode": demo_mode
    }

    return profile, analyze_btn

