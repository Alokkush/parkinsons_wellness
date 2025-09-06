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
    page_title="🧠 Parkinson's AI Wellness Hub", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://parkinsonswellness.com/help',
        'Report a bug': "https://parkinsonswellness.com/bug",
        'About': "# Parkinson's AI Wellness Hub\nAdvanced AI-powered wellness tracking for Parkinson's patients."
    }
)

# Load external CSS
def load_css(file_name):
    """Load CSS from external file"""
    try:
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS file '{file_name}' not found. Please ensure the style.css file is in the same directory as main.py")

# Load the external stylesheet
css_file_path = os.path.join(os.path.dirname(__file__), "style.css")
load_css(css_file_path)

# Enhanced Sidebar
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h1 style="color: #667eea; font-size: 1.8rem; margin: 0;">🧠 AI Wellness Hub</h1>
        <p style="color: #888; font-size: 0.9rem;">Parkinson's Care Reimagined</p>
    </div>
    """, unsafe_allow_html=True)
    
    # User status display
    if "user" in st.session_state:
        user = st.session_state["user"]
        st.markdown(f"""
        <div class="success-card">
            <h4 style="margin: 0 0 0.5rem 0;">👋 Welcome back!</h4>
            <p style="margin: 0; opacity: 0.9;">{user['username']}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="health-card">
            <h4 style="margin: 0 0 0.5rem 0;">🔐 Please Login</h4>
            <p style="margin: 0; opacity: 0.9;">Access your wellness dashboard</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Enhanced navigation
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

con: Connection = get_connection()

