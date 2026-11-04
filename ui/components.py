"""
Visual components, Plotly risk gauges, and styling for FarmGuard AI.
"""
import streamlit as st
import plotly.graph_objects as go
from typing import Dict, Any, List

def inject_custom_styles():
    """Inject modern, clean agricultural dashboard styling."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        
        .main-header {
            font-size: 2.3rem;
            font-weight: 800;
            color: #14532D;
            letter-spacing: -0.02em;
            margin-bottom: 0.1rem;
        }
        
        .sub-header {
            font-size: 1.05rem;
            color: #4B5563;
            margin-bottom: 1.2rem;
            line-height: 1.5;
        }
        
        .live-badge {
            background-color: #ECFDF5;
            color: #065F46;
            border: 1.5px solid #10B981;
            padding: 0.3rem 0.85rem;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 0.82rem;
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
        }
        
        .demo-badge {
            background-color: #FFFBEB;
            color: #92400E;
            border: 1.5px solid #F59E0B;
            padding: 0.3rem 0.85rem;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 0.82rem;
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
        }
        
        .risk-badge-low { background-color: #DCFCE7; color: #166534; border: 1px solid #86EFAC; }
        .risk-badge-moderate { background-color: #FEF9C3; color: #854D0E; border: 1px solid #FDE047; }
        .risk-badge-high { background-color: #FFEDD5; color: #9A3412; border: 1px solid #FDBA74; }
        .risk-badge-critical { background-color: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }
        
        .risk-card {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 1.1rem;
            box-shadow: 0 1px 4px rgba(0,0,0,0.04);
            margin-bottom: 0.8rem;
            transition: transform 0.15s ease-in-out;
        }
        .risk-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        }
        
        .action-item {
            background: #F0FDF4;
            border-left: 5px solid #16A34A;
            padding: 0.85rem 1.1rem;
            border-radius: 6px;
            margin-bottom: 0.65rem;
            font-size: 0.95rem;
            color: #14532D;
            line-height: 1.5;
        }
        
        .disclaimer-card {
            background: #FFF1F2;
            border: 1.5px solid #FDA4AF;
            border-radius: 10px;
            padding: 1.1rem 1.3rem;
            color: #881337;
            font-size: 0.88rem;
            line-height: 1.6;
            margin-top: 1.5rem;
        }
        
        .sms-card {
            background: #0F172A;
            color: #E2E8F0;
            font-family: 'Courier New', Courier, monospace;
            padding: 1.1rem;
            border-radius: 8px;
            white-space: pre-wrap;
            font-size: 0.92rem;
            line-height: 1.5;
        }
    </style>
    """, unsafe_allow_html=True)

def render_vulnerability_gauge(score: float, overall_status: str, language: str = "en"):
    """Render interactive Plotly gauge for the Composite Vulnerability Index."""
    title_text = "కరువు & వాతావరణ ముప్పు సూచిక (CVI)" if language == "te" else "Composite Vulnerability Index (CVI)"
    
    # Color logic
    if score >= 70:
        bar_color = "#DC2626"
    elif score >= 45:
        bar_color = "#EA580C"
    elif score >= 25:
        bar_color = "#EAB308"
    else:
        bar_color = "#16A34A"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title_text, 'font': {'size': 16, 'color': '#1F2937'}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#9CA3AF"},
            'bar': {'color': bar_color},
            'bgcolor': "white",
            'borderwidth': 1.5,
            'bordercolor': "#D1D5DB",
            'steps': [
                {'range': [0, 25], 'color': '#DCFCE7'},
                {'range': [25, 45], 'color': '#FEF9C3'},
                {'range': [45, 70], 'color': '#FFEDD5'},
                {'range': [70, 100], 'color': '#FEE2E2'}
            ],
            'threshold': {'line': {'color': "#111827", 'width': 3.5}, 'thickness': 0.75, 'value': score}
        }
    ))
    fig.update_layout(height=230, margin=dict(l=15, r=15, t=35, b=10))
    return fig

def render_weather_charts(weather_data: Dict[str, Any], crit_temp_c: float = 35.0):
    """Render dual Plotly charts for temperature trajectory and water balance."""
    daily = weather_data.get("daily_forecasts", [])
    if not daily:
        st.info("No daily time-series telemetry available.")
        return

    dates = [d.get("date") for d in daily]
    t_max = [d.get("temp_max_c") for d in daily]
    t_min = [d.get("temp_min_c") for d in daily]
    precip = [d.get("precip_mm") for d in daily]
    et0 = [d.get("et0_mm") for d in daily]

    c1, c2 = st.columns(2)
    with c1:
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(x=dates, y=t_max, name="Max Temp (°C)", line=dict(color="#EF4444", width=3)))
        fig_temp.add_trace(go.Scatter(x=dates, y=t_min, name="Min Temp (°C)", line=dict(color="#3B82F6", width=2, dash='dot')))
        fig_temp.add_hline(y=crit_temp_c, line_dash="dash", line_color="#991B1B", annotation_text=f"Thermal Limit ({crit_temp_c}°C)")
        fig_temp.update_layout(
            title="🌡️ 7-Day Temperature vs. Crop Thermal Limit",
            xaxis_title="Date",
            yaxis_title="°C",
            height=290,
            margin=dict(l=10, r=10, t=35, b=10)
        )
        st.plotly_chart(fig_temp, use_container_width=True)

    with c2:
        fig_water = go.Figure()
        fig_water.add_trace(go.Bar(x=dates, y=precip, name="Precipitation (mm)", marker_color="#0284C7"))
        fig_water.add_trace(go.Scatter(x=dates, y=et0, name="Evaporative Demand ET0 (mm)", line=dict(color="#D97706", width=3)))
        fig_water.update_layout(
            title="💧 7-Day Moisture Balance: Rain vs. ET0",
            xaxis_title="Date",
            yaxis_title="mm",
            height=290,
            margin=dict(l=10, r=10, t=35, b=10)
        )
        st.plotly_chart(fig_water, use_container_width=True)
