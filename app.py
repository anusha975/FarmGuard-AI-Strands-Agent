"""
FarmGuard AI - Multi-Agent Climate Resilience Assistant for Smallholder Farmers
Streamlit Application Powered by AWS Strands Agents SDK & Amazon Bedrock.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from farmguard.models import FarmProfile, FarmGuardDiagnosis
from farmguard.agents.orchestrator import FarmGuardOrchestrator
from farmguard.config import settings
from farmguard.data.crop_knowledge import CROP_DATABASE, SOIL_PROPERTIES

# Set Streamlit page configuration
st.set_page_config(
    page_title="FarmGuard AI - Climate Resilience Assistant",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for agricultural / high-contrast readability
st.markdown("""
<style>
    .main-header {
        font-size: 2.3rem;
        font-weight: 800;
        color: #1B5E20;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4A5568;
        margin-bottom: 1.5rem;
    }
    .status-badge {
        display: inline-block;
        padding: 0.35rem 0.8rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-right: 0.5rem;
    }
    .badge-normal { background-color: #E8F5E9; color: #2E7D32; border: 1px solid #A5D6A7; }
    .badge-advisory { background-color: #FFFDE7; color: #F57F17; border: 1px solid #FFF59D; }
    .badge-warning { background-color: #FFF3E0; color: #E65100; border: 1px solid #FFCC80; }
    .badge-emergency { background-color: #FFEBEE; color: #C62828; border: 1px solid #FFCDD2; }
    
    .risk-card {
        padding: 1.1rem;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        background: #FFFFFF;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        margin-bottom: 0.8rem;
    }
    .action-step {
        background: #F1F8E9;
        border-left: 5px solid #43A047;
        padding: 0.85rem 1.1rem;
        border-radius: 4px;
        margin-bottom: 0.6rem;
        font-size: 0.95rem;
    }
    .sms-box {
        background: #263238;
        color: #ECEFF1;
        font-family: 'Courier New', Courier, monospace;
        padding: 1.2rem;
        border-radius: 8px;
        font-size: 0.92rem;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

# Preset location coordinates for smallholder farming regions
PRESETS = {
    "Vidarbha, India (Semi-Arid Dryland - Cotton/Pulses)": {"lat": 20.93, "lon": 77.75, "crop": "Chickpea (Gram)", "soil": "Clay / Black Cotton Soil (Vertisol)"},
    "Dodoma, Tanzania (Semi-Arid Savanna - Millet/Sorghum)": {"lat": -6.16, "lon": 35.74, "crop": "Pearl Millet", "soil": "Sandy Loam"},
    "Nakuru, Rift Valley, Kenya (Sub-humid Highland - Maize)": {"lat": -0.30, "lon": 36.08, "crop": "Maize (Corn)", "soil": "Loam"},
    "Kano Drylands, Nigeria (Sahelian Zone - Sorghum/Groundnut)": {"lat": 12.00, "lon": 8.59, "crop": "Groundnut (Peanut)", "soil": "Sandy Soil"},
    "Central Dry Zone, Myanmar (Monsoon Rain Shadow - Pulses)": {"lat": 21.95, "lon": 95.88, "crop": "Chickpea (Gram)", "soil": "Sandy Loam"},
    "Custom Coordinates": {"lat": 20.59, "lon": 78.96, "crop": "Maize (Corn)", "soil": "Loam"}
}

def render_sidebar():
    st.sidebar.image("https://images.unsplash.com/photo-1500937386664-56d1dfef3854?auto=format&fit=crop&w=400&q=80", use_container_width=True)
    st.sidebar.title("🌾 Farm & Field Setup")
    
    preset_choice = st.sidebar.selectbox("Select Regional Benchmark:", list(PRESETS.keys()))
    preset_data = PRESETS[preset_choice]
    
    farmer_name = st.sidebar.text_input("Farmer / Cooperative Name:", value="Ramesh Patil")
    location_name = st.sidebar.text_input("Location / Village Name:", value=preset_choice.split(" (")[0])
    
    col_lat, col_lon = st.sidebar.columns(2)
    with col_lat:
        lat = st.number_input("Latitude (°N/S):", value=preset_data["lat"], format="%.4f")
    with col_lon:
        lon = st.number_input("Longitude (°E/W):", value=preset_data["lon"], format="%.4f")
        
    crop_list = list(CROP_DATABASE.keys())
    default_crop_idx = crop_list.index(preset_data["crop"]) if preset_data["crop"] in crop_list else 0
    crop_name = st.sidebar.selectbox("Cultivated Crop:", crop_list, index=default_crop_idx)
    
    growth_stages = ["Germination/Seedling", "Vegetative", "Flowering/Anthesis", "Grain Filling/Tuber Bulking", "Maturity/Harvest"]
    growth_stage = st.sidebar.selectbox("Growth Stage:", growth_stages, index=2)
    
    soil_list = list(SOIL_PROPERTIES.keys())
    default_soil_idx = soil_list.index(preset_data["soil"]) if preset_data["soil"] in soil_list else 0
    soil_type = st.sidebar.selectbox("Soil Texture Type:", soil_list, index=default_soil_idx)
    
    irrigation_options = ["Rainfed Only", "Borewell / Tube-well", "Drip System", "Canal / Furrow Flood", "Water Harvesting Farm Pond"]
    irrigation_access = st.sidebar.selectbox("Irrigation Access:", irrigation_options, index=0)
    
    field_size = st.sidebar.slider("Farm Field Size (Hectares):", min_value=0.2, max_value=25.0, value=1.5, step=0.1)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ System Backbone")
    aws_active = settings.is_aws_configured()
    if aws_active:
        st.sidebar.success(f"AWS Bedrock Connected ({settings.AWS_REGION})")
    else:
        st.sidebar.info("Autonomous Strands Multi-Agent Engine (Offline/Simulation Mode)")
        
    run_btn = st.sidebar.button("🚀 Run Multi-Agent Assessment", use_container_width=True, type="primary")
    
    profile = FarmProfile(
        farmer_name=farmer_name,
        location_name=location_name,
        latitude=lat,
        longitude=lon,
        crop_name=crop_name,
        growth_stage=growth_stage,
        soil_type=soil_type,
        field_size_hectares=field_size,
        irrigation_access=irrigation_access
    )
    
    return profile, run_btn

def render_vulnerability_gauge(score: float, status: str):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Composite Vulnerability Index (CVI)", 'font': {'size': 18, 'color': '#2C3E50'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#7F8C8D"},
            'bar': {'color': "#E74C3C" if score >= 70 else "#E67E22" if score >= 45 else "#F1C40F" if score >= 25 else "#27AE60"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#BDC3C7",
            'steps': [
                {'range': [0, 25], 'color': '#EAFAF1'},
                {'range': [25, 45], 'color': '#FEF9E7'},
                {'range': [45, 70], 'color': '#FBEEE6'},
                {'range': [70, 100], 'color': '#FDEDEC'}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    fig.update_layout(height=230, margin=dict(l=20, r=20, t=40, b=10))
    return fig

def render_agro_charts(diagnosis: FarmGuardDiagnosis):
    weather = diagnosis.weather_summary
    daily = weather.daily_forecasts
    if not daily:
        st.info("No daily time-series data available for chart.")
        return
        
    dates = [d.date for d in daily]
    t_max = [d.temp_max for d in daily]
    t_min = [d.temp_min for d in daily]
    rain = [d.precipitation_sum for d in daily]
    et0 = [d.et0_fao_evapotranspiration for d in daily]
    sm_surface = [d.soil_moisture_0_7cm for d in daily]
    sm_sub = [d.soil_moisture_7_28cm for d in daily]
    
    crop_info = CROP_DATABASE.get(diagnosis.farm_profile.crop_name, CROP_DATABASE["Maize (Corn)"])
    crit_t = crop_info["critical_temp_max_c"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Temperature & Thermal Heatwave Curve
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(x=dates, y=t_max, name="Max Temp (°C)", line=dict(color="#E74C3C", width=3)))
        fig_temp.add_trace(go.Scatter(x=dates, y=t_min, name="Min Temp (°C)", line=dict(color="#3498DB", width=2, dash='dot')))
        fig_temp.add_hline(y=crit_t, line_dash="dash", line_color="#C0392B", annotation_text=f"Crop Critical Limit ({crit_t}°C)")
        fig_temp.update_layout(
            title="🌡️ 7-Day Temperature Trajectory vs. Thermal Threshold",
            xaxis_title="Date",
            yaxis_title="Temperature (°C)",
            hovermode="x unified",
            height=320,
            margin=dict(l=15, r=15, t=40, b=15)
        )
        st.plotly_chart(fig_temp, use_container_width=True)
        
    with col2:
        # Water Balance: Rain vs. ET0
        fig_water = go.Figure()
        fig_water.add_trace(go.Bar(x=dates, y=rain, name="Precipitation (mm)", marker_color="#2980B9"))
        fig_water.add_trace(go.Scatter(x=dates, y=et0, name="FAO-56 ET0 Demand (mm)", line=dict(color="#E67E22", width=3)))
        fig_water.update_layout(
            title="💧 Moisture Balance: Precipitation vs. Atmospheric Demand (ET0)",
            xaxis_title="Date",
            yaxis_title="Water Depth (mm)",
            barmode='group',
            hovermode="x unified",
            height=320,
            margin=dict(l=15, r=15, t=40, b=15)
        )
        st.plotly_chart(fig_water, use_container_width=True)

def main():
    profile, run_btn = render_sidebar()
    
    # App Header
    st.markdown('<div class="main-header">🌾 FarmGuard AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Multi-Agent Climate Resilience Assistant for Smallholder Farmers | Powered by AWS Strands Agents SDK & Amazon Bedrock</div>',
        unsafe_allow_html=True
    )
    
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = FarmGuardOrchestrator()
    if "current_diagnosis" not in st.session_state or run_btn:
        with st.spinner("🤖 Autonomous Multi-Agent System analyzing agro-climatic telemetry..."):
            diagnosis = st.session_state.orchestrator.run_diagnosis(profile)
            st.session_state.current_diagnosis = diagnosis
    else:
        diagnosis = st.session_state.current_diagnosis
        
    # Top Status Bar
    status_class = f"badge-{diagnosis.overall_status.lower().replace(' ', '-')}"
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 1.2rem; gap: 1rem; flex-wrap: wrap;">
        <div><b>Target Farm:</b> {diagnosis.farm_profile.farmer_name} ({diagnosis.farm_profile.location_name})</div>
        <div><b>Crop:</b> {diagnosis.farm_profile.crop_name} ({diagnosis.farm_profile.growth_stage})</div>
        <div><b>Status:</b> <span class="status-badge {status_class}">{diagnosis.overall_status}</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Top Level Metrics and Gauge
    col_gauge, col_cards = st.columns([1, 2])
    with col_gauge:
        st.plotly_chart(render_vulnerability_gauge(diagnosis.composite_vulnerability_index, diagnosis.overall_status), use_container_width=True)
        st.caption(f"📍 GPS: {diagnosis.farm_profile.latitude:.4f}°N, {diagnosis.farm_profile.longitude:.4f}°E | Field: {diagnosis.farm_profile.field_size_hectares} ha")
        
    with col_cards:
        rc1, rc2 = st.columns(2)
        with rc1:
            # Drought Risk Card
            d = diagnosis.drought_risk
            color_d = "#C62828" if d.risk_level in ["Critical", "High"] else "#2E7D32"
            st.markdown(f"""
            <div class="risk-card">
                <div style="font-weight: 700; color: #2C3E50;">☀️ Drought & Deficit Risk</div>
                <div style="font-size: 1.6rem; font-weight: 800; color: {color_d};">{d.score_pct:.0f}% <span style="font-size: 0.9rem;">({d.risk_level})</span></div>
                <div style="font-size: 0.85rem; color: #555;">{d.primary_driver}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Soil Moisture Card
            s = diagnosis.soil_moisture_stress
            color_s = "#C62828" if s.risk_level in ["Critical", "High"] else "#2E7D32"
            st.markdown(f"""
            <div class="risk-card">
                <div style="font-weight: 700; color: #2C3E50;">🌱 Rootzone Water Stress</div>
                <div style="font-size: 1.6rem; font-weight: 800; color: {color_s};">{s.score_pct:.0f}% <span style="font-size: 0.9rem;">({s.risk_level})</span></div>
                <div style="font-size: 0.85rem; color: #555;">{s.primary_driver}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with rc2:
            # Heatwave Card
            h = diagnosis.heatwave_risk
            color_h = "#C62828" if h.risk_level in ["Critical", "High"] else "#2E7D32"
            st.markdown(f"""
            <div class="risk-card">
                <div style="font-weight: 700; color: #2C3E50;">🔥 Thermal & Heatwave Hazard</div>
                <div style="font-size: 1.6rem; font-weight: 800; color: {color_h};">{h.score_pct:.0f}% <span style="font-size: 0.9rem;">({h.risk_level})</span></div>
                <div style="font-size: 0.85rem; color: #555;">{h.primary_driver}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Heavy Rain Card
            f = diagnosis.rainfall_flood_risk
            color_f = "#C62828" if f.risk_level in ["Critical", "High"] else "#2E7D32"
            st.markdown(f"""
            <div class="risk-card">
                <div style="font-weight: 700; color: #2C3E50;">🌧️ Excess Rain & Waterlogging</div>
                <div style="font-size: 1.6rem; font-weight: 800; color: {color_f};">{f.score_pct:.0f}% <span style="font-size: 0.9rem;">({f.risk_level})</span></div>
                <div style="font-size: 0.85rem; color: #555;">{f.primary_driver}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Visual Agro-Meteorological Analytics
    st.subheader("📊 7-Day Agro-Climate Telemetry & Crop Water Dynamics")
    render_agro_charts(diagnosis)
    
    st.markdown("---")
    
    # Action Plans and Advisory
    tab_actions, tab_irrigation, tab_agents, tab_sms = st.tabs([
        "🚨 Immediate Action Plan",
        "📅 7-Day Adaptive Irrigation Schedule",
        "🤖 Multi-Agent Reasoning Trace",
        "📱 Low-Bandwidth SMS / Audio Alert"
    ])
    
    with tab_actions:
        st.markdown("### ⚡ Prioritized Immediate Tactical Interventions (Next 24-48 Hours)")
        for act in diagnosis.immediate_actions_today:
            st.markdown(f'<div class="action-step">{act}</div>', unsafe_allow_html=True)
            
        st.markdown("### 🛡️ Agronomic Resilience & Soil Conservation Best Practices")
        for tip in diagnosis.agronomic_resilience_recommendations:
            st.markdown(f"- **{tip}**")
            
    with tab_irrigation:
        st.markdown("### 💧 Adaptive Day-by-Day Irrigation & Soil Moisture Management")
        st.caption("Considers soil water depletion, forecasted rainfall, evaporative deficit, and heat anomalies.")
        
        sched_data = []
        for d in diagnosis.irrigation_schedule_7d:
            sched_data.append({
                "Date": d.date,
                "Day": d.day_name,
                "Recommendation": d.recommendation,
                "Application Volume": d.volume_liters_or_mm,
                "Agronomic Rationale": d.rationale
            })
            
        st.dataframe(pd.DataFrame(sched_data), use_container_width=True)
        
    with tab_agents:
        st.markdown("### 🧠 Autonomous Multi-Agent Collaborative Reasoning Trace")
        st.caption("Inspect the transparent chain-of-thought and delegated sub-tasks across specialized agents.")
        
        for step in diagnosis.agent_reasoning_trace:
            agent_icon = "🤖" if step["agent"] == "Orchestrator" else "🌤️" if "Climate" in step["agent"] else "🌱" if "Soil" in step["agent"] else "🛡️"
            with st.expander(f"{agent_icon} {step['agent']} ({step['role']})", expanded=True):
                st.write(step["analysis"])
                
    with tab_sms:
        st.markdown("### 📲 2G SMS & Automated Voice IVR Broadcast Card")
        st.caption("Optimized for low-bandwidth rural connectivity, localized language radios, or direct SMS gateways.")
        st.markdown(f'<div class="sms-box">{diagnosis.sms_alert_message}</div>', unsafe_allow_html=True)
        st.text_area("Copy SMS Text to Clipboard:", value=diagnosis.sms_alert_message, height=120)

if __name__ == "__main__":
    main()
