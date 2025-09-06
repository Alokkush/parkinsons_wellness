# app/wellness.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import time

# Enhanced exercise database with detailed information
EXERCISE_DATABASE = {
    "LSVT BIG Movements": {
        "description": "Large amplitude movements to combat bradykinesia",
        "duration": "20-30 min",
        "difficulty": "Beginner",
        "benefits": ["Improved movement amplitude", "Better posture", "Reduced stiffness"],
        "instructions": [
            "Stand with feet shoulder-width apart",
            "Raise arms overhead as high as possible",
            "Make movements BIG and exaggerated",
            "Hold for 2 seconds at peak amplitude",
            "Repeat 10-15 times"
        ],
        "video_url": "https://example.com/lsvt-big",
        "category": "Movement Therapy"
    },
    
    "Boxing Training": {
        "description": "Non-contact boxing for coordination and strength",
        "duration": "30-45 min",
        "difficulty": "Intermediate",
        "benefits": ["Enhanced coordination", "Improved balance", "Cardiovascular fitness"],
        "instructions": [
            "Warm up with light shadowboxing",
            "Practice jabs and crosses",
            "Work on footwork and ducking",
            "Use focus mitts if available",
            "Cool down with stretching"
        ],
        "video_url": "https://example.com/boxing-pd",
        "category": "Cardio & Coordination"
    },
    
    "Tango Dancing": {
        "description": "Argentine tango for balance and cognitive function",
        "duration": "45-60 min",
        "difficulty": "Intermediate",
        "benefits": ["Better balance", "Cognitive stimulation", "Social interaction"],
        "instructions": [
            "Start with basic walking steps",
            "Practice weight transfer",
            "Focus on connection with partner",
            "Work on backward walking",
            "Include pauses and direction changes"
        ],
        "video_url": "https://example.com/tango-pd",
        "category": "Dance Therapy"
    },
    
    "Tai Chi": {
        "description": "Gentle flowing movements for balance and flexibility",
        "duration": "30-45 min",
        "difficulty": "Beginner",
        "benefits": ["Improved balance", "Stress reduction", "Joint flexibility"],
        "instructions": [
            "Begin with centering and breathing",
            "Practice weight shifting",
            "Move slowly and deliberately",
            "Focus on smooth transitions",
            "End with relaxation"
        ],
        "video_url": "https://example.com/taichi-pd",
        "category": "Mind-Body"
    },
    
    "Voice Therapy (LSVT LOUD)": {
        "description": "Voice amplification exercises",
        "duration": "15-20 min",
        "difficulty": "Beginner",
        "benefits": ["Stronger voice", "Better speech clarity", "Improved swallowing"],
        "instructions": [
            "Take deep breath and say 'AH' loudly",
            "Practice reading aloud with emphasis",
            "Work on pitch variation",
            "Practice tongue twisters",
            "Record and review your voice"
        ],
        "video_url": "https://example.com/lsvt-loud",
        "category": "Speech Therapy"
    },
    
    "Resistance Band Training": {
        "description": "Strength training using resistance bands",
        "duration": "25-35 min",
        "difficulty": "Beginner-Intermediate",
        "benefits": ["Muscle strength", "Bone density", "Functional movement"],
        "instructions": [
            "Warm up with gentle stretching",
            "Start with light resistance",
            "Focus on controlled movements",
            "Work all major muscle groups",
            "Cool down with stretching"
        ],
        "video_url": "https://example.com/resistance-pd",
        "category": "Strength Training"
    },
    
    "Water Aerobics": {
        "description": "Low-impact exercise in water",
        "duration": "30-45 min",
        "difficulty": "Beginner",
        "benefits": ["Joint-friendly exercise", "Improved circulation", "Reduced fall risk"],
        "instructions": [
            "Enter water gradually",
            "Start with walking in water",
            "Add arm movements",
            "Practice balance exercises",
            "Include flexibility work"
        ],
        "video_url": "https://example.com/water-aerobics-pd",
        "category": "Aquatic Therapy"
    }
}

