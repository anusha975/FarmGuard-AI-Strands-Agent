"""
FarmGuard AI - Multi-Agent Climate Resilience Assistant for Smallholder Farmers.
Main Streamlit Application powered by the official AWS Strands Agents SDK & Amazon Bedrock.
"""
import streamlit as st
from ui import inject_custom_styles, render_sidebar, render_diagnosis_dashboard
from agent import run_farmguard_pipeline

# Page Setup
st.set_page_config(
    page_title="FarmGuard AI - Climate Resilience Assistant",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom agricultural design CSS
inject_custom_styles()

def main():
    # 1. Render Sidebar Controls
    profile, analyze_clicked = render_sidebar()
    lang = profile.get("language", "en")
    is_te = (lang == "te")

    # 2. Main Header
    title_text = "🌾 ఫామ్‌గార్డ్ ఏఐ (FarmGuard AI)" if is_te else "🌾 FarmGuard AI"
    sub_text = (
        "చిన్నకారు రైతుల కోసం బహుళ-ఏజెంట్ వాతావరణ కరువు సంరక్షణ సహాయకుడు | AWS స్ట్రాండ్స్ ఏజెంట్స్ SDK & అమెజాన్ బెడ్‌రాక్"
        if is_te else
        "Multi-Agent Climate Resilience Assistant for Smallholder Farmers | Powered by AWS Strands Agents SDK & Amazon Bedrock"
    )
    st.markdown(f'<div class="main-header">{title_text}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">{sub_text}</div>', unsafe_allow_html=True)

    # 3. Execution State Handling
    if "latest_diagnosis" not in st.session_state or analyze_clicked:
        spinner_msg = (
            "🤖 స్ట్రాండ్స్ ఏజెంట్ వాతావరణ టెలిమెట్రీ మరియు నేల తేమను విశ్లేషిస్తోంది..."
            if is_te else
            "🤖 Strands Orchestrator Agent is analyzing agro-meteorological telemetry and soil physics..."
        )
        with st.spinner(spinner_msg):
            try:
                res = run_farmguard_pipeline(profile)
                if res.get("status") == "error":
                    err_msg = res.get("message", "Unknown error")
                    st.error(f"⚠️ Assessment Alert: {err_msg}")
                    st.info("💡 Tip: If your internet connection is limited, check 'Demonstration Mode' in the sidebar to run offline simulation.")
                    return
                st.session_state.latest_diagnosis = res
            except Exception as exc:
                st.error(f"⚠️ Unexpected System Error: {str(exc)}")
                return
    else:
        res = st.session_state.latest_diagnosis
        # If user toggled language in sidebar, ensure diagnosis reflects target language
        if res.get("farm_profile", {}).get("language") != lang:
            profile["demo_mode"] = res.get("is_simulated", False)
            res = run_farmguard_pipeline(profile)
            st.session_state.latest_diagnosis = res

    # 4. Render Main Dashboard Panels
    render_diagnosis_dashboard(res, language=lang)

if __name__ == "__main__":
    main()
