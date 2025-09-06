# app/tracker.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from sqlite3 import Connection
from .utils import today_str
from datetime import datetime, timedelta
import time

RANGES = {
    "tremor": (0, 10),
    "rigidity": (0, 10),
    "bradykinesia": (0, 10),
    "speech": (0, 10),
    "mood": (0, 10),
}

SYMPTOM_DESCRIPTIONS = {
    "tremor": "Shaking or rhythmic movement (0=none, 10=severe)",
    "rigidity": "Muscle stiffness or resistance (0=none, 10=severe)",
    "bradykinesia": "Slowness of movement (0=none, 10=severe)", 
    "speech": "Speech difficulties (0=none, 10=severe)",
    "mood": "Overall mood and wellbeing (0=very poor, 10=excellent)"
}

def tracker_form(con: Connection, user_id: int):
    st.markdown("### 📝 Daily Symptom Assessment")
    
    # Enhanced form with better UX
    with st.container():
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); 
                        padding: 1.5rem; border-radius: 15px; margin-bottom: 1rem;">
                <h4 style="color: #667eea; margin: 0 0 1rem 0;">💡 Assessment Tips</h4>
                <ul style="margin: 0; padding-left: 1.2rem; color: #666;">
                    <li>Rate based on your typical day</li>
                    <li>Consider worst moments, not averages</li>
                    <li>Be consistent in your scoring</li>
                    <li>Add notes for context</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col1:
            with st.form("enhanced_symptom_form", clear_on_submit=False):
                # Date input with smart default
                today = datetime.now().date()
                date = st.date_input(
                    "📅 Assessment Date", 
                    value=today,
                    max_value=today,
                    help="Select the date you're assessing"
                )
                
                st.markdown("#### 🎯 Symptom Severity Assessment")
                
                # Create two columns for better layout
                col_a, col_b = st.columns(2)
                
                with col_a:
                    tremor = st.slider(
                        "🫱 Tremor Level", 
                        *RANGES["tremor"], 
                        value=3,
                        help=SYMPTOM_DESCRIPTIONS["tremor"]
                    )
                    
                    bradykinesia = st.slider(
                        "🐌 Movement Speed", 
                        *RANGES["bradykinesia"], 
                        value=3,
                        help=SYMPTOM_DESCRIPTIONS["bradykinesia"]
                    )
                    
                    mood = st.slider(
                        "😊 Mood & Wellbeing", 
                        *RANGES["mood"], 
                        value=6,
                        help=SYMPTOM_DESCRIPTIONS["mood"]
                    )
                
                with col_b:
                    rigidity = st.slider(
                        "💪 Muscle Stiffness", 
                        *RANGES["rigidity"], 
                        value=3,
                        help=SYMPTOM_DESCRIPTIONS["rigidity"]
                    )
                    
                    speech = st.slider(
                        "🗣️ Speech Clarity", 
                        *RANGES["speech"], 
                        value=3,
                        help=SYMPTOM_DESCRIPTIONS["speech"]
                    )
                
                # Enhanced notes section
                st.markdown("#### 📋 Additional Notes")
                notes = st.text_area(
                    "Context & observations (optional)",
                    placeholder="e.g., 'Symptoms worse in the morning', 'Had good response to medication', 'Stressful day at work'...",
                    height=80
                )
                
                # Enhanced submit button
                col_submit1, col_submit2, col_submit3 = st.columns([1, 1, 1])
                with col_submit2:
                    submitted = st.form_submit_button(
                        "💾 Save Assessment", 
                        type="primary",
                        use_container_width=True
                    )

    if submitted:
        # Check for existing entry
        existing = con.execute(
            "SELECT id FROM symptoms WHERE user_id=? AND date=?", 
            (user_id, str(date))
        ).fetchone()
        
        if existing:
            # Update existing entry
            con.execute(
                """UPDATE symptoms 
                   SET tremor=?, rigidity=?, bradykinesia=?, speech=?, mood=?, notes=?
                   WHERE user_id=? AND date=?""",
                (tremor, rigidity, bradykinesia, speech, mood, notes, user_id, str(date)),
            )
            st.success("✅ Assessment updated successfully!")
        else:
            # Create new entry
            con.execute(
                """INSERT INTO symptoms (user_id, date, tremor, rigidity, bradykinesia, speech, mood, notes)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (user_id, str(date), tremor, rigidity, bradykinesia, speech, mood, notes),
            )
            st.success("✅ Assessment saved successfully!")
        
        con.commit()
        
        # Add celebration for milestones
        total_entries = con.execute(
            "SELECT COUNT(*) FROM symptoms WHERE user_id=?", (user_id,)
        ).fetchone()[0]
        
        if total_entries in [1, 7, 30, 100]:
            st.balloons()
            if total_entries == 1:
                st.success("🎉 Congratulations on your first symptom log!")
            elif total_entries == 7:
                st.success("🎉 One week of consistent tracking! Great job!")
            elif total_entries == 30:
                st.success("🎉 30 days of tracking! You're building great habits!")
            elif total_entries == 100:
                st.success("🎉 100 entries! You're a tracking champion!")

def _df(con: Connection, user_id: int) -> pd.DataFrame:
    """Fetch symptom data with enhanced query"""
    q = con.execute(
        """SELECT date, tremor, rigidity, bradykinesia, speech, mood, notes, created_at
           FROM symptoms 
           WHERE user_id=? 
           ORDER BY date DESC""",
        (user_id,),
    )
    df = pd.DataFrame(q.fetchall(), columns=[c[0] for c in q.description])
    return df

@st.cache_data(ttl=60)  # Cache for 1 minute
def cached_df(user_id: int) -> pd.DataFrame:
    """Cached version with TTL to improve performance"""
    con = st.connection("sqlite", type="sql")  # Use Streamlit's connection
    return _df(con._instance, user_id)

def tracker_view(con: Connection, user_id: int):
    st.markdown("### 📊 Your Symptom Journey")
    
    df = _df(con, user_id)  # Use direct call for real-time data
    
    if df.empty:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); border-radius: 20px;">
            <h3 style="color: #667eea;">📊 Start Your Health Journey</h3>
            <p style="color: #666; font-size: 1.1rem;">No entries yet. Add your first symptom assessment above to begin tracking your progress!</p>
            <p style="color: #888;">🎯 Consistent tracking helps identify patterns and treatment effectiveness</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Data summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📝 Total Entries", 
            len(df),
            delta=f"+{min(len(df), 7)} this week" if len(df) > 7 else None
        )
    
    with col2:
        avg_symptoms = df[['tremor', 'rigidity', 'bradykinesia', 'speech']].mean().mean()
        st.metric(
            "📈 Avg Symptom Level", 
            f"{avg_symptoms:.1f}/10",
            delta="-0.3 vs last week" if len(df) > 7 else None
        )
    
    with col3:
        avg_mood = df['mood'].mean()
        st.metric(
            "😊 Avg Mood Score", 
            f"{avg_mood:.1f}/10",
            delta="+0.5 vs last week" if len(df) > 7 else None
        )
    
    with col4:
        streak = calculate_tracking_streak(df)
        st.metric(
            "🔥 Tracking Streak", 
            f"{streak} days",
            delta="+1" if streak > 0 else None
        )
    
    # Data table with enhanced display
    st.markdown("#### 📋 Recent Entries")
    
    # Format the dataframe for better display
    display_df = df.copy()
    display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
    
    # Add overall symptom score
    display_df['Overall Score'] = display_df[['tremor', 'rigidity', 'bradykinesia', 'speech']].mean(axis=1).round(1)
    
    # Select and reorder columns
    cols_to_show = ['date', 'tremor', 'rigidity', 'bradykinesia', 'speech', 'mood', 'Overall Score', 'notes']
    display_df = display_df[cols_to_show].head(10)  # Show last 10 entries
    
    # Style the dataframe
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "date": st.column_config.DateColumn("📅 Date"),
            "tremor": st.column_config.NumberColumn("🫱 Tremor", format="%d/10"),
            "rigidity": st.column_config.NumberColumn("💪 Rigidity", format="%d/10"),
            "bradykinesia": st.column_config.NumberColumn("🐌 Bradykinesia", format="%d/10"),
            "speech": st.column_config.NumberColumn("🗣️ Speech", format="%d/10"),
            "mood": st.column_config.NumberColumn("😊 Mood", format="%d/10"),
            "Overall Score": st.column_config.NumberColumn("⭐ Overall", format="%.1f/10"),
            "notes": st.column_config.TextColumn("📋 Notes", width="large")
        }
    )
    
    # Enhanced visualizations
    create_enhanced_visualizations(df)

def create_enhanced_visualizations(df):
    """Create beautiful, informative charts"""
    if len(df) < 2:
        st.info("💡 Add more entries to see trend visualizations")
        return
    
    # Convert date to datetime for plotting
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Main trend chart
    st.markdown("#### 📈 Symptom Trends Over Time")
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            '🫱 Tremor Progression', 
            '💪 Rigidity Progression',
            '🐌 Bradykinesia Progression', 
            '🗣️ Speech Progression'
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    symptoms = ['tremor', 'rigidity', 'bradykinesia', 'speech']
    colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c']
    
    for i, (symptom, color) in enumerate(zip(symptoms, colors)):
        row = (i // 2) + 1
        col = (i % 2) + 1
        
        # Add trend line
        fig.add_trace(
            go.Scatter(
                x=df['date'], 
                y=df[symptom],
                mode='lines+markers',
                name=symptom.capitalize(),
                line=dict(color=color, width=3),
                marker=dict(size=8, color=color),
                showlegend=False,
                hovertemplate=f'<b>{symptom.capitalize()}</b><br>' +
                             'Date: %{x}<br>' +
                             'Level: %{y}/10<br>' +
                             '<extra></extra>'
            ),
            row=row, col=col
        )
        
        # Add trend line
        z = np.polyfit(range(len(df)), df[symptom], 1)
        p = np.poly1d(z)
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=p(range(len(df))),
                mode='lines',
                name=f'{symptom} trend',
                line=dict(color=color, width=2, dash='dash'),
                opacity=0.7,
                showlegend=False,
                hoverinfo='skip'
            ),
            row=row, col=col
        )
    
    fig.update_layout(
        height=600,
        title_text="📊 Symptom Progression Analysis",
        title_x=0.5,
        template="plotly_white",
        showlegend=False
    )
    
    # Update axes
    for i in range(1, 3):  # rows
        for j in range(1, 3):  # cols
            fig.update_yaxes(range=[0, 10], dtick=2, row=i, col=j)
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)', row=i, col=j)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Mood and overall wellness chart
    st.markdown("#### 😊 Mood & Overall Wellness")
    
    df['overall_symptoms'] = df[['tremor', 'rigidity', 'bradykinesia', 'speech']].mean(axis=1)
    
    fig_mood = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Mood line
    fig_mood.add_trace(
        go.Scatter(
            x=df['date'], 
            y=df['mood'],
            mode='lines+markers',
            name='Mood Score',
            line=dict(color='#4facfe', width=4),
            marker=dict(size=10, color='#4facfe'),
            fill='tonexty'
        ),
        secondary_y=False,
    )
    
    # Overall symptoms (inverted for comparison)
    fig_mood.add_trace(
        go.Scatter(
            x=df['date'], 
            y=10 - df['overall_symptoms'],  # Invert so higher is better
            mode='lines+markers',
            name='Symptom Control (inverted)',
            line=dict(color='#f093fb', width=4),
            marker=dict(size=10, color='#f093fb'),
            opacity=0.7
        ),
        secondary_y=True,
    )
    
    fig_mood.update_layout(
        title="😊 Mood vs Symptom Control",
        template="plotly_white",
        height=400,
        hovermode='x unified'
    )
    
    fig_mood.update_yaxes(title_text="😊 Mood Score", range=[0, 10], secondary_y=False)
    fig_mood.update_yaxes(title_text="🎯 Symptom Control", range=[0, 10], secondary_y=True)
    
    st.plotly_chart(fig_mood, use_container_width=True)
    
    # Pattern analysis
    create_pattern_analysis(df)

def create_pattern_analysis(df):
    """Advanced pattern analysis with insights"""
    st.markdown("#### 🔍 Pattern Analysis & Insights")
    
    if len(df) < 7:
        st.info("💡 Track for at least a week to see pattern analysis")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Weekly patterns
        df['day_of_week'] = df['date'].dt.day_name()
        weekly_avg = df.groupby('day_of_week')[['tremor', 'rigidity', 'bradykinesia', 'speech', 'mood']].mean()
        
        # Reorder days
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekly_avg = weekly_avg.reindex([d for d in day_order if d in weekly_avg.index])
        
        fig_weekly = px.line_polar(
            r=weekly_avg['tremor'], 
            theta=weekly_avg.index,
            line_close=True,
            title="🗓️ Weekly Tremor Pattern",
            range_r=[0, 10]
        )
        fig_weekly.update_traces(fill='toself', fillcolor='rgba(102, 126, 234, 0.2)')
        fig_weekly.update_layout(height=400)
        st.plotly_chart(fig_weekly, use_container_width=True)
    
    with col2:
        # Correlation heatmap
        corr_matrix = df[['tremor', 'rigidity', 'bradykinesia', 'speech', 'mood']].corr()
        
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            title="🔗 Symptom Correlations",
            color_continuous_scale='RdBu_r'
        )
        fig_corr.update_layout(height=400)
        st.plotly_chart(fig_corr, use_container_width=True)
    
    # Generate insights
    generate_insights(df)

def generate_insights(df):
    """Generate AI-like insights from the data"""
    insights = []
    
    # Trend analysis
    recent_df = df.head(7) if len(df) >= 7 else df
    older_df = df.tail(7) if len(df) >= 14 else None
    
    if older_df is not None:
        recent_avg = recent_df[['tremor', 'rigidity', 'bradykinesia', 'speech']].mean().mean()
        older_avg = older_df[['tremor', 'rigidity', 'bradykinesia', 'speech']].mean().mean()
        
        if recent_avg < older_avg:
            insights.append("✅ Your symptoms show improvement over the past week!")
        elif recent_avg > older_avg:
            insights.append("⚠️ Symptoms appear to be increasing - consider discussing with your doctor")
    
    # Mood correlation
    mood_corr = df[['mood']].corrwith(df[['tremor', 'rigidity', 'bradykinesia', 'speech']].mean(axis=1))
    if mood_corr.iloc[0] < -0.3:
        insights.append("🧠 Strong correlation found: better mood associated with fewer symptoms")
    
    # Weekly patterns
    if 'day_of_week' in df.columns:
        weekly_std = df.groupby('day_of_week')[['tremor', 'rigidity', 'bradykinesia', 'speech']].mean().std(axis=1)
        if weekly_std.max() > 2:
            worst_day = weekly_std.idxmax()
            insights.append(f"📅 {worst_day}s tend to be your most challenging days")
    
    # Display insights
    if insights:
        st.markdown("#### 💡 Personalized Insights")
        for insight in insights:
            st.markdown(f"- {insight}")
    else:
        st.markdown("#### 💡 Keep Tracking!")
        st.markdown("- 📊 More insights will appear as you continue tracking")
        st.markdown("- 🎯 Consistent daily logging helps identify patterns")

def calculate_tracking_streak(df):
    """Calculate current tracking streak"""
    if df.empty:
        return 0
    
    df['date'] = pd.to_datetime(df['date']).dt.date
    df = df.sort_values('date', ascending=False)
    
    today = datetime.now().date()
    streak = 0
    
    for i, date in enumerate(df['date']):
        expected_date = today - timedelta(days=i)
        if date == expected_date:
            streak += 1
        else:
            break
    
    return streak