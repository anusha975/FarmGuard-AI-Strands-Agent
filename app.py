"""
FarmGuard AI - Multi-Agent Climate Resilience Assistant for Smallholder Farmers.
Interactive Streamlit Application powered by AWS Strands Agents SDK & Amazon Bedrock.
Supports English & Telugu (తెలుగు) localization, live/simulated telemetry badges, and safety disclaimers.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from farmguard.models import FarmProfile, FarmGuardDiagnosis
from farmguard.orchestrator import FarmGuardOrchestrator
from farmguard.config import settings
from farmguard.data.crop_knowledge import CROP_DATABASE, SOIL_PROPERTIES
from farmguard.data.telugu_translations import (
    TELUGU_CROPS,
    TELUGU_SOILS,
    TELUGU_STAGES,
    TELUGU_HAZARDS
)
from farmguard.utils.safety import get_safety_disclaimer, validate_coordinates

# Streamlit Page Setup
st.set_page_config(
    page_title="FarmGuard AI - Climate Resilience Assistant",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Contrast CSS Styling
st.markdown("""
<style>
    .main-title { font-size: 2.2rem; font-weight: 800; color: #1B5E20; margin-bottom: 0.1rem; }
    .sub-title { font-size: 1.05rem; color: #374151; margin-bottom: 1.2rem; }
    .badge-live {
        background-color: #E8F5E9; color: #2E7D32; border: 1.5px solid #4CAF50;
        padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: 700; font-size: 0.82rem;
    }
    .badge-sim {
        background-color: #FFF3E0; color: #E65100; border: 1.5px solid #FF9800;
        padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: 700; font-size: 0.82rem;
    }
    .status-pill {
        padding: 0.35rem 0.9rem; border-radius: 9999px; font-weight: 700; font-size: 0.85rem;
        display: inline-block; text-transform: uppercase;
    }
    .pill-emergency { background-color: #FFEBEE; color: #C62828; border: 1px solid #EF5350; }
    .pill-warning { background-color: #FFF3E0; color: #E65100; border: 1px solid #FFB74D; }
    .pill-advisory { background-color: #FFFDE7; color: #F57F17; border: 1px solid #FFF176; }
    .pill-normal { background-color: #E8F5E9; color: #2E7D32; border: 1px solid #81C784; }
    .card-metric {
        background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px;
        padding: 1rem; box-shadow: 0 1px 4px rgba(0,0,0,0.04); margin-bottom: 0.8rem;
    }
    .action-pill {
        background: #F0FDF4; border-left: 5px solid #16A34A; padding: 0.8rem 1rem;
        border-radius: 4px; margin-bottom: 0.6rem; font-size: 0.95rem; color: #166534;
    }
    .disclaimer-box {
        background: #FEF2F2; border: 1.5px solid #F87171; border-radius: 8px;
        padding: 1rem 1.2rem; color: #991B1B; font-size: 0.88rem; margin-top: 1.5rem;
    }
    .sms-container {
        background: #1E293B; color: #F8FAFC; font-family: monospace;
        padding: 1rem; border-radius: 8px; white-space: pre-wrap; font-size: 0.92rem;
    }
</style>
""", unsafe_allow_html=True)

# Smallholder Benchmark Presets (including Andhra Pradesh & Telangana regions)
REGIONAL_PRESETS = {
    "Anantapur, Andhra Pradesh (Arid Rayalaseema - Groundnut)": {"lat": 14.68, "lon": 77.60, "crop": "Groundnut (Peanut)", "soil": "Sandy Loam"},
    "Mahabubnagar, Telangana (Semi-Arid Dryland - Maize/Pigeonpea)": {"lat": 16.74, "lon": 78.00, "crop": "Maize (Corn)", "soil": "Clay / Black Cotton Soil (Vertisol)"},
    "Guntur, Andhra Pradesh (Krishna-Godavari Zone - Chillies/Pulses)": {"lat": 16.30, "lon": 80.44, "crop": "Chickpea (Gram)", "soil": "Clay Loam"},
    "Warangal, Telangana (Central Plateau - Cotton/Rice)": {"lat": 17.96, "lon": 79.59, "crop": "Rice (Lowland / Paddy)", "soil": "Loam"},
    "Vidarbha, Maharashtra (Deccan Dryland - Cotton/Pulses)": {"lat": 20.93, "lon": 77.75, "crop": "Chickpea (Gram)", "soil": "Clay / Black Cotton Soil (Vertisol)"},
    "Dodoma, Tanzania (East Africa Savanna - Sorghum)": {"lat": -6.16, "lon": 35.74, "crop": "Sorghum", "soil": "Sandy Loam"},
    "Custom GPS Coordinates": {"lat": 15.00, "lon": 78.00, "crop": "Maize (Corn)", "soil": "Loam"}
}

def render_sidebar():
    st.sidebar.image("https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=400&q=80", use_container_width=True)
    st.sidebar.title("🌾 ఫామ్‌గార్డ్ | Farm Profile")
    
    # Language Selector
    lang_choice = st.sidebar.radio("🌐 Language / భాష:", ["English", "తెలుగు (Telugu)"], index=0)
    language_code = "te" if "తెలుగు" in lang_choice else "en"
    
    st.sidebar.markdown("---")
    
    # Preset Selector
    preset_key = st.sidebar.selectbox("📍 Regional Benchmark Presets:", list(REGIONAL_PRESETS.keys()))
    preset = REGIONAL_PRESETS[preset_key]
    
    farmer_name = st.sidebar.text_input("Farmer Name / రైతు పేరు:", value="రమేష్ నాయుడు (Ramesh Naidu)" if language_code == "te" else "Ramesh Naidu")
    location_name = st.sidebar.text_input("Village / Location:", value=preset_key.split(" (")[0])
    
    c1, c2 = st.sidebar.columns(2)
    with c1:
        lat = st.number_input("Latitude (°N):", value=preset["lat"], format="%.4f")
    with c2:
        lon = st.number_input("Longitude (°E):", value=preset["lon"], format="%.4f")
        
    crop_list = list(CROP_DATABASE.keys())
    crop_display = [f"{c} | {TELUGU_CROPS.get(c, '')}" for c in crop_list]
    default_crop_idx = crop_list.index(preset["crop"]) if preset["crop"] in crop_list else 0
    selected_crop_display = st.sidebar.selectbox("Crop / సాగు చేస్తున్న పంట:", crop_display, index=default_crop_idx)
    crop_name = crop_list[crop_display.index(selected_crop_display)]
    
    stages = ["Germination/Seedling", "Vegetative", "Flowering/Anthesis", "Grain Filling/Tuber Bulking", "Maturity/Harvest"]
    stages_display = [f"{s} | {TELUGU_STAGES.get(s, '')}" for s in stages]
    selected_stage_display = st.sidebar.selectbox("Growth Stage / దశ:", stages_display, index=2)
    growth_stage = stages[stages_display.index(selected_stage_display)]
    
    soils = list(SOIL_PROPERTIES.keys())
    soils_display = [f"{s} | {TELUGU_SOILS.get(s, '')}" for s in soils]
    default_soil_idx = soils.index(preset["soil"]) if preset["soil"] in soils else 0
    selected_soil_display = st.sidebar.selectbox("Soil Type / నేల రకం:", soils_display, index=default_soil_idx)
    soil_type = soils[soils_display.index(selected_soil_display)]
    
    irrigation_options = [
        "Rainfed Only (వర్షాధారం మాత్రమే)",
        "Borewell / Tube-well (బోరుబావి)",
        "Drip System (బిందు సేద్యం)",
        "Canal / Furrow Flood (కాలువ నీరు)",
        "Farm Pond (రైతు కుంట)"
    ]
    irr_selected = st.sidebar.selectbox("Water Source / నీటి వసతి:", irrigation_options, index=0)
    irrigation_access = irr_selected.split(" (")[0]
    
    field_size = st.sidebar.slider("Field Size (Acres/Ha):", min_value=0.5, max_value=25.0, value=2.0, step=0.5)
    
    st.sidebar.markdown("---")
    st.sidebar.caption(f"🤖 Strands SDK Engine: Active | Region: {settings.AWS_REGION}")
    run_btn = st.sidebar.button("🚀 Run Assessment | విశ్లేషణ ప్రారంభించండి", use_container_width=True, type="primary")
    
    profile = FarmProfile(
        farmer_name=farmer_name,
        location_name=location_name,
        latitude=lat,
        longitude=lon,
        crop_name=crop_name,
        growth_stage=growth_stage,
        soil_type=soil_type,
        field_size_hectares=field_size,
        irrigation_access=irrigation_access,
        language=language_code
    )
    return profile, run_btn

def render_vulnerability_gauge(score: float, status: str, lang: str):
    title_text = "సమగ్ర కరువు & వాతావరణ ముప్పు సూచిక (CVI)" if lang == "te" else "Composite Vulnerability Index (CVI)"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title_text, 'font': {'size': 16, 'color': '#1F2937'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#9CA3AF"},
            'bar': {'color': "#DC2626" if score >= 70 else "#EA580C" if score >= 45 else "#CA8A04" if score >= 25 else "#16A34A"},
            'bgcolor': "white",
            'borderwidth': 1.5,
            'bordercolor': "#D1D5DB",
            'steps': [
                {'range': [0, 25], 'color': '#DCFCE7'},
                {'range': [25, 45], 'color': '#FEF9C3'},
                {'range': [45, 70], 'color': '#FFEDD5'},
                {'range': [70, 100], 'color': '#FEE2E2'}
            ],
            'threshold': {'line': {'color': "#111827", 'width': 3}, 'thickness': 0.75, 'value': score}
        }
    ))
    fig.update_layout(height=230, margin=dict(l=15, r=15, t=35, b=10))
    return fig

def render_charts(diagnosis: FarmGuardDiagnosis):
    daily = diagnosis.weather_data.daily_forecasts
    if not daily:
        st.info("No daily time-series data available.")
        return
        
    dates = [d.date for d in daily]
    t_max = [d.temp_max for d in daily]
    t_min = [d.temp_min for d in daily]
    rain = [d.precip_mm for d in daily]
    et0 = [d.et0_mm for d in daily]
    
    col1, col2 = st.columns(2)
    with col1:
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(x=dates, y=t_max, name="Max Temp (°C)", line=dict(color="#EF4444", width=3)))
        fig_temp.add_trace(go.Scatter(x=dates, y=t_min, name="Min Temp (°C)", line=dict(color="#3B82F6", width=2, dash='dot')))
        crit_t = CROP_DATABASE.get(diagnosis.farm_profile.crop_name, {}).get("critical_temp_max_c", 35.0)
        fig_temp.add_hline(y=crit_t, line_dash="dash", line_color="#B91C1C", annotation_text=f"Thermal Stress Limit ({crit_t}°C)")
        fig_temp.update_layout(title="🌡️ 7-Day Temperature vs. Crop Thermal Limit", xaxis_title="Date", yaxis_title="°C", height=300, margin=dict(l=10, r=10, t=35, b=10))
        st.plotly_chart(fig_temp, use_container_width=True)
        
    with col2:
        fig_water = go.Figure()
        fig_water.add_trace(go.Bar(x=dates, y=rain, name="Rainfall (mm)", marker_color="#0284C7"))
        fig_water.add_trace(go.Scatter(x=dates, y=et0, name="Evaporative Demand ET0 (mm)", line=dict(color="#D97706", width=3)))
        fig_water.update_layout(title="💧 7-Day Moisture Balance: Rain vs. Evapotranspiration", xaxis_title="Date", yaxis_title="mm", height=300, margin=dict(l=10, r=10, t=35, b=10))
        st.plotly_chart(fig_water, use_container_width=True)

def main():
    profile, run_btn = render_sidebar()
    lang = profile.language
    is_te = (lang == "te")
    
    # Header
    title_text = "🌾 ఫామ్‌గార్డ్ ఏఐ (FarmGuard AI)" if is_te else "🌾 FarmGuard AI"
    subtitle_text = (
        "చిన్నకారు రైతుల కోసం బహుళ-ఏజెంట్ వాతావరణ కరువు సంరక్షణ సహాయకుడు | AWS స్ట్రాండ్స్ ఏజెంట్స్ SDK & అమెజాన్ బెడ్‌రాక్"
        if is_te else
        "Multi-Agent Climate Resilience Assistant for Smallholder Farmers | Powered by AWS Strands Agents SDK & Amazon Bedrock"
    )
    st.markdown(f'<div class="main-title">{title_text}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title">{subtitle_text}</div>', unsafe_allow_html=True)
    
    # Orchestrator Session
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = FarmGuardOrchestrator()
        
    # Execution
    if "diagnosis" not in st.session_state or run_btn:
        with st.spinner("🤖 Strands Orchestrator Agent is analyzing agro-climate telemetry..."):
            try:
                diag = st.session_state.orchestrator.run_diagnosis(profile)
                st.session_state.diagnosis = diag
            except Exception as e:
                st.error(f"Execution Error: {e}")
                return
    else:
        diag = st.session_state.diagnosis
        
    # Top Information Bar & Live/Simulated Badge
    badge_class = "badge-sim" if diag.is_simulated else "badge-live"
    status_pill_class = "pill-emergency" if "EMERGENCY" in diag.overall_status or "తీవ్ర" in diag.overall_status else "pill-warning" if "WARNING" in diag.overall_status or "అధిక" in diag.overall_status else "pill-advisory" if "ADVISORY" in diag.overall_status or "జాగ్రత్త" in diag.overall_status else "pill-normal"
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; margin-bottom: 1rem; gap: 0.5rem; background: #F8FAFC; padding: 0.8rem 1rem; border-radius: 8px; border: 1px solid #E2E8F0;">
        <div><b>📍 {diag.farm_profile.location_name}</b> | <b>{diag.farm_profile.crop_name}</b> ({diag.farm_profile.growth_stage})</div>
        <div>
            <span class="{badge_class}">{diag.data_source_badge}</span>
            <span class="status-pill {status_pill_class}">{diag.overall_status}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Gauges & Risk Summary
    col_g, col_metrics = st.columns([1, 2])
    with col_g:
        st.plotly_chart(render_vulnerability_gauge(diag.risk_assessment.composite_vulnerability_index, diag.overall_status, lang), use_container_width=True)
        st.caption(f"GPS: {diag.farm_profile.latitude:.4f}°N, {diag.farm_profile.longitude:.4f}°E | Field: {diag.farm_profile.field_size_hectares} ha")
        
    with col_metrics:
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"""
            <div class="card-metric">
                <div style="font-weight: 700; color: #374151;">☀️ {'కరువు ప్రమాదం' if is_te else 'Drought Deficit Risk'}</div>
                <div style="font-size: 1.6rem; font-weight: 800; color: #DC2626;">{diag.risk_assessment.drought_score_pct:.0f}% <span style="font-size: 0.85rem;">({diag.risk_assessment.drought_level})</span></div>
                <div style="font-size: 0.82rem; color: #6B7280;">7-Day Net Deficit: {diag.weather_data.net_water_balance_mm:.1f} mm</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="card-metric">
                <div style="font-weight: 700; color: #374151;">🌱 {'నేల తేమ కొరత (CWSI)' if is_te else 'Rootzone Water Stress (CWSI)'}</div>
                <div style="font-size: 1.6rem; font-weight: 800; color: #DC2626;">{int(diag.soil_data.crop_water_stress_index_cwsi * 100)}% <span style="font-size: 0.85rem;">({diag.soil_data.stress_level})</span></div>
                <div style="font-size: 0.82rem; color: #6B7280;">Moisture: {diag.soil_data.current_moisture_pct:.1f}% (FC: {diag.soil_data.field_capacity_pct}%)</div>
            </div>
            """, unsafe_allow_html=True)
            
        with m2:
            st.markdown(f"""
            <div class="card-metric">
                <div style="font-weight: 700; color: #374151;">🔥 {'ఎండ తీవ్రత / వడగాలులు' if is_te else 'Heatwave & Thermal Stress'}</div>
                <div style="font-size: 1.6rem; font-weight: 800; color: #DC2626;">{diag.risk_assessment.heatwave_score_pct:.0f}% <span style="font-size: 0.85rem;">({diag.risk_assessment.heatwave_level})</span></div>
                <div style="font-size: 0.82rem; color: #6B7280;">Peak Temp: {diag.weather_data.max_forecast_temp_c}°C ({diag.weather_data.heatwave_days_count} heat days)</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="card-metric">
                <div style="font-weight: 700; color: #374151;">🌧️ {'భారీ వర్షాలు / వరద' if is_te else 'Excessive Rain / Flood'}</div>
                <div style="font-size: 1.6rem; font-weight: 800; color: #16A34A;">{diag.risk_assessment.flood_score_pct:.0f}% <span style="font-size: 0.85rem;">({diag.risk_assessment.flood_level})</span></div>
                <div style="font-size: 0.82rem; color: #6B7280;">7-Day Total Rain: {diag.weather_data.total_precipitation_7d_mm:.1f} mm</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Charts
    st.subheader("📊 " + ("వాతావరణ టెలిమెట్రీ & తేమ సమతుల్యత" if is_te else "Agro-Weather Telemetry & Crop Water Dynamics"))
    render_charts(diag)
    
    st.markdown("---")
    
    # Detailed Tabs
    t1, t2, t3, t4 = st.tabs([
        "🚨 " + ("తక్షణ చర్యలు & సిఫార్సులు" if is_te else "Immediate Action Plan"),
        "🤖 " + ("స్ట్రాండ్స్ ఏజెంట్ లూప్ ట్రేస్" if is_te else "Strands Agent Execution Trace"),
        "💧 " + ("నేల నీటి భౌతిక విశ్లేషణ" if is_te else "FAO-56 Soil Water Balance"),
        "📱 " + ("రైతు మొబైల్ SMS అలర్ట్" if is_te else "2G SMS / IVR Broadcast Alert")
    ])
    
    with t1:
        st.markdown("### " + ("⚡ తక్షణమే చేపట్టవలసిన పనులు (రాబోయే 24-48 గంటలు)" if is_te else "⚡ Prioritized Immediate Tactical Interventions (Next 24-48 Hours)"))
        for act in diag.immediate_actions:
            st.markdown(f'<div class="action-pill">{act}</div>', unsafe_allow_html=True)
            
        st.markdown("### " + ("🛡️ దీర్ఘకాలిక కరువు సంరక్షణ పద్ధతులు" if is_te else "🛡️ Long-Term Agronomic Resilience Practices"))
        for rec in diag.resilience_recommendations:
            st.markdown(f"- **{rec}**")
            
    with t2:
        st.markdown("### " + ("🧠 అధికారిక AWS స్ట్రాండ్స్ ఏజెంట్ టూల్స్ ట్రాన్స్పరెన్సీ" if is_te else "🧠 Official AWS Strands Agent Tool Invocation Trace"))
        st.caption("Inspect the actual tools called, execution latencies, and data authenticity flags.")
        for trace in diag.tool_execution_trace:
            with st.expander(f"🔧 Tool: `{trace['tool']}` | Latency: {trace['duration_sec']}s", expanded=True):
                st.write(f"**Data Source:** {trace['data_source']}")
                st.write(f"**Telemetry Summary:** {trace['summary']}")
                
    with t3:
        st.markdown("### " + ("🔬 ఎఫ్.ఎ.ఓ-56 శాస్త్రీయ నేల తేమ వివరాలు" if is_te else "🔬 FAO-56 Scientific Soil Moisture & Water Balance"))
        sd = diag.soil_data
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("Total Available Water (TAW)", f"{sd.total_available_water_taw_mm} mm")
        col_s2.metric("Readily Available Buffer (RAW)", f"{sd.readily_available_water_raw_mm} mm")
        col_s3.metric("Rootzone Depletion (Dr)", f"{sd.rootzone_depletion_mm} mm")
        st.info(f"**Soil Management Directive:** {sd.soil_management_tip}")
        
    with t4:
        st.markdown("### " + ("📲 తక్కువ బ్యాండ్‌విడ్త్ 2G SMS మెసేజ్" if is_te else "📲 Low-Bandwidth 2G SMS / Audio Broadcast Card"))
        st.caption("Suitable for rural cellular dispatch, voice IVR, or regional radio alerts.")
        st.markdown(f'<div class="sms-container">{diag.sms_alert_message}</div>', unsafe_allow_html=True)
        st.text_area("Copy SMS Text to Clipboard:", value=diag.sms_alert_message, height=120)
        
    # Responsible AI & Agricultural Safety Disclaimer Banner
    st.markdown(f'<div class="disclaimer-box">{diag.safety_disclaimer}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
