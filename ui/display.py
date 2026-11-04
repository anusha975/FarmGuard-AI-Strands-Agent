"""
Main display panels, risk metrics, explanations, recommendations, and tabs for FarmGuard AI.
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any
from ui.components import render_vulnerability_gauge, render_weather_charts
from farmguard.data.telugu_translations import TELUGU_HAZARDS, TELUGU_RISK_LEVELS

def render_diagnosis_dashboard(res: Dict[str, Any], language: str = "en"):
    """Render the full risk assessment, explanations, charts, and recommendations."""
    is_te = (language == "te")
    weather = res.get("weather", {})
    soil = res.get("soil", {})
    drought = res.get("drought", {})
    recom = res.get("recommendations", {})
    profile = res.get("farm_profile", {})
    is_sim = res.get("is_simulated", False)
    data_source = res.get("data_source", "Unknown")
    cvi = res.get("composite_vulnerability_index", 25.0)
    overall_status = res.get("overall_status", "NORMAL")

    # 1. Top Status & Telemetry Origin Banner
    badge_html = f'<span class="demo-badge">{data_source}</span>' if is_sim else f'<span class="live-badge">{data_source}</span>'
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; margin-bottom: 1rem; gap: 0.5rem; background: #F8FAFC; padding: 0.85rem 1.1rem; border-radius: 10px; border: 1px solid #E2E8F0;">
        <div><b>📍 {profile.get('location_name')}</b> | <b>{profile.get('crop_name')}</b> ({profile.get('growth_stage')})</div>
        <div>
            {badge_html}
            <span style="margin-left: 0.5rem; font-weight: 700; color: #1E293B;">Status: {overall_status}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Executive Gauges & 4 Core Hazards
    col_gauge, col_cards = st.columns([1, 2])
    with col_gauge:
        st.plotly_chart(render_vulnerability_gauge(cvi, overall_status, language), use_container_width=True)
        st.caption(f"Coordinates: {profile.get('latitude'):.4f}°N, {profile.get('longitude'):.4f}°E")

    with col_cards:
        c1, c2 = st.columns(2)
        
        # Drought Card
        d_lvl = drought.get("drought_risk_level", "Moderate")
        d_score = drought.get("drought_score_pct", 30.0)
        d_class = f"risk-badge-{d_lvl.lower()}"
        with c1:
            st.markdown(f"""
            <div class="risk-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 700; color: #374151;">☀️ {'కరువు ప్రమాదం' if is_te else 'Drought Deficit Risk'}</span>
                    <span class="{d_class}" style="padding: 0.2rem 0.6rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 700;">{d_lvl.upper()}</span>
                </div>
                <div style="font-size: 1.6rem; font-weight: 800; color: #DC2626; margin: 0.3rem 0;">{d_score:.0f}%</div>
                <div style="font-size: 0.82rem; color: #6B7280;">Net Deficit: {weather.get('net_water_balance_mm', -30.0):.1f} mm | Dry Streak: {weather.get('consecutive_dry_days', 0)} days</div>
            </div>
            """, unsafe_allow_html=True)

            # Soil Stress Card
            s_lvl = soil.get("soil_risk_level", "Low")
            cwsi = soil.get("crop_water_stress_index_cwsi", 0.0)
            s_class = f"risk-badge-{s_lvl.lower()}"
            st.markdown(f"""
            <div class="risk-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 700; color: #374151;">🌱 {'నేల తేమ కొరత (CWSI)' if is_te else 'Rootzone Water Stress (CWSI)'}</span>
                    <span class="{s_class}" style="padding: 0.2rem 0.6rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 700;">{s_lvl.upper()}</span>
                </div>
                <div style="font-size: 1.6rem; font-weight: 800; color: #DC2626; margin: 0.3rem 0;">{int(cwsi * 100)}%</div>
                <div style="font-size: 0.82rem; color: #6B7280;">Moisture: {soil.get('current_moisture_pct', 15.0):.1f}% (FC: {soil.get('field_capacity_pct')}%)</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            # Heatwave Card
            h_lvl = drought.get("heatwave_risk_level", "Low")
            h_score = drought.get("heatwave_score_pct", 15.0)
            h_class = f"risk-badge-{h_lvl.lower()}"
            st.markdown(f"""
            <div class="risk-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 700; color: #374151;">🔥 {'ఎండ తీవ్రత & వడగాలులు' if is_te else 'Heatwave & Thermal Stress'}</span>
                    <span class="{h_class}" style="padding: 0.2rem 0.6rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 700;">{h_lvl.upper()}</span>
                </div>
                <div style="font-size: 1.6rem; font-weight: 800; color: #DC2626; margin: 0.3rem 0;">{h_score:.0f}%</div>
                <div style="font-size: 0.82rem; color: #6B7280;">Peak Temp: {weather.get('max_forecast_temp_c', 32.0):.1f}°C ({weather.get('heatwave_days_count', 0)} heat days)</div>
            </div>
            """, unsafe_allow_html=True)

            # Flood Card
            f_lvl = drought.get("flood_risk_level", "Low")
            f_score = drought.get("flood_score_pct", 5.0)
            f_class = f"risk-badge-{f_lvl.lower()}"
            st.markdown(f"""
            <div class="risk-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 700; color: #374151;">🌧️ {'భారీ వర్షాలు / వరద' if is_te else 'Excessive Rain / Flood'}</span>
                    <span class="{f_class}" style="padding: 0.2rem 0.6rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 700;">{f_lvl.upper()}</span>
                </div>
                <div style="font-size: 1.6rem; font-weight: 800; color: #16A34A; margin: 0.3rem 0;">{f_score:.0f}%</div>
                <div style="font-size: 0.82rem; color: #6B7280;">7-Day Total Rain: {weather.get('total_precipitation_7d_mm', 0.0):.1f} mm</div>
            </div>
            """, unsafe_allow_html=True)

    # 3. Transparent Agronomic Risk Explanations
    st.markdown("---")
    st.markdown("### 📋 " + ("ముప్పు వర్గీకరణకు గల స్పష్టమైన కారణాలు" if is_te else "Transparent Causal Explanations for Risk Ratings"))
    
    with st.expander("🔍 " + ("కరువు మరియు ఉష్ణోగ్రత విశ్లేషణ కారణాలు" if is_te else "Drought & Heatwave Attribution Details"), expanded=True):
        st.write(f"**Drought Drivers:**")
        for driver in drought.get("drought_drivers", []):
            st.write(f"- {driver}")
        st.write(f"**Heatwave Drivers:**")
        for hdriver in drought.get("heatwave_drivers", []):
            st.write(f"- {hdriver}")
        st.info(f"**Soil Moisture Rationale:** {soil.get('agronomic_reason')}")

    # 4. Agro-Meteorological Telemetry Curves
    st.markdown("---")
    st.markdown("### 📊 " + ("7 రోజుల వాతావరణ టెలిమెట్రీ & నేల తేమ సమతుల్యత" if is_te else "7-Day Agro-Weather Telemetry & Crop Water Dynamics"))
    render_weather_charts(weather, crit_temp_c=35.0)

    # 5. Modular Action Tabs
    st.markdown("---")
    tab_act, tab_sched, tab_soil, tab_sms, tab_trace = st.tabs([
        "🚨 " + ("తక్షణ చర్యలు" if is_te else "Immediate Action Plan"),
        "📅 " + ("7-రోజుల నీటి యాజమాన్య ప్రణాళిక" if is_te else "7-Day Adaptive Irrigation Schedule"),
        "🔬 " + ("నేల తేమ భౌతిక విశ్లేషణ" if is_te else "FAO-56 Soil Moisture Physics"),
        "📱 " + ("రైతు మొబైల్ SMS అలర్ట్" if is_te else "2G SMS / IVR Broadcast Alert"),
        "🧠 " + ("స్ట్రాండ్స్ ఏజెంట్ టూల్స్ ట్రేస్" if is_te else "Strands Agent Tool Execution Trace")
    ])

    with tab_act:
        st.markdown("#### ⚡ " + ("రాబోయే 24-48 గంటల్లో చేపట్టవలసిన పనులు:" if is_te else "Immediate Tactical Interventions (Next 24-48 Hours):"))
        for act in recom.get("immediate_actions", []):
            st.markdown(f'<div class="action-item">{act}</div>', unsafe_allow_html=True)
            
        st.markdown("#### 🛡️ " + ("దీర్ఘకాలిక కరువు సంరక్షణ పద్ధతులు:" if is_te else "Long-Term Agronomic Resilience Practices:"))
        for tip in recom.get("resilience_recommendations", []):
            st.markdown(f"- **{tip}**")

    with tab_sched:
        st.markdown("#### 💧 " + ("7 రోజుల అనుకూల నీటి తడుల ప్రణాళిక" if is_te else "7-Day Day-by-Day Adaptive Irrigation Directives"))
        st.caption("Considers soil water depletion, forecasted rainfall, evaporative deficit, and heat anomalies.")
        
        sched_rows = []
        depletion = soil.get("rootzone_depletion_mm", 20.0)
        raw_mm = soil.get("readily_available_water_raw_mm", 40.0)
        irr_access = profile.get("irrigation_access", "Rainfed Only")
        
        for i, d in enumerate(weather.get("daily_forecasts", [])):
            d_date = d.get("date")
            d_tmax = d.get("temp_max_c", 30.0)
            d_rain = d.get("precip_mm", 0.0)
            
            if d_rain >= 10.0:
                advice = "Withhold Irrigation / తడి ఇవ్వవద్దు" if is_te else "Withhold Irrigation"
                vol = "0 mm"
                reason = f"Rainfall expected ({d_rain:.1f}mm)."
            elif d_tmax >= 37.0 and irr_access != "Rainfed Only":
                advice = "Evening Cooling / సాయంత్రం తేలికపాటి తడి" if is_te else "Evening Cooling Irrigation"
                vol = "15-20 mm"
                reason = f"Extreme daytime heat ({d_tmax:.1f}°C)."
            elif depletion > raw_mm and irr_access != "Rainfed Only":
                advice = "Refill Rootzone / వేర్లకు నీరందించండి" if is_te else "Targeted Rootzone Irrigation"
                vol = f"{round(depletion, 1)} mm"
                reason = "Soil moisture deficit breached safety buffer."
            elif irr_access == "Rainfed Only":
                advice = "Mulching / ఆచ్ఛాదన చేయండి" if is_te else "Moisture Conservation"
                vol = "N/A (Rainfed)"
                reason = "No irrigation source; apply straw/residue mulch."
            else:
                advice = "Monitor Field / పరిశీలించండి" if is_te else "Monitor Soil Buffer"
                vol = "0 mm"
                reason = "Moisture within safe parameters."
                
            sched_rows.append({
                "Date": d_date,
                "Forecast Temp": f"{d_tmax}°C",
                "Forecast Rain": f"{d_rain} mm",
                "Recommendation": advice,
                "Volume": vol,
                "Agronomic Reason": reason
            })
            
        st.dataframe(pd.DataFrame(sched_rows), use_container_width=True)

    with tab_soil:
        st.markdown("#### 🔬 " + ("ఎఫ్.ఎ.ఓ-56 శాస్త్రీయ నేల తేమ సమాచారం" if is_te else "FAO-56 Dual Crop Coefficient Water Balance"))
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        col_s1.metric("Field Capacity (FC)", f"{soil.get('field_capacity_pct')}%")
        col_s2.metric("Wilting Point (PWP)", f"{soil.get('permanent_wilting_point_pct')}%")
        col_s3.metric("Total Available Water (TAW)", f"{soil.get('total_available_water_taw_mm')} mm")
        col_s4.metric("Readily Available Buffer (RAW)", f"{soil.get('readily_available_water_raw_mm')} mm")
        
        st.metric("Rootzone Depletion (Dr)", f"{soil.get('rootzone_depletion_mm')} mm", delta=f"-{soil.get('irrigation_needed_mm')} mm deficit", delta_color="inverse")
        st.info(f"**Soil Management Directive:** {soil.get('soil_management_tip')}")

    with tab_sms:
        st.markdown("#### 📲 " + ("తక్కువ బ్యాండ్‌విడ్త్ 2G SMS / వాయిస్ సందేశం" if is_te else "Low-Bandwidth 2G SMS / Audio Broadcast Card"))
        st.caption("Optimized for rural cellular dispatch, voice IVR, or regional radio alerts.")
        sms_text = recom.get("sms_dispatch", "")
        st.markdown(f'<div class="sms-card">{sms_text}</div>', unsafe_allow_html=True)
        st.text_area("Copy SMS Text to Clipboard:", value=sms_text, height=120)

    with tab_trace:
        st.markdown("#### 🧠 " + ("అధికారిక AWS స్ట్రాండ్స్ ఏజెంట్ టూల్స్ అమలు వివరాలు" if is_te else "Official AWS Strands Agent Tool Execution Trace"))
        st.caption("Inspect the actual tools invoked by the Strands Agent loop on Amazon Bedrock.")
        for trace in res.get("tool_traces", []):
            with st.expander(f"🔧 Tool: `{trace.get('tool')}` | Status: {trace.get('status')}", expanded=True):
                st.json(trace)

    # 6. Responsible AI & Agricultural Safety Disclaimer
    disclaimer_text = recom.get("safety_disclaimer", "")
    st.markdown(f'<div class="disclaimer-card">{disclaimer_text}</div>', unsafe_allow_html=True)