LIFESTYLE_TIPS = {
    "Medication Management": [
        "Take medications on a consistent schedule - use phone alarms",
        "Keep a medication diary to track effectiveness",
        "Never stop medications abruptly - consult your doctor first",
        "Store medications properly (temperature, humidity)",
        "Use pill organizers to prevent missed doses"
    ],
    
    "Sleep Optimization": [
        "Maintain consistent sleep/wake times, even on weekends",
        "Create a relaxing bedtime routine 1 hour before sleep",
        "Keep bedroom cool (65-68°F), dark, and quiet",
        "Avoid caffeine 6+ hours before bedtime",
        "Consider a weighted blanket for REM sleep behavior disorder"
    ],
    
    "Nutrition Guidelines": [
        "Eat high-fiber foods to combat constipation (prunes, beans, vegetables)",
        "Stay hydrated - aim for 8-10 glasses of water daily",
        "Take levodopa 30-60 minutes before meals for better absorption",
        "Limit protein intake during the day if it interferes with medication",
        "Include antioxidant-rich foods (berries, leafy greens, nuts)"
    ],
    
    "Stress Management": [
        "Practice deep breathing exercises for 5-10 minutes daily",
        "Try meditation or mindfulness apps",
        "Maintain social connections - join support groups",
        "Engage in hobbies that bring joy and purpose",
        "Consider professional counseling for emotional support"
    ],
    
    "Fall Prevention": [
        "Remove tripping hazards (rugs, cords, clutter)",
        "Install grab bars in bathroom and stairways",
        "Use non-slip mats in shower and tub",
        "Improve lighting throughout your home",
        "Wear supportive, non-slip shoes indoors and out"
    ],
    
    "Daily Living Strategies": [
        "Break complex tasks into smaller, manageable steps",
        "Use visual or auditory cues to initiate movement",
        "Plan demanding activities for when medications are most effective",
        "Practice dual-task training (walking while talking)",
        "Use assistive devices when needed (walkers, grab bars)"
    ]
}

MOTIVATIONAL_QUOTES = [
    "Every step forward is progress, no matter how small. 🌟",
    "Your strength is greater than any challenge. 💪",
    "Today's exercise is tomorrow's mobility. 🚀",
    "Consistency beats perfection every time. ⭐",
    "You are more resilient than you know. 🌈",
    "Small actions lead to big changes. 🌱",
    "Your journey inspires others. ✨",
    "Progress is measured in effort, not perfection. 🎯"
]

def wellness_center():
    st.markdown("## 🏃‍♂️ Wellness & Exercise Center")
    
    # Welcome section with motivational quote
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        quote = random.choice(MOTIVATIONAL_QUOTES)
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); border-radius: 20px; margin-bottom: 2rem;">
            <h3 style="color: #667eea; margin: 0;">{quote}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏋️‍♂️ Exercise Library", 
        "📅 Personal Plan", 
        "💡 Lifestyle Tips", 
        "📊 Progress Tracking",
        "🎯 Goals & Achievements"
    ])
    
    with tab1:
        show_exercise_library()
    
    with tab2:
        show_personal_plan()
    
    with tab3:
        show_lifestyle_tips()
    
    with tab4:
        show_progress_tracking()
    
    with tab5:
        show_goals_achievements()

def show_exercise_library():
    """Enhanced exercise library with filtering and detailed views"""
    st.markdown("### 🏋️‍♂️ Comprehensive Exercise Library")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        categories = list(set(ex['category'] for ex in EXERCISE_DATABASE.values()))
        selected_category = st.selectbox("Filter by Category", ["All"] + categories)
    
    with col2:
        difficulties = list(set(ex['difficulty'] for ex in EXERCISE_DATABASE.values()))
        selected_difficulty = st.selectbox("Filter by Difficulty", ["All"] + difficulties)
    
    with col3:
        durations = ["All", "< 20 min", "20-30 min", "30-45 min", "> 45 min"]
        selected_duration = st.selectbox("Filter by Duration", durations)
    
    # Filter exercises
    filtered_exercises = {}
    for name, exercise in EXERCISE_DATABASE.items():
        # Category filter
        if selected_category != "All" and exercise['category'] != selected_category:
            continue
        # Difficulty filter
        if selected_difficulty != "All" and exercise['difficulty'] != selected_difficulty:
            continue
        # Duration filter (simplified logic)
        if selected_duration != "All":
            duration_match = True  # Simplified for demo
        
        filtered_exercises[name] = exercise
    
    # Display exercises in cards
    if filtered_exercises:
        for i, (name, exercise) in enumerate(filtered_exercises.items()):
            if i % 2 == 0:
                cols = st.columns(2)
            
            with cols[i % 2]:
                create_exercise_card(name, exercise)
    else:
        st.info("No exercises match your filters. Try adjusting your criteria.")

