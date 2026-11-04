# 🚀 FarmGuard AI - Cloud Deployment Guide

This guide explains how to deploy your FarmGuard AI application online so anyone can access it from a public URL.

---

## 🌟 Method 1: Deploy on Render (render.com)

Render allows you to host Python web services for free with automatic deployments on git push.

### Step-by-Step Instructions:
1. **Sign Up / Log In**:
   - Go to [https://render.com](https://render.com).
   - Sign in using your **GitHub account** (`anusha975`).

2. **Create New Web Service**:
   - Click the **"New +"** button in the dashboard and select **"Web Service"**.

3. **Connect Your GitHub Repository**:
   - In the repository list, find and select **`FarmGuard-AI-Strands-Agent`** (or paste your repo URL: `https://github.com/anusha975/FarmGuard-AI-Strands-Agent`).
   - Click **Connect**.

4. **Configure Service Settings**:
   - **Name**: `farmguard-ai` (or your choice)
   - **Region**: `Oregon (US West)` or closest to your target audience
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
     ```
   - **Instance Type**: Select **Free** ($0/month).

5. **Environment Variables (Optional)**:
   - Click **Advanced** -> **Add Environment Variable**:
     - `PYTHON_VERSION`: `3.11.9`
     - `FARMGARD_MODE`: `live`
     - *(Optional if using Amazon Bedrock online)*:
       - `AWS_REGION`: `us-east-1`
       - `AWS_ACCESS_KEY_ID`: `your_access_key`
       - `AWS_SECRET_ACCESS_KEY`: `your_secret_key`

6. **Deploy**:
   - Click **"Create Web Service"**.
   - Render will build dependencies and start Streamlit. In ~2–3 minutes, your live URL will be active (e.g., `https://farmguard-ai.onrender.com`).

---

## ⚡ Method 2: Deploy on Streamlit Community Cloud (Fastest - 60 Seconds)

Streamlit Community Cloud is **100% free**, built specifically for Streamlit, does not sleep, and requires zero configuration.

### Step-by-Step Instructions:
1. Go to [https://share.streamlit.io](https://share.streamlit.io).
2. Click **"Continue with GitHub"** and authorize with your account (`anusha975`).
3. Click the blue **"New app"** button.
4. Fill in the three fields:
   - **Repository**: `anusha975/FarmGuard-AI-Strands-Agent`
   - **Branch**: `main`
   - **Main file path**: `app.py`
5. *(Optional)* Click **Advanced settings** if you want to paste your AWS credentials into Secrets.
6. Click **Deploy!**
7. Your app will be live within 90 seconds at:
   `https://farmguard-ai.streamlit.app` (or similar custom sub-domain).

---

## 🔄 Automatic Continuous Deployment (CI/CD)

Whenever you push new code to the `main` branch:
```powershell
git add .
git commit -m "update feature"
git push origin main
```
Both Render and Streamlit Cloud will **automatically rebuild and redeploy** your updated code with zero downtime!

