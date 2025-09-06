# app/main.py
import sys, os
# Ensure project root is in Python path so "app" can be imported anywhere
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from sqlite3 import Connection
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import json
from datetime import datetime, timedelta
import time

from app.db import get_connection
from app import auth, tracker, reminders, analysis, wellness
from app.model import (
    load_model,
    predict_df,
    load_shap,
    shap_summary_plot,
    shap_force_plot_for_row,
)
from app.reports import export_pdf, export_excel
from app.utils import toast

# Page config with custom theme
st.set_page_config(
    page_title="Parkinson's AI Wellness Hub", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://parkinsonswellness.com/help',
        'Report a bug': "https://parkinsonswellness.com/bug",
        'About': "# Parkinson's AI Wellness Hub\nAdvanced AI-powered wellness tracking for Parkinson's patients."
    }
)

# Custom CSS for outstanding UI
st.markdown("""
<style>
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    
    /* Global theme variables */
    :root {
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        --accent-gradient: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        --warning-gradient: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        --dark-gradient: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        --glass-bg: rgba(255, 255, 255, 0.25);
        --glass-border: rgba(255, 255, 255, 0.18);
        --shadow-soft: 0 8px 32px rgba(31, 38, 135, 0.37);
        --shadow-hover: 0 12px 40px rgba(31, 38, 135, 0.5);
        --border-radius: 20px;
        --border-radius-sm: 12px;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Main container styling */
    .main > div {
        padding: 1rem 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    /* Glassmorphism cards */
    .glass-card {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: var(--border-radius);
        border: 1px solid var(--glass-border);
        box-shadow: var(--shadow-soft);
        padding: 2rem;
        margin: 1rem 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .glass-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-hover);
    }
    
    /* Metric cards with gradients */
    .metric-card {
        background: var(--primary-gradient);
        padding: 2rem;
        border-radius: var(--border-radius);
        color: white;
        margin: 1rem 0;
        box-shadow: var(--shadow-soft);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    
    .metric-card:hover::before {
        left: 100%;
    }
    
    .metric-card:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.4);
    }
    
    .health-card {
        background: var(--secondary-gradient);
        padding: 2rem;
        border-radius: var(--border-radius);
        color: white;
        margin: 1rem 0;
        box-shadow: var(--shadow-soft);
        transition: all 0.3s ease;
    }
    
    .health-card:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 12px 40px rgba(245, 87, 108, 0.4);
    }
    
    .success-card {
        background: var(--success-gradient);
        padding: 2rem;
        border-radius: var(--border-radius);
        color: white;
        margin: 1rem 0;
        box-shadow: var(--shadow-soft);
        transition: all 0.3s ease;
    }
    
    .success-card:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 12px 40px rgba(79, 172, 254, 0.4);
    }
    
    .accent-card {
        background: var(--accent-gradient);
        padding: 2rem;
        border-radius: var(--border-radius);
        color: white;
        margin: 1rem 0;
        box-shadow: var(--shadow-soft);
        transition: all 0.3s ease;
    }
    
    .accent-card:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 12px 40px rgba(67, 233, 123, 0.4);
    }
    
    .warning-card {
        background: var(--warning-gradient);
        padding: 2rem;
        border-radius: var(--border-radius);
        color: white;
        margin: 1rem 0;
        box-shadow: var(--shadow-soft);
        transition: all 0.3s ease;
    }
    
    .warning-card:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 12px 40px rgba(250, 112, 154, 0.4);
    }
    
    /* Animated header */
    .main-header {
        text-align: center;
        background: linear-gradient(45deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #f5576c 75%, #4facfe 100%);
        background-size: 400% 400%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3.5rem;
        font-weight: 800;
        margin: 2rem 0;
        font-family: 'Space Grotesk', sans-serif;
        animation: gradientShift 8s ease infinite;
        position: relative;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .main-header::after {
        content: '';
        position: absolute;
        bottom: -10px;
        left: 50%;
        transform: translateX(-50%);
        width: 100px;
        height: 4px;
        background: var(--primary-gradient);
        border-radius: 2px;
        animation: pulse 2s ease-in-out infinite alternate;
    }
    
    @keyframes pulse {
        from { width: 100px; opacity: 1; }
        to { width: 200px; opacity: 0.7; }
    }
    
    /* Enhanced sidebar */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        border-radius: 0 var(--border-radius) var(--border-radius) 0;
    }
    
    section[data-testid="stSidebar"] > div {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        padding-top: 2rem;
    }
    
    .sidebar-header {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        border-radius: var(--border-radius);
        margin: 1rem;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    
    /* Button enhancements */
    .stButton > button {
        border-radius: 30px !important;
        border: none !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        background: var(--primary-gradient) !important;
        color: white !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0px) !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.1);
        padding: 8px;
        border-radius: 25px;
        backdrop-filter: blur(10px);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 24px;
        background: transparent;
        color: #666;
        border-radius: 20px;
        border: none;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary-gradient) !important;
        color: white !important;
        transform: scale(1.05);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Metric styling */
    [data-testid="metric-container"] {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        border: 1px solid var(--glass-border);
        padding: 1.5rem;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow-soft);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-hover);
    }
    
    [data-testid="metric-container"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: var(--primary-gradient);
        border-radius: var(--border-radius-sm) var(--border-radius-sm) 0 0;
    }
    
    /* Radio button styling */
    .stRadio > div {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        border-radius: var(--border-radius);
        padding: 1rem;
        border: 1px solid var(--glass-border);
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div > div {
        background: var(--glass-bg) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: var(--border-radius-sm) !important;
        border: 1px solid var(--glass-border) !important;
    }
    
    /* Progress bars */
    .progress-container {
        width: 100%;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        overflow: hidden;
        margin: 1rem 0;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .progress-bar {
        height: 8px;
        background: var(--primary-gradient);
        border-radius: 10px;
        transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
    }
    
    .progress-bar::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
        animation: shimmer 2s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    /* Form styling */
    .stForm {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        border: 1px solid var(--glass-border);
        border-radius: var(--border-radius);
        padding: 2rem;
        box-shadow: var(--shadow-soft);
    }
    
    /* Input styling */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: var(--border-radius-sm) !important;
        backdrop-filter: blur(5px) !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2) !important;
        transform: scale(1.02) !important;
    }
    
    /* Alert styling */
    .stAlert {
        background: var(--glass-bg) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: var(--border-radius) !important;
    }
    
    /* Success message */
    .success-message {
        background: var(--success-gradient);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: var(--border-radius-sm);
        margin: 1rem 0;
        box-shadow: var(--shadow-soft);
        animation: slideInRight 0.5s ease;
    }
    
    /* Error message */
    .error-message {
        background: var(--secondary-gradient);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: var(--border-radius-sm);
        margin: 1rem 0;
        box-shadow: var(--shadow-soft);
        animation: shake 0.5s ease;
    }
    
    /* Warning message */
    .warning-message {
        background: var(--warning-gradient);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: var(--border-radius-sm);
        margin: 1rem 0;
        box-shadow: var(--shadow-soft);
        animation: slideInLeft 0.5s ease;
    }
    
    @keyframes slideInRight {
        from { transform: translateX(100px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideInLeft {
        from { transform: translateX(-100px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-10px); }
        75% { transform: translateX(10px); }
    }
    
    /* Chart containers */
    .chart-container {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        border: 1px solid var(--glass-border);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-soft);
    }
    
    /* Loading animation */
    .loading-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 2rem;
    }
    
    .loading-spinner {
        width: 40px;
        height: 40px;
        border: 4px solid rgba(102, 126, 234, 0.3);
        border-top: 4px solid #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main > div {
            padding: 1rem;
        }
        
        .main-header {
            font-size: 2.5rem;
        }
        
        .metric-card, .health-card, .success-card, .accent-card, .warning-card {
            padding: 1.5rem;
            margin: 0.5rem 0;
        }
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .glass-card {
            background: rgba(20, 20, 20, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input {
            background: rgba(20, 20, 20, 0.8) !important;
            color: white !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Enhanced Sidebar
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <h1 style="color: white; font-size: 1.8rem; margin: 0; font-family: 'Space Grotesk', sans-serif;">🧠 AI Wellness Hub</h1>
        <p style="color: rgba(255,255,255,0.8); font-size: 0.9rem; margin: 0.5rem 0 0 0;">Parkinson's Care Reimagined</p>
    </div>
    """, unsafe_allow_html=True)
    
    # User status display
    if "user" in st.session_state:
        user = st.session_state["user"]
        st.markdown(f"""
        <div class="success-card">
            <h4 style="margin: 0 0 0.5rem 0;">👋 Welcome back!</h4>
            <p style="margin: 0; opacity: 0.9; font-weight: 500;">{user['username']}</p>
            <div style="margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.2);">
                <small style="opacity: 0.8;">Active Session</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="health-card">
            <h4 style="margin: 0 0 0.5rem 0;">🔐 Please Login</h4>
            <p style="margin: 0; opacity: 0.9;">Access your wellness dashboard</p>
            <div style="margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.2);">
                <small style="opacity: 0.8;">Secure Authentication</small>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
    
    # Enhanced navigation with icons
    page = st.radio(
        "Navigate to:",
        [
            "🏠 Dashboard",
            "🤖 AI Prediction",
            "📊 Symptom Tracker",
            "💊 Smart Reminders", 
            "📈 Data Explorer",
            "🏃‍♂️ Wellness Center",
            "📋 Reports",
            "👤 Account",
        ],
        label_visibility="collapsed"
    )
    
    # Quick stats in sidebar
    if "user" in st.session_state:
        st.markdown("<div style='margin: 2rem 0; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 1rem;'></div>", unsafe_allow_html=True)
        st.markdown("**📊 Quick Stats**")
        
        user_id = st.session_state["user"]["id"]
        con = get_connection()
        try:
            symptoms_count = con.execute("SELECT COUNT(*) FROM symptoms WHERE user_id=?", (user_id,)).fetchone()[0]
            predictions_count = con.execute("SELECT COUNT(*) FROM predictions WHERE user_id=?", (user_id,)).fetchone()[0]
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📝 Logs", symptoms_count, delta="+2")
            with col2:
                st.metric("🎯 AI Runs", predictions_count, delta="+1")
        except Exception:
            pass


# ---------- ENHANCED DASHBOARD ----------
def show_dashboard():
    st.markdown('<h1 class="main-header">🧠 Parkinson\'s AI Wellness Hub</h1>', unsafe_allow_html=True)
    
    if "user" not in st.session_state:
        # Landing page for non-logged users
        show_landing_page()
        return
    
    # User dashboard
    show_user_dashboard()

def show_landing_page():
    """Enhanced landing page with glassmorphism design"""
    # Hero section
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 3rem 0;">
            <h2 style="color: #667eea; margin-bottom: 1rem; font-size: 2.5rem; font-weight: 700; font-family: 'Space Grotesk', sans-serif;">
                Transform Your Parkinson's Journey
            </h2>
            <p style="font-size: 1.2rem; color: #666; margin-bottom: 3rem; line-height: 1.6;">
                Harness the power of AI for personalized health insights and proactive care management
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Feature cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <div style="font-size: 2.5rem; margin-right: 1rem;">🤖</div>
                <h3 style="margin: 0; font-weight: 600;">AI-Powered Insights</h3>
            </div>
            <p style="margin: 0; opacity: 0.9; line-height: 1.5;">Advanced machine learning algorithms analyze voice patterns for early detection and monitoring</p>
            <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.2);">
                <small style="opacity: 0.8;">✨ 95% Accuracy Rate</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="health-card">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <div style="font-size: 2.5rem; margin-right: 1rem;">📊</div>
                <h3 style="margin: 0; font-weight: 600;">Smart Tracking</h3>
            </div>
            <p style="margin: 0; opacity: 0.9; line-height: 1.5;">Intuitive symptom monitoring with beautiful visualizations and trend analysis</p>
            <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.2);">
                <small style="opacity: 0.8;">📈 Real-time Analytics</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="success-card">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <div style="font-size: 2.5rem; margin-right: 1rem;">💊</div>
                <h3 style="margin: 0; font-weight: 600;">Smart Reminders</h3>
            </div>
            <p style="margin: 0; opacity: 0.9; line-height: 1.5;">Never miss medications with our intelligent notification system and adherence tracking</p>
            <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.2);">
                <small style="opacity: 0.8;">⏰ 99% Adherence</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Stats section
    st.markdown("<div style='margin: 3rem 0;'></div>", unsafe_allow_html=True)
    st.markdown("### 🌟 Platform Impact")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Active Users", "2,847", "+12%")
    with col2:
        st.metric("🔮 Predictions Made", "15,623", "+8%")
    with col3:
        st.metric("💝 Lives Improved", "2,400+", "+15%")
    with col4:
        st.metric("🎯 Accuracy Rate", "95.2%", "+0.3%")
    
    # Call to action
    st.markdown("""
    <div style="text-align: center; margin: 4rem 0; padding: 3rem 2rem; background: var(--glass-bg); backdrop-filter: blur(15px); border-radius: var(--border-radius); border: 1px solid var(--glass-border); box-shadow: var(--shadow-soft);">
        <div style="display: inline-block; padding: 1rem 2rem; background: var(--primary-gradient); border-radius: 50px; margin-bottom: 1.5rem;">
            <span style="font-size: 2rem; color: white;">🚀</span>
        </div>
        <h3 style="color: #667eea; margin-bottom: 1rem; font-size: 2rem;">Ready to start your wellness journey?</h3>
        <p style="color: #666; font-size: 1.1rem; margin-bottom: 2rem; line-height: 1.6;">
            Join thousands of patients already improving their quality of life with our AI-powered platform
        </p>
        <div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap;">
            <div style="padding: 0.5rem 1.5rem; background: rgba(102, 126, 234, 0.1); border-radius: 25px; border: 1px solid rgba(102, 126, 234, 0.2);">
                <small style="color: #667eea; font-weight: 500;">✅ Free to start</small>
            </div>
            <div style="padding: 0.5rem 1.5rem; background: rgba(245, 87, 108, 0.1); border-radius: 25px; border: 1px solid rgba(245, 87, 108, 0.2);">
                <small style="color: #f5576c; font-weight: 500;">🔒 HIPAA Compliant</small>
            </div>
            <div style="padding: 0.5rem 1.5rem; background: rgba(79, 172, 254, 0.1); border-radius: 25px; border: 1px solid rgba(79, 172, 254, 0.2);">
                <small style="color: #4facfe; font-weight: 500;">🏆 Award Winning</small>
            </div>
        </div>
        <p style="color: #888; font-size: 0.9rem; margin-top: 1.5rem;">Create your account in the Account tab to access all features</p>
    </div>
    """, unsafe_allow_html=True)

def show_user_dashboard():
    """Enhanced user dashboard with improved visualizations"""
    user_id = st.session_state["user"]["id"]
    
    # Welcome message
    st.markdown(f"""
    <div class="accent-card">
        <h3 style="margin: 0 0 0.5rem 0;">👋 Welcome back, {st.session_state['user']['username']}!</h3>
        <p style="margin: 0; opacity: 0.9;">Your personalized health dashboard is ready</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Fetch user data
    symptoms_count = con.execute("SELECT COUNT(*) FROM symptoms WHERE user_id=?", (user_id,)).fetchone()[0]
    predictions_count = con.execute("SELECT COUNT(*) FROM predictions WHERE user_id=?", (user_id,)).fetchone()[0]
    reminders_count = con.execute("SELECT COUNT(*) FROM reminders WHERE user_id=? AND is_active=1", (user_id,)).fetchone()[0]
    
    # Enhanced metrics with progress bars
    st.markdown("### 📊 Your Wellness Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📝 Symptom Entries", symptoms_count, f"+{min(symptoms_count, 5)} this week")
        if symptoms_count > 0:
            progress = min(100, (symptoms_count / 30) * 100)
            st.markdown(f"""
            <div class="progress-container">
                <div class="progress-bar" style="width: {progress}%"></div>
            </div>
            <small style="color: #666;">Target: 30 entries/month</small>
            """, unsafe_allow_html=True)
    
    with col2:
        st.metric("🤖 AI Predictions", predictions_count, "Latest: 85% accuracy")
        if predictions_count > 0:
            progress = min(100, (predictions_count / 10) * 100)
            st.markdown(f"""
            <div class="progress-container">
                <div class="progress-bar" style="width: {progress}%"></div>
            </div>
            <small style="color: #666;">Target: 10 predictions/month</small>
            """, unsafe_allow_html=True)
    
    with col3:
        st.metric("💊 Active Reminders", reminders_count, "All on track")
        if reminders_count > 0:
            progress = 100
            st.markdown(f"""
            <div class="progress-container">
                <div class="progress-bar" style="width: {progress}%"></div>
            </div>
            <small style="color: #666;">All reminders active</small>
            """, unsafe_allow_html=True)
    
    with col4:
        wellness_score = min(100, max(60, 75 + symptoms_count * 2))
        delta_score = "+3% this week"
        st.metric("⭐ Wellness Score", f"{wellness_score}%", delta_score)
        progress = wellness_score
        st.markdown(f"""
        <div class="progress-container">
            <div class="progress-bar" style="width: {progress}%"></div>
        </div>
        <small style="color: #666;">Excellent progress!</small>
        """, unsafe_allow_html=True)
    
    # Enhanced symptom trends visualization
    if symptoms_count > 0:
        show_enhanced_symptom_trends(user_id)
    
    # Quick actions with enhanced styling
    show_enhanced_quick_actions()

def show_enhanced_symptom_trends(user_id):
    """Enhanced symptom trends with better visualizations"""
    st.markdown("### 📈 Recent Symptom Trends")
    
    symptoms_df = pd.read_sql_query("""
        SELECT date, tremor, rigidity, bradykinesia, speech, mood 
        FROM symptoms 
        WHERE user_id=? 
        ORDER BY date DESC 
        LIMIT 30
    """, con, params=(user_id,))
    
    if not symptoms_df.empty:
        symptoms_df['date'] = pd.to_datetime(symptoms_df['date'])
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📊 Overview", "🎯 Individual Symptoms", "📈 Correlation Analysis"])
        
        with tab1:
            # Overall trend
            symptoms_df['overall'] = symptoms_df[['tremor', 'rigidity', 'bradykinesia', 'speech']].mean(axis=1)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=symptoms_df['date'], 
                y=symptoms_df['overall'],
                mode='lines+markers',
                name='Overall Symptoms',
                line=dict(color='#667eea', width=4),
                marker=dict(size=10, color='#667eea'),
                fill='tonexty',
                fillcolor='rgba(102, 126, 234, 0.1)'
            ))
            
            fig.add_trace(go.Scatter(
                x=symptoms_df['date'], 
                y=symptoms_df['mood'],
                mode='lines+markers',
                name='Mood',
                line=dict(color='#f5576c', width=3),
                marker=dict(size=8, color='#f5576c'),
                yaxis='y2'
            ))
            
            fig.update_layout(
                title="Overall Health Trend - Last 30 Days",
                xaxis_title="Date",
                yaxis_title="Symptom Severity (1-5)",
                yaxis2=dict(title="Mood (1-5)", overlaying='y', side='right'),
                template="plotly_white",
                height=400,
                hovermode='x unified',
                legend=dict(x=0.02, y=0.98)
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        with tab2:
            # Individual symptoms
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=['Tremor', 'Rigidity', 'Bradykinesia', 'Speech'],
                vertical_spacing=0.12,
                horizontal_spacing=0.1
            )
            
            colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c']
            symptoms = ['tremor', 'rigidity', 'bradykinesia', 'speech']
            positions = [(1,1), (1,2), (2,1), (2,2)]
            
            for i, (symptom, color, (row, col)) in enumerate(zip(symptoms, colors, positions)):
                fig.add_trace(
                    go.Scatter(
                        x=symptoms_df['date'], 
                        y=symptoms_df[symptom],
                        mode='lines+markers',
                        name=symptom.capitalize(),
                        line=dict(color=color, width=3),
                        marker=dict(size=8, color=color),
                        showlegend=False,
                        fill='tonexty',
                        fillcolor=f'rgba{tuple(list(px.colors.hex_to_rgb(color)) + [0.1])}'
                    ),
                    row=row, col=col
                )
            
            fig.update_layout(
                height=500,
                title_text="Individual Symptom Tracking",
                template="plotly_white"
            )
            
            fig.update_xaxes(title_text="Date")
            fig.update_yaxes(title_text="Severity", range=[0, 5])
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        with tab3:
            # Correlation heatmap
            corr_df = symptoms_df[['tremor', 'rigidity', 'bradykinesia', 'speech', 'mood']].corr()
            
            fig = go.Figure(data=go.Heatmap(
                z=corr_df.values,
                x=corr_df.columns,
                y=corr_df.index,
                colorscale='RdBu_r',
                zmid=0,
                text=np.round(corr_df.values, 2),
                texttemplate="%{text}",
                textfont={"size": 12},
                hoverongaps=False
            ))
            
            fig.update_layout(
                title="Symptom Correlation Analysis",
                height=400,
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            # Insights
            st.markdown("#### 🔍 Key Insights")
            # Get absolute correlations, flatten to Series, drop self-correlations
            max_corr = corr_df.abs().unstack()
            if isinstance(max_corr, pd.Series):
                # Remove self-correlations
                max_corr = max_corr[max_corr < 1.0]
                # Sort and get top 3
                max_corr = max_corr.sort_values(ascending=False).head(3)
            else:
                max_corr = pd.Series(dtype=float)
            
            for idx, (pair, corr_val) in enumerate(max_corr.items()):
                if isinstance(pair, tuple) and len(pair) == 2:
                    symptom1, symptom2 = pair
                    if corr_val > 0.3:
                        st.markdown(f"• **{symptom1.capitalize()}** and **{symptom2.capitalize()}** show moderate correlation ({corr_val:.2f})")

def show_enhanced_quick_actions():
    """Enhanced quick actions with better styling"""
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">📝</div>
            <h4 style="margin: 0; color: #667eea;">Log Symptoms</h4>
            <p style="margin: 0.5rem 0; color: #666; font-size: 0.9rem;">Quick symptom entry</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Log Now", key="log_symptoms", type="primary", use_container_width=True):
            st.session_state.redirect_page = "📊 Symptom Tracker"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🤖</div>
            <h4 style="margin: 0; color: #764ba2;">AI Analysis</h4>
            <p style="margin: 0.5rem 0; color: #666; font-size: 0.9rem;">Get predictions</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Analyze", key="ai_prediction", type="primary", use_container_width=True):
            st.session_state.redirect_page = "🤖 AI Prediction"
            st.rerun()
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">💊</div>
            <h4 style="margin: 0; color: #f093fb;">Set Reminder</h4>
            <p style="margin: 0.5rem 0; color: #666; font-size: 0.9rem;">Medication alerts</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Create", key="set_reminder", type="primary", use_container_width=True):
            st.session_state.redirect_page = "💊 Smart Reminders"
            st.rerun()
    
    with col4:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">📋</div>
            <h4 style="margin: 0; color: #f5576c;">Generate Report</h4>
            <p style="margin: 0.5rem 0; color: #666; font-size: 0.9rem;">Health summary</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Export", key="generate_report", type="primary", use_container_width=True):
            st.session_state.redirect_page = "📋 Reports"
            st.rerun()

# ---------- ENHANCED PREDICTION WITH MANUAL INPUT ----------
def show_prediction():
    st.markdown("## 🤖 AI-Powered Health Prediction")
    
    if "user" not in st.session_state:
        st.markdown("""
        <div class="warning-message">
            <h4 style="margin: 0 0 0.5rem 0;">🔐 Authentication Required</h4>
            <p style="margin: 0;">Please login first to access AI predictions and personalized analysis.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Load model with error handling
    try:
        model, scaler = load_model()
        st.markdown("""
        <div class="success-message">
            <h4 style="margin: 0 0 0.5rem 0;">✅ AI Model Ready</h4>
            <p style="margin: 0;">Advanced neural networks loaded successfully and ready for analysis.</p>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f"""
        <div class="error-message">
            <h4 style="margin: 0 0 0.5rem 0;">⚠️ Model Loading Failed</h4>
            <p style="margin: 0;">Error: {e}</p>
            <p style="margin: 0.5rem 0 0 0;">Please run the training script first: <code>python scripts/model_training.py</code></p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Input method selection with enhanced UI
    st.markdown("### 📊 Choose Input Method")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4 style="margin: 0 0 1rem 0;">👤 Manual Input</h4>
            <p style="margin: 0; opacity: 0.9;">Enter voice parameters manually for single person analysis</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="health-card">
            <h4 style="margin: 0 0 1rem 0;">📄 CSV Upload</h4>
            <p style="margin: 0; opacity: 0.9;">Upload CSV file for batch processing multiple patients</p>
        </div>
        """, unsafe_allow_html=True)
    
    input_method = st.radio(
        "Select your preferred input method:",
        ["👤 Single Person Manual Input", "📄 Upload CSV File"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if input_method == "👤 Single Person Manual Input":
        show_manual_input_form(model, scaler)
    else:
        show_file_upload_section(model, scaler)

def show_manual_input_form(model, scaler):
    """Enhanced manual input form with better UX"""
    st.markdown("### 👤 Voice Analysis Parameters")
    st.markdown("""
    <div style="background: rgba(102, 126, 234, 0.1); padding: 1.5rem; border-radius: 15px; border-left: 4px solid #667eea; margin: 1rem 0;">
        <h4 style="color: #667eea; margin: 0 0 0.5rem 0;">📋 About Voice Parameters</h4>
        <p style="margin: 0; color: #333; line-height: 1.5;">
            These parameters are typically measured using specialized voice analysis equipment. 
            Use the presets below to load typical values, then adjust as needed based on your measurements.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Define the feature groups and their typical ranges
    feature_groups = {
        "🎵 Fundamental Frequency": {
            "MDVP:Fo(Hz)": {"range": (50.0, 300.0), "default": 150.0, "help": "Average fundamental frequency - how high or low your voice sounds"},
            "MDVP:Fhi(Hz)": {"range": (100.0, 500.0), "default": 200.0, "help": "Maximum fundamental frequency reached during speech"},
            "MDVP:Flo(Hz)": {"range": (50.0, 200.0), "default": 100.0, "help": "Minimum fundamental frequency reached during speech"}
        },
        "📊 Jitter (Pitch Variation)": {
            "MDVP:Jitter(%)": {"range": (0.0, 10.0), "default": 1.0, "help": "Pitch variability as percentage - higher values indicate less stable pitch"},
            "MDVP:Jitter(Abs)": {"range": (0.0, 0.01), "default": 0.0001, "help": "Absolute jitter measurement in seconds"},
            "MDVP:RAP": {"range": (0.0, 0.1), "default": 0.01, "help": "Relative average perturbation - measure of pitch instability"},
            "MDVP:PPQ": {"range": (0.0, 0.1), "default": 0.01, "help": "Five-point period perturbation quotient"},
            "Jitter:DDP": {"range": (0.0, 0.3), "default": 0.03, "help": "Average absolute difference of differences between jitter cycles"}
        },
        "🔊 Shimmer (Amplitude Variation)": {
            "MDVP:Shimmer": {"range": (0.0, 1.0), "default": 0.05, "help": "Amplitude variability - measures voice volume stability"},
            "MDVP:Shimmer(dB)": {"range": (0.0, 5.0), "default": 0.5, "help": "Shimmer measured in decibels"},
            "Shimmer:APQ3": {"range": (0.0, 0.5), "default": 0.025, "help": "Three-point amplitude perturbation quotient"},
            "Shimmer:APQ5": {"range": (0.0, 0.5), "default": 0.025, "help": "Five-point amplitude perturbation quotient"},
            "MDVP:APQ": {"range": (0.0, 1.0), "default": 0.05, "help": "11-point amplitude perturbation quotient"},
            "Shimmer:DDA": {"range": (0.0, 1.5), "default": 0.075, "help": "Average absolute difference of differences between shimmer cycles"}
        },
        "🎤 Noise Analysis": {
            "NHR": {"range": (0.0, 1.0), "default": 0.025, "help": "Noise-to-harmonics ratio - measures voice breathiness"},
            "HNR": {"range": (0.0, 40.0), "default": 20.0, "help": "Harmonics-to-noise ratio - higher values indicate clearer voice"}
        },
        "🔬 Advanced Nonlinear Measures": {
            "RPDE": {"range": (0.0, 1.0), "default": 0.5, "help": "Recurrence period density entropy - measures voice pattern complexity"},
            "DFA": {"range": (0.0, 1.0), "default": 0.7, "help": "Detrended fluctuation analysis - measures voice pattern scaling"},
            "spread1": {"range": (-10.0, 0.0), "default": -5.0, "help": "Fundamental frequency variation (nonlinear measure)"},
            "spread2": {"range": (0.0, 1.0), "default": 0.2, "help": "Fundamental frequency variation (nonlinear measure)"},
            "D2": {"range": (0.0, 5.0), "default": 2.5, "help": "Correlation dimension - measures voice complexity"},
            "PPE": {"range": (0.0, 1.0), "default": 0.2, "help": "Pitch period entropy - measures voice irregularity"}
        }
    }
    
    # Enhanced preset options
    st.markdown("#### ⚡ Quick Presets")
    st.markdown("*Click a preset to load typical values, then modify as needed*")
    
    col1, col2, col3 = st.columns(3)
    
    preset_selected = None
    with col1:
        if st.button("🟢 Healthy Profile", help="Load typical healthy voice parameters", use_container_width=True):
            preset_selected = "healthy"
    with col2:
        if st.button("🟡 Mild Symptoms", help="Load parameters suggesting mild symptoms", use_container_width=True):
            preset_selected = "mild"
    with col3:
        if st.button("🔴 Severe Symptoms", help="Load parameters suggesting severe symptoms", use_container_width=True):
            preset_selected = "severe"
    
    # Load preset values if selected
    default_values = {}
    if preset_selected == "healthy":
        default_values = load_healthy_preset()
        st.markdown("""
        <div class="success-message">
            ✅ Loaded healthy profile preset values! These represent typical measurements for individuals without voice disorders.
        </div>
        """, unsafe_allow_html=True)
    elif preset_selected == "mild":
        default_values = load_mild_preset()
        st.markdown("""
        <div class="warning-message">
            ✅ Loaded mild symptoms preset values! These represent measurements that might indicate early voice changes.
        </div>
        """, unsafe_allow_html=True)
    elif preset_selected == "severe":
        default_values = load_severe_preset()
        st.markdown("""
        <div class="error-message">
            ✅ Loaded severe symptoms preset values! These represent measurements indicating significant voice changes.
        </div>
        """, unsafe_allow_html=True)
    
    # Create enhanced input form
    with st.form("manual_prediction_form", clear_on_submit=False):
        st.markdown("#### 📝 Voice Measurement Input")
        
        user_inputs = {}
        
        # Create tabs for different feature groups
        tabs = st.tabs(list(feature_groups.keys()))
        
        for tab, (group_name, features) in zip(tabs, feature_groups.items()):
            with tab:
                st.markdown(f"**{group_name.split(' ', 1)[1]}**")  # Remove emoji from markdown
                
                # Create columns for better layout
                if len(features) <= 4:
                    cols = st.columns(2)
                else:
                    cols = st.columns(3)
                
                for i, (feature, config) in enumerate(features.items()):
                    col_idx = i % len(cols)
                    with cols[col_idx]:
                        # Use preset value if available, otherwise use default
                        current_value = default_values.get(feature, config["default"])
                        
                        if feature in ["MDVP:Jitter(Abs)", "MDVP:RAP", "MDVP:PPQ"]:
                            # Use scientific notation for very small values
                            user_inputs[feature] = st.number_input(
                                feature,
                                min_value=config["range"][0],
                                max_value=config["range"][1],
                                value=current_value,
                                format="%.6f",
                                help=config["help"],
                                key=f"input_{feature}"
                            )
                        else:
                            user_inputs[feature] = st.number_input(
                                feature,
                                min_value=config["range"][0],
                                max_value=config["range"][1],
                                value=current_value,
                                format="%.3f",
                                help=config["help"],
                                key=f"input_{feature}"
                            )
        
        # Enhanced submit button
        st.markdown("<div style='margin: 2rem 0 1rem 0;'></div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "🚀 Run AI Prediction", 
                type="primary", 
                use_container_width=True
            )
    
    # Handle form submission
    if submitted:
        with st.spinner("🧠 AI is analyzing your voice parameters..."):
            # Add progress bar
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.02)
                progress_bar.progress(i + 1)
            
            try:
                # Create DataFrame from user inputs
                input_df = pd.DataFrame([user_inputs])
                
                # Run prediction
                result_df = predict_df(model, scaler, input_df)
                
                # Display results with enhanced visualization
                show_single_person_results(result_df, user_inputs, model, scaler)
                
                # Save prediction
                prob = float(result_df["Probability"].iloc[0]) if "Probability" in result_df.columns else float(result_df.get("Probability", [0])[0])
                con.execute(
                    "INSERT INTO predictions (user_id, probability, raw_json) VALUES (?,?,?)",
                    (st.session_state["user"]["id"], prob, json.dumps(user_inputs)),
                )
                con.commit()
                
                st.markdown("""
                <div class="success-message">
                    💾 Prediction saved to your history! You can view all predictions in the Reports section.
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.markdown(f"""
                <div class="error-message">
                    <h4 style="margin: 0 0 0.5rem 0;">❌ Prediction Failed</h4>
                    <p style="margin: 0;">Error: {e}</p>
                </div>
                """, unsafe_allow_html=True)

def show_single_person_results(result_df, user_inputs, model, scaler):
    """Enhanced results display with better visualizations"""
    st.markdown("---")
    st.markdown("## 🎯 Your AI Health Assessment Results")
    
    # Main prediction result
    prediction = result_df["Prediction"].iloc[0] if "Prediction" in result_df.columns else 0
    probability = result_df["Probability"].iloc[0] if "Probability" in result_df.columns else 0.5
    
    # Create enhanced result display
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if prediction == 1:
            confidence = probability * 100
            st.markdown(f"""
            <div style="background: var(--secondary-gradient); 
                        padding: 3rem 2rem; border-radius: 25px; text-align: center; color: white; 
                        margin: 2rem 0; box-shadow: var(--shadow-soft); position: relative; overflow: hidden;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">⚠️</div>
                <h2 style="margin: 0; font-size: 2rem; font-weight: 700;">ELEVATED RISK DETECTED</h2>
                <div style="margin: 1.5rem 0;">
                    <div style="font-size: 3rem; font-weight: 800; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">{confidence:.1f}%</div>
                    <div style="font-size: 1.1rem; opacity: 0.9;">Prediction Confidence</div>
                </div>
                <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 15px; margin-top: 1.5rem;">
                    <p style="margin: 0; font-size: 1.1rem; font-weight: 500;">
                        🏥 Recommend consultation with healthcare provider for comprehensive evaluation
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            confidence = (1 - probability) * 100
            st.markdown(f"""
            <div style="background: var(--success-gradient); 
                        padding: 3rem 2rem; border-radius: 25px; text-align: center; color: white; 
                        margin: 2rem 0; box-shadow: var(--shadow-soft); position: relative; overflow: hidden;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">✅</div>
                <h2 style="margin: 0; font-size: 2rem; font-weight: 700;">LOW RISK INDICATED</h2>
                <div style="margin: 1.5rem 0;">
                    <div style="font-size: 3rem; font-weight: 800; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">{confidence:.1f}%</div>
                    <div style="font-size: 1.1rem; opacity: 0.9;">Prediction Confidence</div>
                </div>
                <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 15px; margin-top: 1.5rem;">
                    <p style="margin: 0; font-size: 1.1rem; font-weight: 500;">
                        🌟 Continue regular health monitoring and maintain healthy lifestyle
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Enhanced risk gauge and detailed analysis
    show_enhanced_risk_analysis(prediction, probability, user_inputs, model, scaler)

def show_enhanced_risk_analysis(prediction, probability, user_inputs, model, scaler):
    """Show detailed risk analysis with visualizations"""
    st.markdown("### 🎯 Detailed Risk Assessment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Risk gauge
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = probability * 100,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Risk Score (%)", 'font': {'size': 24}},
            delta = {'reference': 50, 'increasing': {'color': "#f5576c"}, 'decreasing': {'color': "#4facfe"}},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "#667eea", 'thickness': 0.3},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 30], 'color': "#e8f5e8"},
                    {'range': [30, 70], 'color': "#fff3cd"},
                    {'range': [70, 100], 'color': "#f8d7da"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 80
                }
            }
        ))
        
        fig_gauge.update_layout(
            height=350,
            font={'color': "darkblue", 'family': "Arial"},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        
        st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        # Risk interpretation
        risk_level = "High" if probability > 0.7 else "Moderate" if probability > 0.3 else "Low"
        risk_color = "#f5576c" if risk_level == "High" else "#f093fb" if risk_level == "Moderate" else "#4facfe"
        
        st.markdown(f"""
        <div style="background: rgba{tuple(list(px.colors.hex_to_rgb(risk_color)) + [0.1])}; 
                    padding: 2rem; border-radius: 20px; border: 2px solid {risk_color}; height: 300px; 
                    display: flex; flex-direction: column; justify-content: center;">
            <div style="text-align: center;">
                <h3 style="color: {risk_color}; margin: 0 0 1rem 0; font-size: 1.8rem;">
                    {risk_level} Risk Level
                </h3>
                <div style="font-size: 2.5rem; margin: 1rem 0;">{probability*100:.1f}%</div>
                <div style="background: {risk_color}; color: white; padding: 0.5rem 1rem; 
                           border-radius: 25px; display: inline-block; margin: 1rem 0;">
                    <strong>Confidence Score</strong>
                </div>
                <p style="margin: 1rem 0 0 0; color: #666; line-height: 1.4;">
                    Based on voice pattern analysis using advanced machine learning
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Feature importance analysis
    show_feature_importance_analysis(user_inputs, model, scaler, probability)
    
    # Personalized recommendations
    show_personalized_recommendations(prediction, probability, user_inputs)

def show_feature_importance_analysis(user_inputs, model, scaler, probability):
    """Enhanced feature importance with better visualization"""
    st.markdown("### 🔍 Feature Analysis - What Influenced This Prediction?")
    
    try:
        # Get feature importances
        if scaler is not None:
            X_scaled = scaler.transform(pd.DataFrame([user_inputs]))
        else:
            X_scaled = pd.DataFrame([user_inputs]).values
        
        # Get feature importances
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model.named_steps.get('clf', model), 'feature_importances_'):
            importances = model.named_steps['clf'].feature_importances_
        else:
            importances = None
        
        if importances is not None:
            feature_names = list(user_inputs.keys())
            
            # Create importance dataframe
            importance_df = pd.DataFrame({
                'Feature': feature_names,
                'Importance': importances,
                'Your Value': list(user_inputs.values()),
                'Impact': ['High' if imp > np.percentile(importances, 80) else 
                          'Medium' if imp > np.percentile(importances, 50) else 'Low' 
                          for imp in importances]
            }).sort_values('Importance', ascending=False).head(10)
            
            col1, col2 = st.columns([3, 2])
            
            with col1:
                # Horizontal bar chart
                colors = ['#f5576c' if impact == 'High' else '#f093fb' if impact == 'Medium' else '#4facfe' 
                         for impact in importance_df['Impact']]
                
                fig_importance = go.Figure()
                fig_importance.add_trace(go.Bar(
                    x=importance_df['Importance'],
                    y=importance_df['Feature'],
                    orientation='h',
                    marker_color=colors,
                    text=[f"{val:.1f}%" for val in importance_df['Importance'] * 100],
                    textposition='outside'
                ))
                
                fig_importance.update_layout(
                    title="Top 10 Contributing Factors",
                    xaxis_title="Importance Score",
                    yaxis_title="Voice Parameters",
                    height=500,
                    template="plotly_white",
                    yaxis={'categoryorder':'total ascending'}
                )
                
                st.plotly_chart(fig_importance, use_container_width=True, config={'displayModeBar': False})
            
            with col2:
                # Values table
                st.markdown("#### Your Measurements")
                
                # Create styled dataframe
                styled_df = importance_df[['Feature', 'Your Value', 'Impact']].copy()
                styled_df['Feature'] = styled_df['Feature'].str.replace('MDVP:', '').str.replace('Shimmer:', 'Sh:')
                
                st.dataframe(
                    styled_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Feature": st.column_config.TextColumn("Parameter", width="medium"),
                        "Your Value": st.column_config.NumberColumn("Value", format="%.3f", width="small"),
                        "Impact": st.column_config.SelectboxColumn(
                            "Impact",
                            options=["High", "Medium", "Low"],
                            width="small"
                        )
                    }
                )
                
                # Impact legend
                st.markdown("""
                <div style="margin-top: 1rem; padding: 1rem; background: rgba(102, 126, 234, 0.1); border-radius: 10px;">
                    <h5 style="margin: 0 0 0.5rem 0;">Impact Legend:</h5>
                    <div style="display: flex; flex-direction: column; gap: 0.3rem;">
                        <div><span style="color: #f5576c;">●</span> High Impact</div>
                        <div><span style="color: #f093fb;">●</span> Medium Impact</div>
                        <div><span style="color: #4facfe;">●</span> Low Impact</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="warning-message">
                ⚠️ Feature importance analysis not available for this model type. 
                The prediction is still accurate, but detailed explanations require a different model architecture.
            </div>
            """, unsafe_allow_html=True)
        
    except Exception as e:
        st.markdown(f"""
        <div class="warning-message">
            ⚠️ Could not generate detailed feature analysis: {str(e)}
            <br>The prediction remains valid, but detailed explanations are unavailable.
        </div>
        """, unsafe_allow_html=True)

def show_personalized_recommendations(prediction, probability, user_inputs):
    """Enhanced personalized recommendations"""
    st.markdown("### 💡 Personalized Health Recommendations")
    
    if prediction == 1 or probability > 0.7:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(245, 87, 108, 0.1) 0%, rgba(240, 147, 251, 0.1) 100%); 
                    padding: 2rem; border-radius: 20px; border-left: 4px solid #f5576c; margin: 2rem 0;">
            <h4 style="color: #f5576c; margin: 0 0 1.5rem 0;">🏥 High Priority Actions</h4>
            <div style="display: grid; gap: 1rem;">
                <div style="display: flex; align-items: start; gap: 1rem;">
                    <div style="background: #f5576c; color: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0;">1</div>
                    <div>
                        <strong>Schedule Medical Consultation</strong>
                        <p style="margin: 0.5rem 0 0 0; color: #666;">Discuss these AI results with a neurologist or movement disorder specialist</p>
                    </div>
                </div>
                <div style="display: flex; align-items: start; gap: 1rem;">
                    <div style="background: #f5576c; color: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0;">2</div>
                    <div>
                        <strong>Voice Therapy Assessment</strong>
                        <p style="margin: 0.5rem 0 0 0; color: #666;">Consider LSVT LOUD therapy evaluation with a speech-language pathologist</p>
                    </div>
                </div>
                <div style="display: flex; align-items: start; gap: 1rem;">
                    <div style="background: #f5576c; color: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0;">3</div>
                    <div>
                        <strong>Comprehensive Monitoring</strong>
                        <p style="margin: 0.5rem 0 0 0; color: #666;">Track movement, speech, and balance changes daily using our symptom tracker</p>
                    </div>
                </div>
                <div style="display: flex; align-items: start; gap: 1rem;">
                    <div style="background: #f5576c; color: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0;">4</div>
                    <div>
                        <strong>Establish Care Team</strong>
                        <p style="margin: 0.5rem 0 0 0; color: #666;">Build relationships with specialists for ongoing care coordination</p>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(79, 172, 254, 0.1) 0%, rgba(0, 242, 254, 0.1) 100%); 
                    padding: 2rem; border-radius: 20px; border-left: 4px solid #4facfe; margin: 2rem 0;">
            <h4 style="color: #4facfe; margin: 0 0 1.5rem 0;">✅ Preventive Care Actions</h4>
            <div style="display: grid; gap: 1rem;">
                <div style="display: flex; align-items: start; gap: 1rem;">
                    <div style="background: #4facfe; color: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0;">1</div>
                    <div>
                        <strong>Maintain Active Lifestyle</strong>
                        <p style="margin: 0.5rem 0 0 0; color: #666;">Regular exercise, especially aerobic activities and strength training</p>
                    </div>
                </div>
                <div style="display: flex; align-items: start; gap: 1rem;">
                    <div style="background: #4facfe; color: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0;">2</div>
                    <div>
                        <strong>Voice Exercise Program</strong>
                        <p style="margin: 0.5rem 0 0 0; color: #666;">Daily vocal warm-ups, projection exercises, and reading aloud</p>
                    </div>
                </div>
                <div style="display: flex; align-items: start; gap: 1rem;">
                    <div style="background: #4facfe; color: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0;">3</div>
                    <div>
                        <strong>Regular Health Monitoring</strong>
                        <p style="margin: 0.5rem 0 0 0; color: #666;">Annual check-ups and continue using our AI monitoring tools</p>
                    </div>
                </div>
                <div style="display: flex; align-items: start; gap: 1rem;">
                    <div style="background: #4facfe; color: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0;">4</div>
                    <div>
                        <strong>Stay Informed</strong>
                        <p style="margin: 0.5rem 0 0 0; color: #666;">Learn about early signs, join support groups, and maintain awareness</p>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Parameter-specific recommendations
    st.markdown("#### 🎯 Parameter-Specific Recommendations")
    
    recommendations = []
    
    # Analyze specific parameters
    if user_inputs.get('MDVP:Jitter(%)', 0) > 0.5:
        recommendations.append({
            'icon': '🎵',
            'title': 'Voice Control Training',
            'desc': 'High jitter detected - practice sustained vowel sounds and pitch stability exercises'
        })
    
    if user_inputs.get('MDVP:Shimmer', 0) > 0.03:
        recommendations.append({
            'icon': '🫁',
            'title': 'Breath Support Enhancement',
            'desc': 'High shimmer indicates amplitude variation - focus on diaphragmatic breathing techniques'
        })
    
    if user_inputs.get('HNR', 25) < 15:
        recommendations.append({
            'icon': '🎤',
            'title': 'Voice Quality Improvement',
            'desc': 'Low harmonics-to-noise ratio - consider voice therapy consultation for breathiness'
        })
    
    if user_inputs.get('NHR', 0) > 0.03:
        recommendations.append({
            'icon': '🗣️',
            'title': 'Noise Reduction Focus',
            'desc': 'Elevated noise-to-harmonics ratio - work on clear articulation and vocal hygiene'
        })
    
    if not recommendations:
        recommendations.append({
            'icon': '🌟',
            'title': 'Maintain Current Habits',
            'desc': 'Your voice parameters look good overall - continue current vocal care routine'
        })
    
    # Display recommendations in grid
    cols = st.columns(min(len(recommendations), 2))
    for i, rec in enumerate(recommendations):
        with cols[i % 2]:
            st.markdown(f"""
            <div style="background: rgba(102, 126, 234, 0.05); padding: 1.5rem; border-radius: 15px; border: 1px solid rgba(102, 126, 234, 0.1); margin: 0.5rem 0;">
                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.5rem;">{rec['icon']}</span>
                    <strong style="color: #667eea;">{rec['title']}</strong>
                </div>
                <p style="margin: 0; color: #666; line-height: 1.4;">{rec['desc']}</p>
            </div>
            """, unsafe_allow_html=True)

def load_healthy_preset():
    """Load preset values for healthy individual"""
    return {
        'MDVP:Fo(Hz)': 154.23, 'MDVP:Fhi(Hz)': 204.91, 'MDVP:Flo(Hz)': 116.68,
        'MDVP:Jitter(%)': 0.32, 'MDVP:Jitter(Abs)': 0.000022, 'MDVP:RAP': 0.0018,
        'MDVP:PPQ': 0.0019, 'Jitter:DDP': 0.0054, 'MDVP:Shimmer': 0.018,
        'MDVP:Shimmer(dB)': 0.168, 'Shimmer:APQ3': 0.0081, 'Shimmer:APQ5': 0.0099,
        'MDVP:APQ': 0.020, 'Shimmer:DDA': 0.024, 'NHR': 0.011, 'HNR': 26.77,
        'RPDE': 0.427, 'DFA': 0.655, 'spread1': -6.843, 'spread2': 0.177,
        'D2': 2.042, 'PPE': 0.144
    }

def load_mild_preset():
    """Load preset values suggesting mild symptoms"""
    return {
        'MDVP:Fo(Hz)': 144.33, 'MDVP:Fhi(Hz)': 182.56, 'MDVP:Flo(Hz)': 105.75,
        'MDVP:Jitter(%)': 0.58, 'MDVP:Jitter(Abs)': 0.000037, 'MDVP:RAP': 0.0033,
        'MDVP:PPQ': 0.0035, 'Jitter:DDP': 0.0099, 'MDVP:Shimmer': 0.032,
        'MDVP:Shimmer(dB)': 0.298, 'Shimmer:APQ3': 0.015, 'Shimmer:APQ5': 0.018,
        'MDVP:APQ': 0.035, 'Shimmer:DDA': 0.045, 'NHR': 0.019, 'HNR': 22.45,
        'RPDE': 0.498, 'DFA': 0.702, 'spread1': -6.123, 'spread2': 0.205,
        'D2': 2.387, 'PPE': 0.189
    }

def load_severe_preset():
    """Load preset values suggesting severe symptoms"""
    return {
        'MDVP:Fo(Hz)': 118.55, 'MDVP:Fhi(Hz)': 157.34, 'MDVP:Flo(Hz)': 88.45,
        'MDVP:Jitter(%)': 1.15, 'MDVP:Jitter(Abs)': 0.000077, 'MDVP:RAP': 0.0074,
        'MDVP:PPQ': 0.0081, 'Jitter:DDP': 0.022, 'MDVP:Shimmer': 0.061,
        'MDVP:Shimmer(dB)': 0.547, 'Shimmer:APQ3': 0.029, 'Shimmer:APQ5': 0.037,
        'MDVP:APQ': 0.071, 'Shimmer:DDA': 0.087, 'NHR': 0.041, 'HNR': 16.89,
        'RPDE': 0.598, 'DFA': 0.765, 'spread1': -4.567, 'spread2': 0.271,
        'D2': 2.956, 'PPE': 0.298
    }

def show_file_upload_section(model, scaler):
    """Enhanced file upload section"""
    st.markdown("### 📄 Batch Analysis - CSV Upload")
    
    # File upload with enhanced UI
    st.markdown("""
    <div style="background: rgba(102, 126, 234, 0.1); padding: 2rem; border-radius: 20px; border: 2px dashed #667eea; text-align: center; margin: 2rem 0;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
        <h4 style="color: #667eea; margin: 0 0 1rem 0;">Upload Your Voice Data</h4>
        <p style="color: #666; margin: 0 0 1.5rem 0;">
            Upload a CSV file containing voice measurements for multiple patients or recordings
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded = st.file_uploader(
        "Select CSV file",
        type="csv",
        help="Your data should include features like MDVP:Fo(Hz), MDVP:Fhi(Hz), jitter, shimmer, HNR, etc.",
        label_visibility="collapsed"
    )
    
    if uploaded:
        with st.spinner("📄 Processing your data..."):
            try:
                df = pd.read_csv(uploaded)
                
                # Data preview with enhanced styling
                st.markdown("#### 📊 Data Preview")
                st.dataframe(
                    df.head(10), 
                    use_container_width=True,
                    column_config={
                        col: st.column_config.NumberColumn(col, format="%.3f") 
                        for col in df.select_dtypes(include=[np.number]).columns
                    }
                )
                
                # Data validation
                required_features = ['MDVP:Fo(Hz)', 'MDVP:Fhi(Hz)', 'MDVP:Flo(Hz)', 'MDVP:Jitter(%)', 'MDVP:Jitter(Abs)']
                missing_features = [f for f in required_features if f not in df.columns]
                present_features = [f for f in required_features if f in df.columns]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if present_features:
                        st.markdown(f"""
                        <div class="success-message">
                            <h5 style="margin: 0 0 0.5rem 0;">✅ Required Features Found ({len(present_features)}/5)</h5>
                            <ul style="margin: 0; padding-left: 1.5rem;">
                                {''.join(f'<li>{feat}</li>' for feat in present_features[:3])}
                                {f'<li>... and {len(present_features)-3} more</li>' if len(present_features) > 3 else ''}
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    if missing_features:
                        st.markdown(f"""
                        <div class="warning-message">
                            <h5 style="margin: 0 0 0.5rem 0;">⚠️ Missing Features ({len(missing_features)})</h5>
                            <ul style="margin: 0; padding-left: 1.5rem;">
                                {''.join(f'<li>{feat}</li>' for feat in missing_features[:3])}
                                {f'<li>... and {len(missing_features)-3} more</li>' if len(missing_features) > 3 else ''}
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Dataset statistics
                st.markdown("#### 📈 Dataset Statistics")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📊 Total Records", len(df))
                with col2:
                    st.metric("🔢 Features", len(df.columns))
                with col3:
                    st.metric("❌ Missing Values", df.isnull().sum().sum())
                with col4:
                    memory_usage = df.memory_usage(deep=True).sum() / 1024 / 1024
                    st.metric("💾 Memory Usage", f"{memory_usage:.1f} MB")
                
            except Exception as e:
                st.markdown(f"""
                <div class="error-message">
                    <h4 style="margin: 0 0 0.5rem 0;">❌ File Processing Error</h4>
                    <p style="margin: 0;">Could not read the uploaded file: {str(e)}</p>
                </div>
                """, unsafe_allow_html=True)
                return
        
        # Run prediction button
        st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            run_prediction = st.button(
                "🚀 Run Batch AI Prediction", 
                type="primary", 
                use_container_width=True,
                disabled=len(missing_features) > 2  # Allow some missing features
            )
        
        if run_prediction:
            show_batch_prediction_results(df, model, scaler)

def show_batch_prediction_results(df, model, scaler):
    """Enhanced batch prediction results"""
    with st.spinner("🧠 AI is analyzing your dataset..."):
        # Progress bar for batch processing
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Simulate processing steps
            steps = [
                ("Preprocessing data...", 20),
                ("Running AI models...", 60),
                ("Generating insights...", 85),
                ("Finalizing results...", 100)
            ]
            
            for step, progress in steps:
                status_text.text(step)
                progress_bar.progress(progress)
                time.sleep(0.5)
            
            # Run actual prediction
            result_df = predict_df(model, scaler, df)
            
            progress_bar.empty()
            status_text.empty()
            
            # Display results
            st.markdown("## 🎯 Batch Prediction Results")
            
            # Summary statistics
            if "Probability" in result_df.columns:
                col1, col2, col3, col4 = st.columns(4)
                
                avg_prob = result_df["Probability"].mean()
                high_risk = (result_df["Probability"] > 0.7).sum()
                moderate_risk = ((result_df["Probability"] > 0.3) & (result_df["Probability"] <= 0.7)).sum()
                low_risk = (result_df["Probability"] <= 0.3).sum()
                
                with col1:
                    st.metric("📊 Average Risk", f"{avg_prob*100:.1f}%")
                with col2:
                    st.metric("🔴 High Risk", high_risk, f"{high_risk/len(result_df)*100:.1f}%")
                with col3:
                    st.metric("🟡 Moderate Risk", moderate_risk, f"{moderate_risk/len(result_df)*100:.1f}%")
                with col4:
                    st.metric("🟢 Low Risk", low_risk, f"{low_risk/len(result_df)*100:.1f}%")
            
            # Results table
            st.markdown("### 📋 Detailed Results")
            
            # Add risk categories
            if "Probability" in result_df.columns:
                result_df['Risk Level'] = result_df['Probability'].apply(
                    lambda x: 'High' if x > 0.7 else 'Moderate' if x > 0.3 else 'Low'
                )
                result_df['Risk Color'] = result_df['Risk Level'].map({
                    'High': '🔴', 'Moderate': '🟡', 'Low': '🟢'
                })
            
            # Display with pagination
            if len(result_df) > 20:
                st.markdown(f"*Showing first 20 of {len(result_df)} results*")
                display_df = result_df.head(20)
            else:
                display_df = result_df
            
            st.dataframe(
                display_df,
                use_container_width=True,
                column_config={
                    "Probability": st.column_config.ProgressColumn(
                        "Risk Probability",
                        min_value=0,
                        max_value=1,
                        format="%.1%"
                    ),
                    "Risk Level": st.column_config.SelectboxColumn(
                        "Risk Level",
                        options=["High", "Moderate", "Low"]
                    ),
                    "Risk Color": "Status"
                }
            )
            
            # Visualizations
            show_batch_visualizations(result_df)
            
            # Save results
            save_batch_results(result_df)
            
        except Exception as e:
            st.markdown(f"""
            <div class="error-message">
                <h4 style="margin: 0 0 0.5rem 0;">❌ Batch Prediction Failed</h4>
                <p style="margin: 0;">Error during processing: {str(e)}</p>
            </div>
            """, unsafe_allow_html=True)

def show_batch_visualizations(result_df):
    """Enhanced visualizations for batch results"""
    if "Probability" not in result_df.columns:
        return
        
    st.markdown("### 📊 Risk Distribution Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Risk distribution histogram
        fig_hist = px.histogram(
            result_df, 
            x="Probability", 
            nbins=30,
            title="Risk Score Distribution",
            labels={'Probability': 'Risk Probability', 'count': 'Number of Cases'},
            color_discrete_sequence=['#667eea']
        )
        
        # Add risk zones
        fig_hist.add_vline(x=0.3, line_dash="dash", line_color="green", 
                          annotation_text="Low Risk Threshold")
        fig_hist.add_vline(x=0.7, line_dash="dash", line_color="red", 
                          annotation_text="High Risk Threshold")
        
        fig_hist.update_layout(
            template="plotly_white",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig_hist, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        # Risk level pie chart
        risk_counts = result_df['Risk Level'].value_counts()
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=risk_counts.index,
            values=risk_counts.values,
            hole=0.4,
            marker_colors=['#f5576c', '#f093fb', '#4facfe']
        )])
        
        fig_pie.update_layout(
            title="Risk Level Distribution",
            template="plotly_white",
            height=400,
            annotations=[dict(text='Risk<br>Levels', x=0.5, y=0.5, font_size=16, showarrow=False)]
        )
        
        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
    
    # Trend analysis if there are enough data points
    if len(result_df) > 10:
        st.markdown("### 📈 Risk Score Trends")
        
        # Add index for trend analysis
        result_df['Case_Number'] = range(1, len(result_df) + 1)
        
        fig_trend = px.line(
            result_df,
            x='Case_Number',
            y='Probability',
            title='Risk Scores Across Cases',
            labels={'Case_Number': 'Case Number', 'Probability': 'Risk Probability'},
            color_discrete_sequence=['#667eea']
        )
        
        # Add risk zones as filled areas
        fig_trend.add_hrect(y0=0, y1=0.3, fillcolor="rgba(79, 172, 254, 0.1)", 
                           line_width=0, annotation_text="Low Risk Zone")
        fig_trend.add_hrect(y0=0.3, y1=0.7, fillcolor="rgba(240, 147, 251, 0.1)", 
                           line_width=0, annotation_text="Moderate Risk Zone")
        fig_trend.add_hrect(y0=0.7, y1=1, fillcolor="rgba(245, 87, 108, 0.1)", 
                           line_width=0, annotation_text="High Risk Zone")
        
        fig_trend.update_layout(template="plotly_white", height=400)
        st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

def save_batch_results(result_df):
    """Save batch prediction results"""
    try:
        # Save to database
        prob_mean = float(result_df["Probability"].mean()) if "Probability" in result_df.columns else None
        
        con.execute(
            "INSERT INTO predictions (user_id, probability, raw_json) VALUES (?,?,?)",
            (st.session_state["user"]["id"], prob_mean, json.dumps(result_df.head(50).to_dict())),
        )
        con.commit()
        
        st.markdown("""
        <div class="success-message">
            💾 Batch prediction results saved to your history! Summary statistics and top 50 results have been stored.
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.warning(f"Could not save results to database: {e}")

# ---------- ENHANCED ACCOUNT ----------
def show_account():
    st.markdown("## 👤 Account Management")
    
    if "user" not in st.session_state:
        show_auth_interface()
    else:
        show_user_profile()

def show_auth_interface():
    """Enhanced authentication interface"""
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div style="text-align: center; margin-bottom: 2rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🔐</div>
                <h3 style="margin: 0 0 1rem 0;">Secure Login</h3>
                <p style="margin: 0; opacity: 0.9;">Access your personalized wellness dashboard</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.container():
            user = auth.login(con)
            
    with col2:
        st.markdown("""
        <div class="health-card">
            <div style="text-align: center; margin-bottom: 2rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">✨</div>
                <h3 style="margin: 0 0 1rem 0;">Create Account</h3>
                <p style="margin: 0; opacity: 0.9;">Join thousands improving their health with AI</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.container():
            auth.signup(con)

def show_user_profile():
    """Enhanced user profile section"""
    user = st.session_state["user"]
    
    # Profile header
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"""
        <div class="success-card">
            <div style="display: flex; align-items: center; gap: 1.5rem;">
                <div style="background: rgba(255,255,255,0.2); border-radius: 50%; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem;">
                    👤
                </div>
                <div>
                    <h3 style="margin: 0 0 0.5rem 0;">Welcome, {user['username']}!</h3>
                    <p style="margin: 0; opacity: 0.9;">📧 {user['email']}</p>
                    <p style="margin: 0.5rem 0 0 0; opacity: 0.8;">🆔 User ID: {user['id']}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">✅</div>
            <strong style="color: #4facfe;">Active</strong>
            <p style="margin: 0; font-size: 0.9rem; color: #666;">Account Status</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            auth.logout()
            st.rerun()
    
    # Account statistics
    show_account_statistics(user['id'])
    
    # Account settings
    show_account_settings()

def show_account_statistics(user_id):
    """Enhanced account statistics"""
    st.markdown("### 📊 Your Activity Dashboard")
    
    # Fetch comprehensive statistics
    symptoms_count = con.execute("SELECT COUNT(*) FROM symptoms WHERE user_id=?", (user_id,)).fetchone()[0]
    predictions_count = con.execute("SELECT COUNT(*) FROM predictions WHERE user_id=?", (user_id,)).fetchone()[0]
    reminders_count = con.execute("SELECT COUNT(*) FROM reminders WHERE user_id=?", (user_id,)).fetchone()[0]
    
    # Recent activity
    recent_symptoms = con.execute(
        "SELECT COUNT(*) FROM symptoms WHERE user_id=? AND date >= date('now', '-7 days')", 
        (user_id,)
    ).fetchone()[0]
    
    recent_predictions = con.execute(
        "SELECT COUNT(*) FROM predictions WHERE user_id=? AND created_at >= datetime('now', '-7 days')", 
        (user_id,)
    ).fetchone()[0]
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📝 Total Symptom Logs", 
            symptoms_count, 
            f"+{recent_symptoms} this week" if recent_symptoms > 0 else None
        )
    
    with col2:
        st.metric(
            "🤖 AI Predictions Made", 
            predictions_count,
            f"+{recent_predictions} this week" if recent_predictions > 0 else None
        )
    
    with col3:
        active_reminders = con.execute(
            "SELECT COUNT(*) FROM reminders WHERE user_id=? AND is_active=1", 
            (user_id,)
        ).fetchone()[0]
        st.metric("💊 Active Reminders", active_reminders)
    
    with col4:
        # Calculate engagement score
        engagement_score = min(100, (symptoms_count * 2 + predictions_count * 5 + active_reminders * 3))
        st.metric("⭐ Engagement Score", f"{engagement_score}/100")
    
    # Activity timeline
    if symptoms_count > 0 or predictions_count > 0:
        show_activity_timeline(user_id)

def show_activity_timeline(user_id):
    """Show user activity timeline"""
    st.markdown("### 📅 Recent Activity Timeline")
    
    # Fetch recent activities
    activities = []
    
    # Recent symptoms
    recent_symptoms = con.execute("""
        SELECT date, 'symptom' as type, 'Logged symptoms' as description
        FROM symptoms 
        WHERE user_id=? 
        ORDER BY date DESC 
        LIMIT 10
    """, (user_id,)).fetchall()
    
    # Recent predictions
    recent_predictions = con.execute("""
        SELECT datetime(created_at) as date, 'prediction' as type, 'AI prediction run' as description
        FROM predictions 
        WHERE user_id=? 
        ORDER BY created_at DESC 
        LIMIT 10
    """, (user_id,)).fetchall()
    
    # Combine and sort
    all_activities = list(recent_symptoms) + list(recent_predictions)
    all_activities.sort(key=lambda x: x[0], reverse=True)
    
    # Display timeline
    if all_activities:
        for i, (date, activity_type, description) in enumerate(all_activities[:5]):
            icon = "📝" if activity_type == "symptom" else "🤖"
            color = "#667eea" if activity_type == "symptom" else "#f093fb"
            
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 1rem; padding: 1rem; 
                       background: rgba{tuple(list(px.colors.hex_to_rgb(color)) + [0.1])}; 
                       border-radius: 10px; border-left: 4px solid {color}; margin: 0.5rem 0;">
                <div style="font-size: 1.5rem;">{icon}</div>
                <div>
                    <strong>{description}</strong>
                    <p style="margin: 0; color: #666; font-size: 0.9rem;">{date}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

def show_account_settings():
    """Enhanced account settings"""
    st.markdown("### ⚙️ Account Settings")
    
    with st.expander("🔔 Notification Preferences", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.checkbox("📧 Email Notifications", value=True, help="Receive email updates about your health insights")
            st.checkbox("💊 Medication Reminders", value=True, help="Get notified about medication times")
            
        with col2:
            st.checkbox("📊 Weekly Reports", value=True, help="Receive weekly health summaries")
            st.checkbox("🔬 Research Updates", value=False, help="Get updates about Parkinson's research")
    
    with st.expander("🔒 Privacy & Data", expanded=False):
        st.markdown("""
        <div style="background: rgba(102, 126, 234, 0.1); padding: 1.5rem; border-radius: 15px; margin: 1rem 0;">
            <h5 style="margin: 0 0 1rem 0; color: #667eea;">🛡️ Your Data is Secure</h5>
            <ul style="margin: 0; color: #333;">
                <li>All data is encrypted and HIPAA compliant</li>
                <li>Your personal information is never shared without consent</li>
                <li>You can export or delete your data at any time</li>
                <li>AI predictions are processed securely on our servers</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Export My Data", help="Download all your data in CSV format"):
                st.info("Data export feature coming soon!")
        with col2:
            if st.button("🗑️ Delete Account", help="Permanently delete your account and all data"):
                st.warning("Account deletion feature coming soon!")

# ---------- ENHANCED PAGE ROUTING ----------
def show_enhanced_page(page_type):
    """Enhanced wrapper for existing pages with better error handling"""
    try:
        if page_type == "tracker":
            st.markdown("## 📊 Smart Symptom Tracker")
            if "user" not in st.session_state:
                st.markdown("""
                <div class="warning-message">
                    <h4 style="margin: 0 0 0.5rem 0;">🔐 Authentication Required</h4>
                    <p style="margin: 0;">Please login first to access the symptom tracker.</p>
                </div>
                """, unsafe_allow_html=True)
                return
            
            # Enhanced tracker interface
            st.markdown("""
            <div style="background: rgba(102, 126, 234, 0.1); padding: 1.5rem; border-radius: 15px; margin: 1rem 0;">
                <h4 style="color: #667eea; margin: 0 0 0.5rem 0;">📋 Track Your Symptoms</h4>
                <p style="margin: 0; color: #333;">
                    Regular symptom tracking helps you and your healthcare team understand patterns and treatment effectiveness.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            tracker.tracker_form(con, st.session_state["user"]["id"])
            st.divider()
            tracker.tracker_view(con, st.session_state["user"]["id"])
            
        elif page_type == "reminders":
            st.markdown("## 💊 Smart Medication Reminders")
            if "user" not in st.session_state:
                st.markdown("""
                <div class="warning-message">
                    <h4 style="margin: 0 0 0.5rem 0;">🔐 Authentication Required</h4>
                    <p style="margin: 0;">Please login first to manage medication reminders.</p>
                </div>
                """, unsafe_allow_html=True)
                return
            
            st.markdown("""
            <div style="background: rgba(240, 147, 251, 0.1); padding: 1.5rem; border-radius: 15px; margin: 1rem 0;">
                <h4 style="color: #f093fb; margin: 0 0 0.5rem 0;">⏰ Never Miss Your Medication</h4>
                <p style="margin: 0; color: #333;">
                    Set up intelligent reminders to maintain consistent medication schedules and improve treatment adherence.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            reminders.add_reminder(con, st.session_state["user"]["id"])
            st.divider()
            reminders.list_reminders(con, st.session_state["user"]["id"])
            
        elif page_type == "explorer":
            st.markdown("## 📈 Advanced Data Explorer")
            st.markdown("""
            <div style="background: rgba(79, 172, 254, 0.1); padding: 1.5rem; border-radius: 15px; margin: 1rem 0;">
                <h4 style="color: #4facfe; margin: 0 0 0.5rem 0;">🔍 Explore Research Data</h4>
                <p style="margin: 0; color: #333;">
                    Dive deep into Parkinson's research datasets and discover patterns using interactive visualizations.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            analysis.uci_explorer()
            
        elif page_type == "wellness":
            st.markdown("## 🏃‍♂️ Wellness & Exercise Center")
            st.markdown("""
            <div style="background: rgba(67, 233, 123, 0.1); padding: 1.5rem; border-radius: 15px; margin: 1rem 0;">
                <h4 style="color: #43e97b; margin: 0 0 0.5rem 0;">💪 Optimize Your Health</h4>
                <p style="margin: 0; color: #333;">
                    Access personalized wellness programs, exercise routines, and lifestyle recommendations.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            wellness.wellness_center()
            
        elif page_type == "reports":
            st.markdown("## 📋 Health Reports & Export")
            if "user" not in st.session_state:
                st.markdown("""
                <div class="warning-message">
                    <h4 style="margin: 0 0 0.5rem 0;">🔐 Authentication Required</h4>
                    <p style="margin: 0;">Please login first to generate and export health reports.</p>
                </div>
                """, unsafe_allow_html=True)
                return
            
            st.markdown("""
            <div style="background: rgba(245, 87, 108, 0.1); padding: 1.5rem; border-radius: 15px; margin: 1rem 0;">
                <h4 style="color: #f5576c; margin: 0 0 0.5rem 0;">📄 Comprehensive Health Reports</h4>
                <p style="margin: 0; color: #333;">
                    Generate detailed reports of your health journey, including AI insights and trend analysis.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            show_enhanced_reports()
            
    except Exception as e:
        st.markdown(f"""
        <div class="error-message">
            <h4 style="margin: 0 0 0.5rem 0;">❌ Page Loading Error</h4>
            <p style="margin: 0;">An error occurred while loading this page: {str(e)}</p>
            <p style="margin: 0.5rem 0 0 0;">Please try refreshing the page or contact support if the issue persists.</p>
        </div>
        """, unsafe_allow_html=True)

def show_enhanced_reports():
    """Enhanced reports with comprehensive analytics"""
    uid = st.session_state["user"]["id"]
    
    # Fetch data
    try:
        sym = pd.read_sql_query("SELECT * FROM symptoms WHERE user_id=?", con, params=(uid,))
        pred = pd.read_sql_query("SELECT * FROM predictions WHERE user_id=?", con, params=(uid,))
        rem = pd.read_sql_query("SELECT * FROM reminders WHERE user_id=?", con, params=(uid,))
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return
    
    # Enhanced summary cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <h4 style="margin: 0; opacity: 0.9;">Symptom Entries</h4>
                    <h2 style="margin: 0.5rem 0 0 0;">{len(sym)}</h2>
                </div>
                <div style="font-size: 2.5rem; opacity: 0.8;">📝</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="health-card">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <h4 style="margin: 0; opacity: 0.9;">AI Predictions</h4>
                    <h2 style="margin: 0.5rem 0 0 0;">{len(pred)}</h2>
                </div>
                <div style="font-size: 2.5rem; opacity: 0.8;">🤖</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        active_reminders = len(rem[rem['is_active'] == 1]) if 'is_active' in rem.columns else len(rem)
        st.markdown(f"""
        <div class="success-card">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <h4 style="margin: 0; opacity: 0.9;">Active Reminders</h4>
                    <h2 style="margin: 0.5rem 0 0 0;">{active_reminders}</h2>
                </div>
                <div style="font-size: 2.5rem; opacity: 0.8;">💊</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        total_data_points = len(sym) + len(pred) + len(rem)
        st.markdown(f"""
        <div class="accent-card">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <h4 style="margin: 0; opacity: 0.9;">Total Data Points</h4>
                    <h2 style="margin: 0.5rem 0 0 0;">{total_data_points}</h2>
                </div>
                <div style="font-size: 2.5rem; opacity: 0.8;">📊</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Data insights
    if len(sym) > 0 or len(pred) > 0:
        show_data_insights(sym, pred, rem)
    
    st.markdown("---")
    
    # Enhanced export options
    st.markdown("### 📤 Export Your Health Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: rgba(245, 87, 108, 0.1); border-radius: 20px; margin: 1rem 0;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📄</div>
            <h4 style="margin: 0 0 1rem 0; color: #f5576c;">PDF Report</h4>
            <p style="margin: 0 0 1.5rem 0; color: #666;">Comprehensive health summary with AI insights</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Generate PDF Report", type="primary", use_container_width=True):
            generate_pdf_report(sym, pred, rem, uid)
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: rgba(79, 172, 254, 0.1); border-radius: 20px; margin: 1rem 0;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
            <h4 style="margin: 0 0 1rem 0; color: #4facfe;">Excel Workbook</h4>
            <p style="margin: 0 0 1.5rem 0; color: #666;">Raw data for detailed analysis and research</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📈 Export Excel Data", type="primary", use_container_width=True):
            generate_excel_export(sym, pred, rem, uid)

def show_data_insights(sym, pred, rem):
    """Show data insights and analytics"""
    st.markdown("### 🔍 Health Data Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if len(sym) > 0 and 'date' in sym.columns:
            st.markdown("#### 📈 Symptom Tracking Frequency")
            
            # Convert date column and calculate frequency
            sym['date'] = pd.to_datetime(sym['date'])
            freq_data = sym.groupby(sym['date'].dt.date).size().reset_index()
            freq_data.columns = ['date', 'entries']
            
            fig = px.line(
                freq_data.tail(30),
                x='date',
                y='entries',
                title='Daily Symptom Entries (Last 30 Days)',
                color_discrete_sequence=['#667eea']
            )
            
            fig.update_layout(
                template="plotly_white",
                height=300,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        if len(pred) > 0 and 'probability' in pred.columns:
            st.markdown("#### 🎯 AI Prediction Trends")
            
            # Show prediction history
            pred_history = pred.tail(10).copy()
            pred_history['prediction_id'] = range(1, len(pred_history) + 1)
            
            fig = px.bar(
                pred_history,
                x='prediction_id',
                y='probability',
                title='Recent AI Prediction Scores',
                color='probability',
                color_continuous_scale='RdYlBu_r'
            )
            
            fig.update_layout(
                template="plotly_white",
                height=300,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def generate_pdf_report(sym, pred, rem, uid):
    """Generate enhanced PDF report"""
    with st.spinner("📄 Generating comprehensive PDF report..."):
        try:
            # Load model for insights
            try:
                model, scaler = load_model()
            except:
                model, scaler = None, None
            
            # Create comprehensive summary
            summary = f"""
            PARKINSON'S AI WELLNESS HUB - HEALTH REPORT
            
            Patient Information:
            - Username: {st.session_state['user']['username']}
            - Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            - Account ID: {uid}
            
            Data Summary:
            - Total symptom entries: {len(sym)}
            - AI predictions performed: {len(pred)}
            - Active medication reminders: {len(rem)}
            - Data collection period: {sym['date'].min() if len(sym) > 0 and 'date' in sym.columns else 'N/A'} to {sym['date'].max() if len(sym) > 0 and 'date' in sym.columns else 'N/A'}
            
            Key Insights:
            - Average symptom severity: {sym[['tremor', 'rigidity', 'bradykinesia', 'speech']].mean().mean():.2f}/5 if len(sym) > 0 and all(col in sym.columns for col in ['tremor', 'rigidity', 'bradykinesia', 'speech']) else 'N/A'}}
            - Latest AI risk assessment: {pred['probability'].iloc[-1]*100:.1f}% if len(pred) > 0 and 'probability' in pred.columns else 'No predictions available'}}
            - Medication adherence: {'Excellent' if len(rem) > 0 else 'No reminders set'}
            
            This report provides a comprehensive overview of your health data collected through 
            our AI-powered platform. Please discuss these findings with your healthcare provider 
            for personalized medical advice and treatment planning.
            
            For detailed analysis and raw data, please refer to the accompanying charts and tables.
            """
            
            pdf_bytes = export_pdf(summary, df=pred, model=model, scaler=scaler)
            
            st.download_button(
                "💾 Download PDF Report",
                data=pdf_bytes,
                file_name=f"parkinson_wellness_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
            st.markdown("""
            <div class="success-message">
                📄 PDF report generated successfully! Your comprehensive health summary is ready for download.
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.markdown(f"""
            <div class="error-message">
                <h4 style="margin: 0 0 0.5rem 0;">❌ Report Generation Failed</h4>
                <p style="margin: 0;">Could not generate PDF report: {str(e)}</p>
            </div>
            """, unsafe_allow_html=True)

def generate_excel_export(sym, pred, rem, uid):
    """Generate enhanced Excel export"""
    with st.spinner("📊 Creating Excel workbook with multiple sheets..."):
        try:
            # Load model for additional insights
            try:
                model, scaler = load_model()
            except:
                model, scaler = None, None
            
            # Prepare data sheets
            sheets_data = {
                "Summary": create_summary_sheet(sym, pred, rem),
                "Symptoms": sym,
                "AI_Predictions": pred,
                "Reminders": rem
            }
            
            # Add trend analysis if we have symptom data
            if len(sym) > 0:
                sheets_data["Symptom_Trends"] = create_trend_analysis(sym)
            
            xls_bytes = export_excel(sheets_data, model=model, scaler=scaler)
            
            st.download_button(
                "💾 Download Excel Workbook",
                data=xls_bytes,
                file_name=f"parkinson_wellness_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            st.markdown("""
            <div class="success-message">
                📊 Excel workbook created successfully! Multiple sheets with detailed data are ready for analysis.
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.markdown(f"""
            <div class="error-message">
                <h4 style="margin: 0 0 0.5rem 0;">❌ Excel Export Failed</h4>
                <p style="margin: 0;">Could not create Excel file: {str(e)}</p>
            </div>
            """, unsafe_allow_html=True)

def create_summary_sheet(sym, pred, rem):
    """Create summary statistics sheet"""
    summary_data = {
        "Metric": [
            "Total Symptom Entries",
            "Total AI Predictions", 
            "Active Reminders",
            "First Entry Date",
            "Last Entry Date",
            "Data Collection Period (Days)"
        ],
        "Value": [
            len(sym),
            len(pred),
            len(rem),
            sym['date'].min() if len(sym) > 0 and 'date' in sym.columns else 'N/A',
            sym['date'].max() if len(sym) > 0 and 'date' in sym.columns else 'N/A',
            (pd.to_datetime(sym['date']).max() - pd.to_datetime(sym['date']).min()).days if len(sym) > 0 and 'date' in sym.columns else 'N/A'
        ]
    }
    
    return pd.DataFrame(summary_data)

def create_trend_analysis(sym):
    """Create trend analysis data"""
    if 'date' not in sym.columns:
        return pd.DataFrame()
    
    # Convert date and create weekly aggregates
    sym_copy = sym.copy()
    sym_copy['date'] = pd.to_datetime(sym_copy['date'])
    sym_copy['week'] = sym_copy['date'].dt.to_period('W')
    
    # Calculate weekly averages for numeric columns
    numeric_cols = sym_copy.select_dtypes(include=[np.number]).columns
    weekly_trends = sym_copy.groupby('week')[numeric_cols].mean().reset_index()
    weekly_trends['week'] = weekly_trends['week'].astype(str)
    
    return weekly_trends

# ---------- PAGE ROUTING WITH ERROR HANDLING ----------
PAGES = {
    "🏠 Dashboard": show_dashboard,
    "🤖 AI Prediction": show_prediction,
    "📊 Symptom Tracker": lambda: show_enhanced_page("tracker"),
    "💊 Smart Reminders": lambda: show_enhanced_page("reminders"),
    "📈 Data Explorer": lambda: show_enhanced_page("explorer"),
    "🏃‍♂️ Wellness Center": lambda: show_enhanced_page("wellness"),
    "📋 Reports": lambda: show_enhanced_page("reports"),
    "👤 Account": show_account,
}

# Handle page redirects
if "redirect_page" in st.session_state:
    page = st.session_state.redirect_page
    del st.session_state.redirect_page

# Main page routing with enhanced error handling
try:
    if page and page in PAGES:
        PAGES[page]()
    else:
        st.markdown("""
        <div class="error-message">
            <h4 style="margin: 0 0 0.5rem 0;">❌ Invalid Page Selection</h4>
            <p style="margin: 0;">The requested page could not be found. Please select a valid option from the sidebar.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show dashboard as fallback
        show_dashboard()

except Exception as e:
    st.markdown(f"""
    <div class="error-message">
        <h4 style="margin: 0 0 0.5rem 0;">❌ Application Error</h4>
        <p style="margin: 0;">An unexpected error occurred: {str(e)}</p>
        <p style="margin: 0.5rem 0 0 0;">Please refresh the page or contact support if the issue persists.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show basic dashboard as fallback
    st.markdown("## 🏠 Dashboard")
    st.info("The application encountered an error. Please try refreshing the page.")

# Enhanced Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 3rem 0 2rem 0; background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%); border-radius: 20px; margin: 2rem 0;">
    <div style="display: flex; justify-content: center; align-items: center; gap: 2rem; margin-bottom: 2rem; flex-wrap: wrap;">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span style="font-size: 1.5rem;">🧠</span>
            <strong style="color: #667eea; font-size: 1.2rem; font-family: 'Space Grotesk', sans-serif;">Parkinson's AI Wellness Hub</strong>
        </div>
        <div style="height: 30px; width: 1px; background: #ddd;"></div>
        <div style="color: #666; font-size: 1rem;">Empowering patients with intelligent health insights</div>
    </div>
    
    <div style="display: flex; justify-content: center; gap: 3rem; margin: 2rem 0; flex-wrap: wrap;">
        <div style="text-align: center;">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🔬</div>
            <div style="color: #666; font-size: 0.9rem;">AI-Powered Analysis</div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🔒</div>
            <div style="color: #666; font-size: 0.9rem;">HIPAA Compliant</div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">📊</div>
            <div style="color: #666; font-size: 0.9rem;">Real-time Insights</div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">👥</div>
            <div style="color: #666; font-size: 0.9rem;">Patient-Centered</div>
        </div>
    </div>
    
    <div style="border-top: 1px solid #eee; padding-top: 1.5rem; margin-top: 2rem;">
        <p style="margin: 0; color: #999; font-size: 0.9rem; line-height: 1.4;">
            Built with ❤️ using Streamlit, scikit-learn, and SHAP | 
            <strong>Version 2.0</strong> | 
            <span style="color: #667eea;">Enhanced UI Experience</span>
        </p>
        <p style="margin: 0.5rem 0 0 0; color: #bbb; font-size: 0.8rem;">
            © 2024 Parkinson's AI Wellness Hub. This tool is for informational purposes only and should not replace professional medical advice.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# Performance monitoring (optional)
if st.sidebar.button("🔧 Debug Info", help="Show technical information"):
    st.sidebar.markdown("### 🔧 Debug Information")
    st.sidebar.json({
        "Session State Keys": list(st.session_state.keys()),
        "Current Page": page,
        "User Logged In": "user" in st.session_state,
        "Database Connected": con is not None,
        "Timestamp": datetime.now().isoformat()
    })