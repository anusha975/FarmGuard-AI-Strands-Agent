# 🎬 FarmGuard AI - Demo Video Script (Under 3 Minutes)

**Target Duration**: 2 minutes 45 seconds (165 seconds)  
**Speaking Rate**: ~130–140 words/minute (Total word count: ~380 words)  
**Resolution**: 1080p Full HD (Screen Recording with Voiceover)  
**App URL**: `http://localhost:8501`

---

## ⏱️ Video Timeline & Shot-by-Shot Blueprint

---

### [0:00 – 0:25] Scene 1: The Climate Problem for Smallholder Farmers
* **Visual**:
  - Show a high-contrast slide or the FarmGuard AI banner showing vulnerable rainfed smallholder farming fields.
  - Or display the top of the Streamlit dashboard highlighting the drought and heatwave hazard cards.
* **Voiceover**:
  > *"Over 500 million smallholder farmers produce one-third of the world's food supply, yet they operate on the frontlines of the climate crisis without access to real-time agronomists or expensive IoT soil sensors. A sudden five-day heatwave or dry spell during crop flowering can decimate an entire season's harvest within 48 hours."*

---

### [0:25 – 0:45] Scene 2: Introducing FarmGuard AI & Architecture
* **Visual**:
  - Show the Streamlit application title: **FarmGuard AI - Climate Resilience Assistant**.
  - Highlight the badge: `🟢 LIVE DATA (Open-Meteo Agro-Weather API)`.
  - Briefly flash the architecture diagram from the README showing the Strands Orchestrator and Amazon Bedrock.
* **Voiceover**:
  > *"Meet FarmGuard AI: an autonomous climate resilience assistant built using the official AWS Strands Agents SDK and Amazon Bedrock. FarmGuard AI fuses real-time satellite telemetry with verified FAO-56 crop water balance physics to give smallholders timely, low-cost adaptation strategies with zero hardware costs."*

---

### [0:45 – 1:10] Scene 3: Farmer Profile Input & Real Telemetry
* **Visual**:
  - Go to the sidebar.
  - Select Regional Benchmark: **"Anantapur, Andhra Pradesh (Arid Rayalaseema - Groundnut)"**.
  - Show latitude `14.68`, longitude `77.60`, crop **Groundnut (Peanut)**, stage **Flowering/Anthesis**, and soil **Sandy Loam**.
  - Show water source set to **"Rainfed Only"**.
* **Voiceover**:
  > *"A farmer or cooperative extension worker simply inputs their village coordinates, crop, phenological stage, and soil texture. Let's select Anantapur in the arid Rayalaseema region of India during the critical groundnut flowering stage."*

---

### [1:10 – 1:35] Scene 4: Strands Agent Execution & Custom Tool Calls
* **Visual**:
  - Click the primary button: **"🚀 Analyze Climate Risk"**.
  - Show the execution spinner (`Strands AI Orchestrator running diagnosis...`).
  - Once loaded, click on the **"🧠 Strands Agent Tool Execution Trace"** tab.
  - Expand `get_weather_forecast`, `analyze_soil_moisture`, and `calculate_drought_risk`.
* **Voiceover**:
  > *"When we click 'Analyze Climate Risk', the central Strands Agent takes control. It doesn't guess or hallucinate—it queries four specialized custom tools: fetching authentic 7-day weather from Open-Meteo, calculating FAO-56 rootzone water depletion, assessing thermal heatwave anomalies, and synthesizing prioritized directives."*

---

### [1:35 – 2:00] Scene 5: Scientific Risk Analysis & FAO-56 Hydrology
* **Visual**:
  - Scroll up to the main dashboard.
  - Show the 4 Hazard Metric Cards: Drought (High), Heatwave (High), Soil Moisture (Moderate), and Flood (Low).
  - Point to the Plotly **Composite Vulnerability Index (CVI)** gauge.
  - Switch to the **"🔬 FAO-56 Soil Moisture Physics"** tab showing Field Capacity (FC), Wilting Point (PWP), TAW, and RAW.
* **Voiceover**:
  > *"The dashboard presents an immediate visual diagnosis: a Composite Vulnerability Index gauge and four distinct hazard cards. In the soil physics tab, we see scientific metrics: Total Available Water, Readily Available Water, and the Crop Water Stress Index, identifying exactly when the rootzone safety buffer is breached."*

---

### [2:00 – 2:25] Scene 6: Practical Recommendations & Telugu Demonstration
* **Visual**:
  - Switch to the **"🚨 Immediate Action Plan"** tab showing tactical steps (mulching, evening cooling).
  - Go back to the sidebar and toggle Language to **"తెలుగు (Telugu)"**.
  - Show the entire UI update instantaneously into Telugu.
  - Open the **"📱 రైతు మొబైల్ SMS అలర్ట్"** tab showing the localized 2G SMS text card.
* **Voiceover**:
  > *"Instead of generic advice, FarmGuard AI delivers prioritized 24-to-48 hour interventions—like applying crop residue mulch and shifting to evening deficit irrigation. Even better, FarmGuard AI provides complete localization in Telugu, generating concise 2G SMS alerts optimized for basic cellular dispatch and voice IVR broadcasts to reach farmers without smartphones."*

---

### [2:25 – 2:45] Scene 7: Social Impact & Closing Call to Action
* **Visual**:
  - Show the Responsible AI & Safety Disclaimer card.
  - Switch briefly to terminal or VS Code showing the **62 passing automated tests** (`Ran 62 tests in 30.109s - OK`).
  - End on the GitHub repository page (`https://github.com/anusha975/FarmGuard-AI-Strands-Agent`).
* **Voiceover**:
  > *"FarmGuard AI removes the economic barrier to climate intelligence for smallholders. Every calculation is grounded in agricultural science and backed by 62 passing automated tests. Built with the AWS Strands Agents SDK and Amazon Bedrock, FarmGuard AI protects livelihoods and strengthens food resilience where it matters most. Thank you!"*

---

## 💡 Pro-Tips for Recording:
1. **Screen Resolution**: Set display scaling to 100% or 125% so text and gauge numbers are crisp and readable.
2. **Audio**: Use a headset or external microphone in a quiet room to eliminate background noise.
3. **Cursor**: Move the mouse smoothly to direct the viewer's eye to each metric card and tab.
4. **Duration Check**: Rehearse once with a stopwatch to ensure you finish between 2:30 and 2:50.