def create_exercise_card(name, exercise):
    """Create an attractive exercise card"""
    # Color coding by difficulty
    colors = {
        "Beginner": "#4facfe",
        "Intermediate": "#f093fb", 
        "Advanced": "#f5576c"
    }
    color = colors.get(exercise['difficulty'], "#667eea")
    
    with st.expander(f"🎯 {name}", expanded=False):
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {color}22 0%, {color}11 100%); padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border-left: 4px solid {color};">
            <p><strong>📝 Description:</strong> {exercise['description']}</p>
            <p><strong>⏱️ Duration:</strong> {exercise['duration']} | <strong>📊 Difficulty:</strong> {exercise['difficulty']}</p>
            <p><strong>🏷️ Category:</strong> {exercise['category']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Benefits
        st.markdown("**✅ Benefits:**")
        for benefit in exercise['benefits']:
            st.markdown(f"• {benefit}")
        
        # Instructions
        st.markdown("**📋 Instructions:**")
        for i, instruction in enumerate(exercise['instructions'], 1):
            st.markdown(f"{i}. {instruction}")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(f"⭐ Add to Plan", key=f"add_{name}"):
                if 'workout_plan' not in st.session_state:
                    st.session_state.workout_plan = []
                if name not in st.session_state.workout_plan:
                    st.session_state.workout_plan.append(name)
                    st.success(f"Added {name} to your plan!")
                else:
                    st.info("Already in your plan!")
        
        with col2:
            if st.button(f"✅ Mark Complete", key=f"complete_{name}"):
                if 'completed_exercises' not in st.session_state:
                    st.session_state.completed_exercises = []
                st.session_state.completed_exercises.append({
                    'exercise': name,
                    'date': datetime.now(),
                    'duration': exercise['duration']
                })
                st.success("Exercise logged! 🎉")
                st.balloons()
        
        with col3:
            if st.button(f"📺 Watch Video", key=f"video_{name}"):
                st.info("Video feature coming soon!")

def show_personal_plan():
    """Personalized exercise plan generator"""
    st.markdown("### 📅 Your Personalized Exercise Plan")
    
    # Quick assessment
    with st.expander("🎯 Quick Assessment (Optional)", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            current_activity = st.select_slider(
                "Current Activity Level",
                options=["Sedentary", "Light", "Moderate", "Active", "Very Active"],
                value="Light"
            )
            
            primary_symptoms = st.multiselect(
                "Primary Symptoms",
                ["Tremor", "Rigidity", "Bradykinesia", "Balance Issues", "Speech Issues", "Freezing"],
                default=["Tremor", "Rigidity"]
            )
        
        with col2:
            exercise_goals = st.multiselect(
                "Exercise Goals",
                ["Improve Balance", "Increase Strength", "Better Flexibility", 
                 "Enhance Coordination", "Boost Mood", "Social Interaction"],
                default=["Improve Balance", "Increase Strength"]
            )
            
            available_time = st.select_slider(
                "Time Available Daily",
                options=["15-30 min", "30-45 min", "45-60 min", "60+ min"],
                value="30-45 min"
            )
        
        if st.button("🚀 Generate Personalized Plan", type="primary"):
            generate_personalized_plan(current_activity, primary_symptoms, exercise_goals, available_time)
    
    # Current plan display
    if 'workout_plan' in st.session_state and st.session_state.workout_plan:
        st.markdown("#### 📋 Your Current Plan")
        
        for i, exercise_name in enumerate(st.session_state.workout_plan):
            exercise = EXERCISE_DATABASE[exercise_name]
            
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{i+1}. {exercise_name}** ({exercise['duration']})")
                st.markdown(f"   *{exercise['description']}*")
            
            with col2:
                if st.button("✅", key=f"plan_complete_{i}", help="Mark as completed"):
                    if 'completed_exercises' not in st.session_state:
                        st.session_state.completed_exercises = []
                    st.session_state.completed_exercises.append({
                        'exercise': exercise_name,
                        'date': datetime.now(),
                        'duration': exercise['duration']
                    })
                    st.success("Completed! 🎉")
            
            with col3:
                if st.button("🗑️", key=f"plan_remove_{i}", help="Remove from plan"):
                    st.session_state.workout_plan.remove(exercise_name)
                    st.rerun()
        
        # Plan statistics
        total_time = len(st.session_state.workout_plan) * 30  # Simplified calculation
        st.markdown(f"**📊 Plan Summary:** {len(st.session_state.workout_plan)} exercises • ~{total_time} minutes total")
    
    else:
        st.info("🎯 No exercises in your plan yet. Add some from the Exercise Library or generate a personalized plan above!")

def generate_personalized_plan(activity_level, symptoms, goals, time_available):
    """Generate a personalized exercise plan based on assessment"""
    
    # Simple algorithm to select exercises
    recommended_exercises = []
    
    # Base recommendations by symptoms
    if "Balance Issues" in symptoms:
        recommended_exercises.extend(["Tai Chi", "Tango Dancing"])
    if "Tremor" in symptoms or "Rigidity" in symptoms:
        recommended_exercises.extend(["LSVT BIG Movements", "Boxing Training"])
    if "Speech Issues" in symptoms:
        recommended_exercises.append("Voice Therapy (LSVT LOUD)")
    if "Bradykinesia" in symptoms:
        recommended_exercises.extend(["LSVT BIG Movements", "Boxing Training"])
    
    # Add based on goals
    if "Improve Balance" in goals:
        recommended_exercises.extend(["Tai Chi", "Tango Dancing"])
    if "Increase Strength" in goals:
        recommended_exercises.extend(["Resistance Band Training", "Boxing Training"])
    if "Better Flexibility" in goals:
        recommended_exercises.extend(["Tai Chi", "Water Aerobics"])
    
    # Remove duplicates and limit based on time
    recommended_exercises = list(set(recommended_exercises))
    
    # Adjust for activity level
    max_exercises = {
        "Sedentary": 2,
        "Light": 3,
        "Moderate": 4,
        "Active": 5,
        "Very Active": 6
    }.get(activity_level, 3)
    
    final_plan = recommended_exercises[:max_exercises]
    
    # Update session state
    st.session_state.workout_plan = final_plan
    
    st.success(f"🎉 Generated personalized plan with {len(final_plan)} exercises!")
    st.rerun()

def show_lifestyle_tips():
    """Enhanced lifestyle tips with interactive features"""
    st.markdown("### 💡 Lifestyle & Wellness Tips")
    
    # Tip categories in expandable sections
    for category, tips in LIFESTYLE_TIPS.items():
        with st.expander(f"📚 {category}", expanded=False):
            for i, tip in enumerate(tips, 1):
                col1, col2 = st.columns([10, 1])
                with col1:
                    st.markdown(f"**{i}.** {tip}")
                with col2:
                    if st.button("✅", key=f"tip_{category}_{i}", help="Mark as implemented"):
                        st.success("Great job implementing this tip! 🎉")
    
    # Daily wellness checklist
    st.markdown("### ✅ Daily Wellness Checklist")
    
    checklist_items = [
        "Took medications on schedule",
        "Did at least 20 minutes of exercise",
        "Practiced deep breathing or meditation",
        "Stayed hydrated (8+ glasses of water)",
        "Got adequate sleep (7-9 hours)",
        "Connected with family/friends",
        "Practiced speech exercises",
        "Maintained good posture"
    ]
    
    completed_today = 0
    col1, col2 = st.columns(2)
    
    for i, item in enumerate(checklist_items):
        with col1 if i % 2 == 0 else col2:
            if st.checkbox(item, key=f"checklist_{i}"):
                completed_today += 1
    
    # Progress visualization
    progress_percentage = (completed_today / len(checklist_items)) * 100
    
    st.markdown("#### 📊 Today's Wellness Score")
    
    # Create a circular progress indicator
    fig = go.Figure(data=[go.Pie(
        values=[completed_today, len(checklist_items) - completed_today],
        labels=['Completed', 'Remaining'],
        hole=0.7,
        marker_colors=['#4facfe', '#e0e0e0'],
        textinfo='none',
        hoverinfo='skip'
    )])
    
    fig.update_layout(
        annotations=[
            dict(text=f'{progress_percentage:.0f}%<br>Complete', 
                 x=0.5, y=0.5, font_size=20, showarrow=False)
        ],
        showlegend=False,
        height=300,
        margin=dict(t=0, b=0, l=0, r=0)
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.plotly_chart(fig, use_container_width=True)
    
    if progress_percentage >= 80:
        st.success("🌟 Excellent wellness habits today!")
    elif progress_percentage >= 60:
        st.info("👍 Good progress - keep it up!")
    else:
        st.warning("💪 There's room for improvement today!")

def show_progress_tracking():
    """Track and visualize wellness progress"""
    st.markdown("### 📊 Progress Tracking & Analytics")
    
    # Exercise completion history
    if 'completed_exercises' in st.session_state and st.session_state.completed_exercises:
        df_exercises = pd.DataFrame(st.session_state.completed_exercises)
        df_exercises['date'] = pd.to_datetime(df_exercises['date']).dt.date
        
        # Exercise frequency chart
        exercise_counts = df_exercises['exercise'].value_counts()
        
        fig_freq = px.bar(
            x=exercise_counts.index,
            y=exercise_counts.values,
            title="🏋️‍♂️ Exercise Completion Frequency",
            labels={'x': 'Exercise Type', 'y': 'Times Completed'},
            color=exercise_counts.values,
            color_continuous_scale='viridis'
        )
        fig_freq.update_layout(showlegend=False)
        st.plotly_chart(fig_freq, use_container_width=True)
        
        # Weekly activity chart
        df_exercises['week'] = pd.to_datetime(df_exercises['date']).dt.isocalendar().week
        weekly_counts = df_exercises.groupby('week').size()
        
        fig_weekly = px.line(
            x=weekly_counts.index,
            y=weekly_counts.values,
            title="📅 Weekly Exercise Activity",
            labels={'x': 'Week Number', 'y': 'Exercises Completed'},
            markers=True
        )
        st.plotly_chart(fig_weekly, use_container_width=True)
        
        # Recent activity summary
        st.markdown("#### 📈 Recent Activity Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Exercises", len(st.session_state.completed_exercises))
        
        with col2:
            unique_exercises = len(df_exercises['exercise'].unique())
            st.metric("Exercise Variety", unique_exercises)
        
        with col3:
            last_7_days = df_exercises[
                df_exercises['date'] >= (datetime.now().date() - timedelta(days=7))
            ]
            st.metric("This Week", len(last_7_days))
        
        with col4:
            # Calculate streak
            dates_sorted = sorted(df_exercises['date'].unique(), reverse=True)
            current_streak = calculate_exercise_streak(dates_sorted)
            st.metric("Current Streak", f"{current_streak} days")
        
    else:
        st.info("📊 Start completing exercises to see your progress analytics!")
        
        # Sample visualization for demo
        sample_data = pd.DataFrame({
            'Week': range(1, 9),
            'Exercises': [2, 3, 4, 3, 5, 4, 6, 5]
        })
        
        fig_sample = px.line(
            sample_data, x='Week', y='Exercises',
            title="📅 Sample: Weekly Exercise Progress",
            markers=True
        )
        st.plotly_chart(fig_sample, use_container_width=True)

def show_goals_achievements():
    """Goal setting and achievement tracking"""
    st.markdown("### 🎯 Goals & Achievements")
    
    # Goal setting section
    st.markdown("#### 🎯 Set Your Wellness Goals")
    
    with st.form("wellness_goals"):
        goal_categories = [
            "Exercise Consistency", "Medication Adherence", "Sleep Quality",
            "Stress Management", "Social Engagement", "Symptom Management"
        ]
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_goal = st.selectbox("Goal Category", goal_categories)
            goal_description = st.text_area(
                "Goal Description",
                placeholder="e.g., Complete 20 minutes of exercise 5 days per week"
            )
        
        with col2:
            target_date = st.date_input("Target Date", value=datetime.now().date() + timedelta(days=30))
            goal_priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        
        submitted = st.form_submit_button("💾 Save Goal", type="primary")
        
        if submitted and goal_description:
            if 'wellness_goals' not in st.session_state:
                st.session_state.wellness_goals = []
            
            new_goal = {
                'id': len(st.session_state.wellness_goals),
                'category': selected_goal,
                'description': goal_description,
                'target_date': target_date,
                'priority': goal_priority,
                'created_date': datetime.now().date(),
                'completed': False,
                'progress': 0
            }
            
            st.session_state.wellness_goals.append(new_goal)
            st.success("🎉 Goal saved successfully!")
    
    # Display current goals
    if 'wellness_goals' in st.session_state and st.session_state.wellness_goals:
        st.markdown("#### 📋 Your Current Goals")
        
        for goal in st.session_state.wellness_goals:
            if not goal['completed']:
                create_goal_card(goal)
    
    # Achievement badges
    st.markdown("#### 🏆 Achievement Badges")
    
    achievements = calculate_achievements()
    
    cols = st.columns(4)
    for i, (badge, earned) in enumerate(achievements.items()):
        with cols[i % 4]:
            if earned:
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 15px; margin: 0.5rem 0; color: white;">
                    <h3 style="margin: 0; font-size: 2rem;">🏆</h3>
                    <p style="margin: 0; font-weight: bold;">{badge}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; background: rgba(128, 128, 128, 0.2); border-radius: 15px; margin: 0.5rem 0; color: #666;">
                    <h3 style="margin: 0; font-size: 2rem;">🔒</h3>
                    <p style="margin: 0;">{badge}</p>
                </div>
                """, unsafe_allow_html=True)

def create_goal_card(goal):
    """Create a goal tracking card"""
    days_remaining = (goal['target_date'] - datetime.now().date()).days
    
    color = {
        'High': '#f5576c',
        'Medium': '#f093fb', 
        'Low': '#4facfe'
    }.get(goal['priority'], '#667eea')
    
    with st.expander(f"🎯 {goal['description'][:50]}...", expanded=False):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**Category:** {goal['category']}")
            st.markdown(f"**Priority:** {goal['priority']}")
            st.markdown(f"**Target Date:** {goal['target_date']}")
            st.markdown(f"**Days Remaining:** {days_remaining}")
            
            # Progress slider
            progress = st.slider(
                "Progress (%)", 
                0, 100, 
                value=goal['progress'],
                key=f"progress_{goal['id']}"
            )
            
            # Update progress
            goal['progress'] = progress
        
        with col2:
            if st.button("✅ Complete", key=f"complete_goal_{goal['id']}"):
                goal['completed'] = True
                st.success("🎉 Goal completed! Congratulations!")
                st.balloons()
                st.rerun()
            
            if st.button("🗑️ Delete", key=f"delete_goal_{goal['id']}"):
                st.session_state.wellness_goals = [
                    g for g in st.session_state.wellness_goals if g['id'] != goal['id']
                ]
                st.rerun()

def calculate_exercise_streak(dates_list):
    """Calculate current exercise streak"""
    if not dates_list:
        return 0
    
    today = datetime.now().date()
    streak = 0
    
    for i, date in enumerate(dates_list):
        expected_date = today - timedelta(days=i)
        if date == expected_date:
            streak += 1
        else:
            break
    
    return streak

def calculate_achievements():
    """Calculate earned achievement badges"""
    achievements = {
        "First Steps": False,
        "Week Warrior": False,
        "Goal Setter": False,
        "Consistency King": False
    }
    
    # First exercise completed
    if 'completed_exercises' in st.session_state and st.session_state.completed_exercises:
        achievements["First Steps"] = True
    
    # 7 exercises in a week
    if 'completed_exercises' in st.session_state:
        df = pd.DataFrame(st.session_state.completed_exercises)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date']).dt.date
            last_7_days = df[df['date'] >= (datetime.now().date() - timedelta(days=7))]
            if len(last_7_days) >= 7:
                achievements["Week Warrior"] = True
    
    # Set a goal
    if 'wellness_goals' in st.session_state and st.session_state.wellness_goals:
        achievements["Goal Setter"] = True
    
    # Exercise streak of 5+ days
    if 'completed_exercises' in st.session_state and st.session_state.completed_exercises:
        df = pd.DataFrame(st.session_state.completed_exercises)
        df['date'] = pd.to_datetime(df['date']).dt.date
        dates_sorted = sorted(df['date'].unique(), reverse=True)
        streak = calculate_exercise_streak(dates_sorted)
        if streak >= 5:
            achievements["Consistency King"] = True
    
    return achievements