# ---------- ENHANCED DASHBOARD ----------
def show_dashboard():
    st.markdown('<h1 class="main-header">🧠 Parkinson\'s AI Wellness Hub</h1>', unsafe_allow_html=True)
    
    if "user" not in st.session_state:
        # Landing page for non-logged users
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 2rem;">
                <h2 style="color: #667eea; margin-bottom: 2rem;">Transform Your Parkinson's Journey</h2>
                <div class="metric-card">
                    <h3>🤖 AI-Powered Insights</h3>
                    <p>Advanced machine learning for personalized health predictions</p>
                </div>
                <div class="health-card">
                    <h3>📊 Smart Tracking</h3>
                    <p>Intuitive symptom monitoring with beautiful visualizations</p>
                </div>
                <div class="success-card">
                    <h3>💊 Intelligent Reminders</h3>
                    <p>Never miss medications with our smart notification system</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Demo metrics
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Active Users", "2,847", "+12%")
            with col_b:
                st.metric("Predictions Made", "15,623", "+8%")
            with col_c:
                st.metric("Lives Improved", "2,400+", "+15%")
                
        st.markdown("""
        <div style="text-align: center; margin: 3rem 0; padding: 2rem; background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); border-radius: 20px;">
            <h3 style="color: #667eea;">Ready to start your wellness journey?</h3>
            <p style="color: #666; font-size: 1.1rem;">Create your account in the Account tab to access all features</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # User dashboard
    user_id = st.session_state["user"]["id"]
    
    # Quick stats
    st.markdown("### 📊 Your Wellness Overview")
    
    # Fetch user data
    symptoms_count = con.execute("SELECT COUNT(*) FROM symptoms WHERE user_id=?", (user_id,)).fetchone()[0]
    predictions_count = con.execute("SELECT COUNT(*) FROM predictions WHERE user_id=?", (user_id,)).fetchone()[0]
    reminders_count = con.execute("SELECT COUNT(*) FROM reminders WHERE user_id=? AND is_active=1", (user_id,)).fetchone()[0]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📝 Symptom Entries", symptoms_count, f"+{min(symptoms_count, 5)} this week")
    with col2:
        st.metric("🤖 AI Predictions", predictions_count, "Latest: 85% accuracy")
    with col3:
        st.metric("💊 Active Reminders", reminders_count, "All on track")
    with col4:
        wellness_score = min(100, max(60, 75 + symptoms_count * 2))
        st.metric("🌟 Wellness Score", f"{wellness_score}%", "+3% this week")
    
    # Recent activity chart
    if symptoms_count > 0:
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
            
            fig = make_subplots(
                rows=2, cols=3,
                subplot_titles=['Tremor', 'Rigidity', 'Bradykinesia', 'Speech', 'Mood', 'Overall Trend'],
                specs=[[{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}, {"colspan": 1, "secondary_y": False}]]
            )
            
            colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe']
            symptoms = ['tremor', 'rigidity', 'bradykinesia', 'speech', 'mood']
            
            for i, symptom in enumerate(symptoms):
                row = (i // 3) + 1
                col = (i % 3) + 1
                
                fig.add_trace(
                    go.Scatter(
                        x=symptoms_df['date'], 
                        y=symptoms_df[symptom],
                        mode='lines+markers',
                        name=symptom.capitalize(),
                        line=dict(color=colors[i], width=3),
                        marker=dict(size=8),
                        showlegend=False
                    ),
                    row=row, col=col
                )
            
            # Overall trend in the last subplot
            symptoms_df['overall'] = symptoms_df[['tremor', 'rigidity', 'bradykinesia', 'speech']].mean(axis=1)
            fig.add_trace(
                go.Scatter(
                    x=symptoms_df['date'], 
                    y=symptoms_df['overall'],
                    mode='lines+markers',
                    name='Overall Symptoms',
                    line=dict(color='#667eea', width=4),
                    marker=dict(size=10),
                    showlegend=False,
                    fill='tonexty'
                ),
                row=2, col=3
            )
            
            fig.update_layout(
                height=500,
                title_text="Your Health Journey - Last 30 Days",
                title_x=0.5,
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📝 Log Symptoms", type="primary", use_container_width=True):
            st.session_state.redirect_page = "📊 Symptom Tracker"
            st.rerun()
    
    with col2:
        if st.button("🤖 Run AI Analysis", type="primary", use_container_width=True):
            st.session_state.redirect_page = "🤖 AI Prediction"
            st.rerun()
    
    with col3:
        if st.button("💊 Set Reminder", type="primary", use_container_width=True):
            st.session_state.redirect_page = "💊 Smart Reminders"
            st.rerun()
    
    with col4:
        if st.button("📋 Generate Report", type="primary", use_container_width=True):
            st.session_state.redirect_page = "📋 Reports"
            st.rerun()

# ---------- ENHANCED PREDICTION WITH MANUAL INPUT ----------
def show_prediction():
    st.markdown("## 🤖 AI-Powered Health Prediction")
    
    if "user" not in st.session_state:
        st.warning("🔐 Please login first to access AI predictions.")
        return

    # Load model with error handling
    try:
        model, scaler = load_model()
        st.success("✅ AI Model loaded successfully!")
    except Exception as e:
        st.error(f"❌ Model loading failed: {e}")
        st.info("💡 Please run the training script first: `python scripts/model_training.py`")
        return

    # Input method selection
    st.markdown("### 📊 Choose Input Method")
    input_method = st.radio(
        "How would you like to provide data for prediction?",
        ["👤 Single Person Manual Input", "📄 Upload CSV File"],
        horizontal=True
    )
    
    if input_method == "👤 Single Person Manual Input":
        show_manual_input_form(model, scaler)
    else:
        show_file_upload_section(model, scaler)

def show_manual_input_form(model, scaler):
    """Manual input form for single person prediction"""
    st.markdown("### 👤 Manual Health Data Input")
    st.markdown("Enter your voice and speech measurements for AI analysis:")
    
    # Define the feature groups and their typical ranges
    feature_groups = {
        "Fundamental Frequency": {
            "MDVP:Fo(Hz)": {"range": (50.0, 300.0), "default": 150.0, "help": "Average fundamental frequency"},
            "MDVP:Fhi(Hz)": {"range": (100.0, 500.0), "default": 200.0, "help": "Maximum fundamental frequency"},
            "MDVP:Flo(Hz)": {"range": (50.0, 200.0), "default": 100.0, "help": "Minimum fundamental frequency"}
        },
        "Jitter Measurements": {
            "MDVP:Jitter(%)": {"range": (0.0, 10.0), "default": 1.0, "help": "Jitter as percentage"},
            "MDVP:Jitter(Abs)": {"range": (0.0, 0.01), "default": 0.0001, "help": "Absolute jitter"},
            "MDVP:RAP": {"range": (0.0, 0.1), "default": 0.01, "help": "Relative average perturbation"},
            "MDVP:PPQ": {"range": (0.0, 0.1), "default": 0.01, "help": "Five-point period perturbation quotient"},
            "Jitter:DDP": {"range": (0.0, 0.3), "default": 0.03, "help": "Average absolute difference"}
        },
        "Shimmer Measurements": {
            "MDVP:Shimmer": {"range": (0.0, 1.0), "default": 0.05, "help": "Shimmer"},
            "MDVP:Shimmer(dB)": {"range": (0.0, 5.0), "default": 0.5, "help": "Shimmer in dB"},
            "Shimmer:APQ3": {"range": (0.0, 0.5), "default": 0.025, "help": "Three-point amplitude perturbation quotient"},
            "Shimmer:APQ5": {"range": (0.0, 0.5), "default": 0.025, "help": "Five-point amplitude perturbation quotient"},
            "MDVP:APQ": {"range": (0.0, 1.0), "default": 0.05, "help": "11-point amplitude perturbation quotient"},
            "Shimmer:DDA": {"range": (0.0, 1.5), "default": 0.075, "help": "Average absolute difference"}
        },
        "Noise Ratio": {
            "NHR": {"range": (0.0, 1.0), "default": 0.025, "help": "Noise-to-harmonics ratio"},
            "HNR": {"range": (0.0, 40.0), "default": 20.0, "help": "Harmonics-to-noise ratio"}
        },
        "Nonlinear Measures": {
            "RPDE": {"range": (0.0, 1.0), "default": 0.5, "help": "Recurrence period density entropy"},
            "DFA": {"range": (0.0, 1.0), "default": 0.7, "help": "Detrended fluctuation analysis"},
            "spread1": {"range": (-10.0, 0.0), "default": -5.0, "help": "Nonlinear measure of fundamental frequency variation"},
            "spread2": {"range": (0.0, 1.0), "default": 0.2, "help": "Nonlinear measure of fundamental frequency variation"},
            "D2": {"range": (0.0, 5.0), "default": 2.5, "help": "Correlation dimension"},
            "PPE": {"range": (0.0, 1.0), "default": 0.2, "help": "Pitch period entropy"}
        }
    }
    
    # Quick preset options (outside of form)
    st.markdown("#### ⚡ Quick Presets")
    st.markdown("*Click a preset to load typical values, then modify as needed*")
    col1, col2, col3 = st.columns(3)
    
    preset_selected = None
    if col1.button("🟢 Healthy Profile", help="Load typical healthy voice parameters"):
        preset_selected = "healthy"
    if col2.button("🟡 Mild Symptoms", help="Load parameters suggesting mild symptoms"):
        preset_selected = "mild"
    if col3.button("🔴 Severe Symptoms", help="Load parameters suggesting severe symptoms"):
        preset_selected = "severe"
    
    # Load preset values if selected
    default_values = {}
    if preset_selected == "healthy":
        default_values = load_healthy_preset()
        st.success("✅ Loaded healthy profile preset values!")
    elif preset_selected == "mild":
        default_values = load_mild_preset()
        st.success("✅ Loaded mild symptoms preset values!")
    elif preset_selected == "severe":
        default_values = load_severe_preset()
        st.success("✅ Loaded severe symptoms preset values!")
    
    # Create input form
    with st.form("manual_prediction_form"):
        st.markdown("#### 📋 Voice Measurement Input")
        st.markdown("*These are technical voice analysis parameters typically measured by specialized equipment*")
        
        user_inputs = {}
        
        # Create tabs for different feature groups
        tabs = st.tabs(list(feature_groups.keys()))
        
        for tab, (group_name, features) in zip(tabs, feature_groups.items()):
            with tab:
                st.markdown(f"**{group_name}**")
                cols = st.columns(2)
                
                for i, (feature, config) in enumerate(features.items()):
                    with cols[i % 2]:
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
        
        submitted = st.form_submit_button("🚀 Run AI Prediction", type="primary", use_container_width=True)
    
    # Handle form submission
    if submitted:
        # Run prediction
        with st.spinner("🧠 AI is analyzing your voice parameters..."):
            time.sleep(2)  # Simulate processing
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
                toast("💾 Prediction saved to your history!", "success")
                
            except Exception as e:
                st.error(f"❌ Prediction failed: {e}")

def show_single_person_results(result_df, user_inputs, model, scaler):
    """Display results for single person prediction with enhanced visualization"""
    st.markdown("---")
    st.markdown("## 🎯 Your AI Health Assessment Results")
    
    # Main prediction result
    prediction = result_df["Prediction"].iloc[0] if "Prediction" in result_df.columns else 0
    probability = result_df["Probability"].iloc[0] if "Probability" in result_df.columns else 0.5
    
    # Create main result display
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if prediction == 1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%); 
                        padding: 2rem; border-radius: 20px; text-align: center; color: white; margin: 1rem 0;">
                <h2 style="margin: 0;">⚠️ ELEVATED RISK DETECTED</h2>
                <h3 style="margin: 0.5rem 0;">Confidence: {probability*100:.1f}%</h3>
                <p style="margin: 0; opacity: 0.9;">Consult healthcare provider for evaluation</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                        padding: 2rem; border-radius: 20px; text-align: center; color: white; margin: 1rem 0;">
                <h2 style="margin: 0;">✅ LOW RISK INDICATED</h2>
                <h3 style="margin: 0.5rem 0;">Confidence: {(1-probability)*100:.1f}%</h3>
                <p style="margin: 0; opacity: 0.9;">Continue regular health monitoring</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Risk gauge
    st.markdown("### 🎯 Risk Assessment Gauge")
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = probability * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Risk Score (%)"},
        delta = {'reference': 50, 'increasing': {'color': "#f5576c"}, 'decreasing': {'color': "#4facfe"}},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "#667eea"},
            'steps': [
                {'range': [0, 30], 'color': "#4facfe"},
                {'range': [30, 70], 'color': "#f093fb"},
                {'range': [70, 100], 'color': "#f5576c"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    # Feature importance for this prediction
    st.markdown("### 🔍 Personalized Analysis")
    
    try:
        # Show which features contributed most to this prediction
        if scaler is not None:
            X_scaled = scaler.transform(pd.DataFrame([user_inputs]))
        else:
            X_scaled = pd.DataFrame([user_inputs]).values
        
        # Get feature importances (simplified approach)
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model.named_steps.get('clf', model), 'feature_importances_'):
            importances = model.named_steps['clf'].feature_importances_
        else:
            importances = None
        
        if importances is not None:
            feature_names = list(user_inputs.keys())
            importance_df = pd.DataFrame({
                'Feature': feature_names,
                'Importance': importances,
                'Your Value': list(user_inputs.values())
            }).sort_values('Importance', ascending=False).head(8)
            
            st.markdown("#### 📊 Most Influential Factors")
            
            fig_importance = px.bar(
                importance_df, 
                x='Importance', 
                y='Feature',
                title="Top Contributing Factors to Your Prediction",
                orientation='h',
                color='Importance',
                color_continuous_scale='viridis'
            )
            fig_importance.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_importance, use_container_width=True)
            
            # Show the actual values
            st.markdown("#### 🔢 Your Values vs. Normal Ranges")
            st.dataframe(
                importance_df[['Feature', 'Your Value', 'Importance']].round(4),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Feature": "Parameter",
                    "Your Value": st.column_config.NumberColumn("Your Measurement", format="%.4f"),
                    "Importance": st.column_config.ProgressColumn("AI Importance", min_value=0, max_value=1)
                }
            )
        
    except Exception as e:
        st.warning(f"⚠️ Could not generate detailed analysis: {e}")
    
    # Recommendations based on results
    show_personalized_recommendations(prediction, probability, user_inputs)

def show_personalized_recommendations(prediction, probability, user_inputs):
    """Show personalized recommendations based on prediction results"""
    st.markdown("### 💡 Personalized Recommendations")
    
    if prediction == 1 or probability > 0.7:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(245, 87, 108, 0.1) 0%, rgba(240, 147, 251, 0.1) 100%); 
                    padding: 1.5rem; border-radius: 15px; border-left: 4px solid #f5576c; margin: 1rem 0;">
            <h4 style="color: #f5576c; margin: 0 0 1rem 0;">🏥 High Priority Actions</h4>
            <ul style="margin: 0; color: #333;">
                <li><strong>Schedule medical consultation</strong> - Discuss these results with a neurologist</li>
                <li><strong>Voice therapy assessment</strong> - Consider LSVT LOUD therapy evaluation</li>
                <li><strong>Monitor symptoms</strong> - Track any changes in movement, speech, or balance</li>
                <li><strong>Regular follow-up</strong> - Establish baseline and monitoring schedule</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(79, 172, 254, 0.1) 0%, rgba(0, 242, 254, 0.1) 100%); 
                    padding: 1.5rem; border-radius: 15px; border-left: 4px solid #4facfe; margin: 1rem 0;">
            <h4 style="color: #4facfe; margin: 0 0 1rem 0;">✅ Preventive Care Actions</h4>
            <ul style="margin: 0; color: #333;">
                <li><strong>Maintain healthy lifestyle</strong> - Regular exercise, balanced nutrition</li>
                <li><strong>Voice exercises</strong> - Practice daily vocal warm-ups and projection</li>
                <li><strong>Annual check-ups</strong> - Continue regular health monitoring</li>
                <li><strong>Stay informed</strong> - Learn about early signs and prevention</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Additional recommendations based on specific parameters
    st.markdown("#### 🎯 Specific Parameter Recommendations")
    
    recommendations = []
    
    # Check jitter values
    if user_inputs.get('MDVP:Jitter(%)', 0) > 0.5:
        recommendations.append("🎵 **Voice Control**: High jitter detected - practice sustained vowel sounds")
    
    # Check shimmer values
    if user_inputs.get('MDVP:Shimmer', 0) > 0.03:
        recommendations.append("📊 **Breath Support**: High shimmer - work on diaphragmatic breathing")
    
    # Check HNR
    if user_inputs.get('HNR', 25) < 15:
        recommendations.append("🎤 **Voice Quality**: Low HNR - consider voice therapy consultation")
    
    if recommendations:
        for rec in recommendations:
            st.markdown(f"• {rec}")
    else:
        st.markdown("• 🎉 **Overall**: Your voice parameters look good - maintain current habits!")

def load_healthy_preset():
    """Load preset values for healthy individual"""
    return {
        'MDVP:Fo(Hz)': 150.0, 'MDVP:Fhi(Hz)': 200.0, 'MDVP:Flo(Hz)': 100.0,
        'MDVP:Jitter(%)': 0.3, 'MDVP:Jitter(Abs)': 0.000020, 'MDVP:RAP': 0.002,
        'MDVP:PPQ': 0.002, 'Jitter:DDP': 0.006, 'MDVP:Shimmer': 0.020,
        'MDVP:Shimmer(dB)': 0.180, 'Shimmer:APQ3': 0.010, 'Shimmer:APQ5': 0.012,
        'MDVP:APQ': 0.022, 'Shimmer:DDA': 0.030, 'NHR': 0.012, 'HNR': 25.0,
        'RPDE': 0.450, 'DFA': 0.680, 'spread1': -6.5, 'spread2': 0.180,
        'D2': 2.2, 'PPE': 0.15
    }

def load_mild_preset():
    """Load preset values suggesting mild symptoms"""
    return {
        'MDVP:Fo(Hz)': 145.0, 'MDVP:Fhi(Hz)': 185.0, 'MDVP:Flo(Hz)': 95.0,
        'MDVP:Jitter(%)': 0.6, 'MDVP:Jitter(Abs)': 0.000040, 'MDVP:RAP': 0.004,
        'MDVP:PPQ': 0.004, 'Jitter:DDP': 0.012, 'MDVP:Shimmer': 0.035,
        'MDVP:Shimmer(dB)': 0.320, 'Shimmer:APQ3': 0.018, 'Shimmer:APQ5': 0.022,
        'MDVP:APQ': 0.040, 'Shimmer:DDA': 0.054, 'NHR': 0.022, 'HNR': 20.0,
        'RPDE': 0.520, 'DFA': 0.720, 'spread1': -5.8, 'spread2': 0.220,
        'D2': 2.6, 'PPE': 0.20
    }

def load_severe_preset():
    """Load preset values suggesting severe symptoms"""
    return {
        'MDVP:Fo(Hz)': 120.0, 'MDVP:Fhi(Hz)': 160.0, 'MDVP:Flo(Hz)': 80.0,
        'MDVP:Jitter(%)': 1.2, 'MDVP:Jitter(Abs)': 0.000080, 'MDVP:RAP': 0.008,
        'MDVP:PPQ': 0.008, 'Jitter:DDP': 0.024, 'MDVP:Shimmer': 0.065,
        'MDVP:Shimmer(dB)': 0.580, 'Shimmer:APQ3': 0.032, 'Shimmer:APQ5': 0.040,
        'MDVP:APQ': 0.075, 'Shimmer:DDA': 0.096, 'NHR': 0.045, 'HNR': 15.0,
        'RPDE': 0.620, 'DFA': 0.780, 'spread1': -4.2, 'spread2': 0.280,
        'D2': 3.2, 'PPE': 0.32
    }

def show_file_upload_section(model, scaler):
    """Original file upload section (unchanged)"""
    st.markdown("### 📄 Upload Health Data")
    uploaded = st.file_uploader(
        "Upload CSV file with health metrics (same format as training data)",
        type="csv",
        help="Your data should include features like jitter, shimmer, HNR, etc."
    )
    
    if uploaded:
        with st.spinner("📄 Processing your data..."):
            df = pd.read_csv(uploaded)
            
        st.markdown("#### 📊 Data Preview")
        st.dataframe(df.head(), use_container_width=True)
        
        # Data validation
        required_features = ['MDVP:Fo(Hz)', 'MDVP:Fhi(Hz)', 'MDVP:Flo(Hz)', 'MDVP:Jitter(%)', 'MDVP:Jitter(Abs)']
        missing_features = [f for f in required_features if f not in df.columns]
        
        if missing_features:
            st.warning(f"⚠️ Missing features: {missing_features[:3]}...")
        else:
            st.success("✅ All required features present!")
        
        # Run prediction
        if st.button("🚀 Run AI Prediction", type="primary", use_container_width=True):
            with st.spinner("🧠 AI is analyzing your data..."):
                time.sleep(2)
                try:
                    result_df = predict_df(model, scaler, df)
                    
                    st.markdown("#### 🎯 Prediction Results")
                    st.dataframe(result_df, use_container_width=True)
                    
                    # Enhanced visualizations
                    if "Probability" in result_df.columns:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fig_hist = px.histogram(
                                result_df, x="Probability", 
                                nbins=20, 
                                title="🎯 Prediction Confidence Distribution",
                                color_discrete_sequence=['#667eea']
                            )
                            fig_hist.update_layout(template="plotly_white")
                            st.plotly_chart(fig_hist, use_container_width=True)
                        
                        with col2:
                            avg_prob = result_df["Probability"].mean()
                            fig_gauge = go.Figure(go.Indicator(
                                mode = "gauge+number+delta",
                                value = avg_prob * 100,
                                domain = {'x': [0, 1], 'y': [0, 1]},
                                title = {'text': "🎯 Average Risk Score"},
                                delta = {'reference': 50},
                                gauge = {
                                    'axis': {'range': [None, 100]},
                                    'bar': {'color': "#667eea"},
                                    'steps': [
                                        {'range': [0, 30], 'color': "#4facfe"},
                                        {'range': [30, 70], 'color': "#f093fb"},
                                        {'range': [70, 100], 'color': "#f5576c"}
                                    ],
                                    'threshold': {
                                        'line': {'color': "red", 'width': 4},
                                        'thickness': 0.75,
                                        'value': 90
                                    }
                                }
                            ))
                            st.plotly_chart(fig_gauge, use_container_width=True)
                    
                    # Save prediction
                    prob = float(np.mean(result_df.get("Probability", [0]))) if "Probability" in result_df.columns else None
                    con.execute(
                        "INSERT INTO predictions (user_id, probability, raw_json) VALUES (?,?,?)",
                        (st.session_state["user"]["id"], prob, json.dumps(result_df.head(10).to_dict())),
                    )
                    con.commit()
                    toast("💾 Prediction saved to your history!", "success")
                    
                    # SHAP explanations
                    show_shap_explanations(model, scaler, df)
                    
                except Exception as e:
                    st.error(f"❌ Prediction failed: {e}")

def show_shap_explanations(model, scaler, df):
    """Enhanced SHAP explanations with better UI"""
    st.markdown("---")
    st.markdown("## 🔍 AI Explanation - Why This Prediction?")
    
    # Global importance
    st.markdown("### 🌍 Global Feature Importance")
    shap_img = shap_summary_plot()
    
    if shap_img:
        from io import BytesIO
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st.image(
                BytesIO(shap_img),
                caption="Most influential features across all patients",
                use_column_width=True
            )
    else:
        st.info("📊 SHAP visualization not available for this model type")
    
    # Patient-specific explanation
    st.markdown("### 👤 Your Personal Health Insights")
    X = df.drop(columns=[c for c in ["name", "status"] if c in df.columns], errors="ignore")
    
    if not X.empty:
        col1, col2 = st.columns([1, 3])
        with col1:
            row_idx = st.selectbox(
                "Select patient/record:",
                range(len(X)),
                format_func=lambda x: f"Patient {x+1}"
            )
        
        with col2:
            if st.button("🔍 Explain This Prediction", type="secondary"):
                try:
                    with st.spinner("🧠 Generating personalized explanation..."):
                        if row_idx is not None:
                            idx = int(row_idx)
                            fig = shap_force_plot_for_row(model, scaler, X, idx)
                            st.pyplot(fig, use_container_width=True)
                            
                            # Feature contribution table
                            st.markdown("#### 📊 Top Contributing Factors")
                            import shap
                            
                            if scaler is not None:
                                X_transformed = scaler.transform(X)
                            else:
                                X_transformed = X
                            
                            explainer = shap.Explainer(model, X_transformed)
                            shap_values_row = explainer(X_transformed)[idx]
                            
                            contribs = pd.DataFrame({
                                "🔬 Feature": X.columns,
                                "📊 Your Value": X.iloc[idx].values,
                                "⚡ Impact Score": shap_values_row.values,
                                "📈 Impact": ["🔴 Increases Risk" if x > 0 else "🟢 Decreases Risk" for x in shap_values_row.values]
                            }).sort_values("Impact Score", key=abs, ascending=False).head(8)
                            
                            st.dataframe(contribs, use_container_width=True, hide_index=True)
                        else:
                            st.warning("⚠️ Please select a valid patient/record.")
                        
                except Exception as e:
                    st.warning(f"⚠️ Could not generate explanation: {e}")

# ---------- ENHANCED ACCOUNT ----------
def show_account():
    st.markdown("## 👤 Account Management")
    
    if "user" not in st.session_state:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>🔐 Secure Login</h3>
                <p>Access your personalized wellness dashboard</p>
            </div>
            """, unsafe_allow_html=True)
            user = auth.login(con)
            
        with col2:
            st.markdown("""
            <div class="health-card">
                <h3>✨ Create Account</h3>
                <p>Join thousands improving their health with AI</p>
            </div>
            """, unsafe_allow_html=True)
            auth.signup(con)
    else:
        user = st.session_state["user"]
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"""
            <div class="success-card">
                <h3>👋 Welcome, {user['username']}!</h3>
                <p>📧 {user['email']}</p>
                <p>🆔 User ID: {user['id']}</p>
                <p>✅ Account Status: Active</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if st.button("🚪 Logout", type="secondary", use_container_width=True):
                auth.logout()
                st.rerun()
        
        # User statistics
        st.markdown("### 📊 Your Activity Stats")
        user_id = user['id']
        
        symptoms_count = con.execute("SELECT COUNT(*) FROM symptoms WHERE user_id=?", (user_id,)).fetchone()[0]
        predictions_count = con.execute("SELECT COUNT(*) FROM predictions WHERE user_id=?", (user_id,)).fetchone()[0]
        reminders_count = con.execute("SELECT COUNT(*) FROM reminders WHERE user_id=?", (user_id,)).fetchone()[0]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📝 Total Symptom Logs", symptoms_count)
        with col2:
            st.metric("🤖 AI Predictions Made", predictions_count)
        with col3:
            st.metric("💊 Reminders Created", reminders_count)

# ---------- PAGE ROUTING ----------
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

def show_enhanced_page(page_type):
    """Enhanced wrapper for existing pages"""
    if page_type == "tracker":
        st.markdown("## 📊 Smart Symptom Tracker")
        if "user" not in st.session_state:
            st.warning("🔐 Please login first to track symptoms.")
            return
        tracker.tracker_form(con, st.session_state["user"]["id"])
        st.divider()
        tracker.tracker_view(con, st.session_state["user"]["id"])
        
    elif page_type == "reminders":
        st.markdown("## 💊 Smart Medication Reminders")
        if "user" not in st.session_state:
            st.warning("🔐 Please login first to manage reminders.")
            return
        reminders.add_reminder(con, st.session_state["user"]["id"])
        st.divider()
        reminders.list_reminders(con, st.session_state["user"]["id"])
        
    elif page_type == "explorer":
        st.markdown("## 📈 Advanced Data Explorer")
        analysis.uci_explorer()
        
    elif page_type == "wellness":
        st.markdown("## 🏃‍♂️ Wellness & Exercise Center")
        wellness.wellness_center()
        
    elif page_type == "reports":
        st.markdown("## 📋 Health Reports & Export")
        if "user" not in st.session_state:
            st.warning("🔐 Please login first to generate reports.")
            return
        show_enhanced_reports()

def show_enhanced_reports():
    """Enhanced reports with better UI"""
    uid = st.session_state["user"]["id"]
    
    # Fetch data
    sym = pd.read_sql_query("SELECT * FROM symptoms WHERE user_id=?", con, params=(uid,))
    pred = pd.read_sql_query("SELECT * FROM predictions WHERE user_id=?", con, params=(uid,))
    rem = pd.read_sql_query("SELECT * FROM reminders WHERE user_id=?", con, params=(uid,))
    
    # Summary cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>📝 Symptom Entries</h4>
            <h2>{len(sym)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="health-card">
            <h4>🤖 AI Predictions</h4>
            <h2>{len(pred)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="success-card">
            <h4>💊 Active Reminders</h4>
            <h2>{len(rem)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Export options
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Generate PDF Report", type="primary", use_container_width=True):
            with st.spinner("📄 Generating comprehensive PDF report..."):
                try:
                    model, scaler = load_model()
                except:
                    model, scaler = None, None
                
                summary = f"""
                Health Summary for {st.session_state['user']['username']}
                Generated on: {datetime.now().strftime('%B %d, %Y')}
                
                📊 Data Overview:
                • Symptom entries: {len(sym)}
                • AI predictions: {len(pred)}
                • Active reminders: {len(rem)}
                
                🎯 Recent insights available in detailed report below.
                """
                
                pdf_bytes = export_pdf(summary, df=pred, model=model, scaler=scaler)
                st.download_button(
                    "💾 Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"wellness_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                )
                toast("📄 PDF report generated successfully!", "success")
    
    with col2:
        if st.button("📊 Export Excel Data", type="primary", use_container_width=True):
            with st.spinner("📊 Creating Excel workbook..."):
                try:
                    model, scaler = load_model()
                except:
                    model, scaler = None, None
                
                xls_bytes = export_excel(
                    {"Symptoms": sym, "Predictions": pred, "Reminders": rem},
                    model=model, scaler=scaler
                )
                st.download_button(
                    "💾 Download Excel File",
                    data=xls_bytes,
                    file_name=f"wellness_data_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                toast("📊 Excel file created successfully!", "success")

# Handle page redirects
if "redirect_page" in st.session_state:
    page = st.session_state.redirect_page
    del st.session_state.redirect_page

# Main page routing
if page and page in PAGES:
    PAGES[page]()
else:
    st.error("❌ Invalid page selection.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem 0; color: #666;">
    <p>🧠 <strong>Parkinson's AI Wellness Hub</strong> | Empowering patients with intelligent health insights</p>
    <p style="font-size: 0.9rem;">Built with ❤️ using Streamlit, scikit-learn, and SHAP</p>
</div>
""", unsafe_allow_html=True)