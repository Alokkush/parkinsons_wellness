import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import pickle
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import hashlib
import io
import base64
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import warnings
import os
import json

warnings.filterwarnings('ignore')

# Configure page
st.set_page_config(
    page_title="Parkinson's Health Manager",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        color: #155724;
    }
    .warning-message {
        padding: 1rem;
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 5px;
        color: #856404;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# Database initialization with better error handling
@st.cache_resource
def init_database():
    """Initialize database with proper error handling"""
    try:
        conn = sqlite3.connect('parkinsons_app.db', check_same_thread=False)
        c = conn.cursor()
        
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT UNIQUE NOT NULL,
                      password_hash TEXT NOT NULL,
                      email TEXT,
                      created_date TEXT,
                      profile_data TEXT)''')
        
        # Symptoms table with better structure
        c.execute('''CREATE TABLE IF NOT EXISTS symptoms
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      date TEXT,
                      hand_tremors INTEGER CHECK (hand_tremors >= 1 AND hand_tremors <= 10),
                      speech_clarity INTEGER CHECK (speech_clarity >= 1 AND speech_clarity <= 10),
                      mood INTEGER CHECK (mood >= 1 AND mood <= 10),
                      stiffness INTEGER CHECK (stiffness >= 1 AND stiffness <= 10),
                      balance INTEGER CHECK (balance >= 1 AND balance <= 10),
                      fatigue INTEGER CHECK (fatigue >= 1 AND fatigue <= 10),
                      sleep_quality INTEGER CHECK (sleep_quality >= 1 AND sleep_quality <= 10),
                      notes TEXT,
                      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY (user_id) REFERENCES users (id))''')
        
        # Predictions table
        c.execute('''CREATE TABLE IF NOT EXISTS predictions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      date TEXT,
                      prediction_result REAL,
                      confidence REAL,
                      features TEXT,
                      model_version TEXT DEFAULT '1.0',
                      FOREIGN KEY (user_id) REFERENCES users (id))''')
        
        # Reminders table with better structure
        c.execute('''CREATE TABLE IF NOT EXISTS reminders
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      medicine_name TEXT NOT NULL,
                      dosage TEXT,
                      frequency TEXT,
                      time TEXT,
                      active INTEGER DEFAULT 1,
                      created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                      last_taken TEXT,
                      FOREIGN KEY (user_id) REFERENCES users (id))''')
        
        # Goals table for tracking improvement goals
        c.execute('''CREATE TABLE IF NOT EXISTS goals
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      goal_type TEXT,
                      target_value REAL,
                      current_value REAL,
                      target_date TEXT,
                      status TEXT DEFAULT 'active',
                      created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY (user_id) REFERENCES users (id))''')
        
        conn.commit()
        return conn
    except Exception as e:
        st.error(f"Database initialization error: {str(e)}")
        return None

# Enhanced authentication functions
def hash_password(password):
    """Hash password with salt"""
    salt = "parkinson_health_app_salt"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_password(password, hashed):
    """Verify password against hash"""
    return hash_password(password) == hashed

def create_user(username, password, email):
    """Create new user with validation"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    if "@" not in email:
        return False, "Please enter a valid email address"
    
    conn = sqlite3.connect('parkinsons_app.db')
    c = conn.cursor()
    try:
        profile_data = json.dumps({
            "age": None,
            "diagnosis_date": None,
            "medications": [],
            "emergency_contact": ""
        })
        
        c.execute("""INSERT INTO users (username, password_hash, email, created_date, profile_data) 
                     VALUES (?, ?, ?, ?, ?)""",
                  (username, hash_password(password), email, 
                   datetime.now().strftime("%Y-%m-%d %H:%M:%S"), profile_data))
        conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Username already exists!"
    except Exception as e:
        return False, f"Error creating account: {str(e)}"
    finally:
        conn.close()

def authenticate_user(username, password):
    """Authenticate user with better error handling"""
    try:
        conn = sqlite3.connect('parkinsons_app.db')
        c = conn.cursor()
        c.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and verify_password(password, user[1]):
            return user[0]  # Return user_id
        return None
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return None

# Enhanced symptom tracking functions
def save_symptoms(user_id, date, symptoms_data):
    """Save symptoms with validation"""
    try:
        conn = sqlite3.connect('parkinsons_app.db')
        c = conn.cursor()
        
        # Check if entry for this date already exists
        c.execute("SELECT id FROM symptoms WHERE user_id = ? AND date = ?", (user_id, date))
        existing = c.fetchone()
        
        if existing:
            # Update existing entry
            c.execute("""UPDATE symptoms SET 
                        hand_tremors=?, speech_clarity=?, mood=?, stiffness=?, 
                        balance=?, fatigue=?, sleep_quality=?, notes=?
                        WHERE user_id=? AND date=?""",
                     (symptoms_data['hand_tremors'], symptoms_data['speech_clarity'], 
                      symptoms_data['mood'], symptoms_data['stiffness'], 
                      symptoms_data['balance'], symptoms_data['fatigue'],
                      symptoms_data['sleep_quality'], symptoms_data['notes'], 
                      user_id, date))
            message = "Symptoms updated successfully!"
        else:
            # Insert new entry
            c.execute("""INSERT INTO symptoms 
                         (user_id, date, hand_tremors, speech_clarity, mood, stiffness, 
                          balance, fatigue, sleep_quality, notes)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (user_id, date, symptoms_data['hand_tremors'], symptoms_data['speech_clarity'], 
                       symptoms_data['mood'], symptoms_data['stiffness'], symptoms_data['balance'], 
                       symptoms_data['fatigue'], symptoms_data['sleep_quality'], symptoms_data['notes']))
            message = "Symptoms recorded successfully!"
        
        conn.commit()
        return True, message
    except Exception as e:
        return False, f"Error saving symptoms: {str(e)}"
    finally:
        if 'conn' in locals():
            conn.close()

def get_user_symptoms(user_id, days=30):
    """Get user symptoms with error handling"""
    try:
        conn = sqlite3.connect('parkinsons_app.db')
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        query = """SELECT * FROM symptoms WHERE user_id = ? AND date >= ? ORDER BY date DESC"""
        df = pd.read_sql_query(query, conn, params=(user_id, start_date))
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error retrieving symptoms: {str(e)}")
        return pd.DataFrame()

# Enhanced ML model functions
def create_sample_model():
    """Create enhanced sample model"""
    np.random.seed(42)
    n_samples = 2000
    
    # More realistic feature generation
    features = np.random.randn(n_samples, 22)  # Standard Parkinson's features
    
    # Create more realistic correlations
    target = np.zeros(n_samples)
    for i in range(n_samples):
        score = (features[i, 0] * 0.3 + features[i, 1] * 0.25 + 
                features[i, 2] * 0.2 + features[i, 3] * 0.15 + 
                np.random.randn() * 0.1)
        target[i] = 1 if score > 0 else 0
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=200, 
        random_state=42, 
        max_depth=12,
        min_samples_split=5,
        class_weight='balanced'
    )
    scaler = StandardScaler()
    
    features_scaled = scaler.fit_transform(features)
    model.fit(features_scaled, target)
    
    return model, scaler

@st.cache_resource
def load_or_create_model():
    """Load or create model with caching"""
    try:
        if os.path.exists('models/parkinsons_model.pkl') and os.path.exists('models/scaler.pkl'):
            with open('models/parkinsons_model.pkl', 'rb') as f:
                model = pickle.load(f)
            with open('models/scaler.pkl', 'rb') as f:
                scaler = pickle.load(f)
            return model, scaler
        else:
            st.info("Using demo model. For production, train with real data.")
            return create_sample_model()
    except Exception as e:
        st.warning(f"Model loading error: {str(e)}. Using demo model.")
        return create_sample_model()

def make_prediction(features):
    """Make prediction with confidence intervals"""
    try:
        model, scaler = load_or_create_model()
        features_scaled = scaler.transform([features])
        prediction = model.predict(features_scaled)[0]
        probabilities = model.predict_proba(features_scaled)[0]
        confidence = max(probabilities)
        
        return {
            'prediction': int(prediction),
            'confidence': float(confidence),
            'risk_score': float(probabilities[1]) if len(probabilities) > 1 else 0.0
        }
    except Exception as e:
        st.error(f"Prediction error: {str(e)}")
        return {'prediction': 0, 'confidence': 0.5, 'risk_score': 0.0}

# Enhanced reminder functions
def save_reminder(user_id, medicine_name, dosage, frequency, time):
    """Save medicine reminder with validation"""
    try:
        if not medicine_name.strip():
            return False, "Medicine name cannot be empty"
        
        conn = sqlite3.connect('parkinsons_app.db')
        c = conn.cursor()
        c.execute("""INSERT INTO reminders (user_id, medicine_name, dosage, frequency, time)
                     VALUES (?, ?, ?, ?, ?)""",
                  (user_id, medicine_name.strip(), dosage.strip(), frequency, time))
        conn.commit()
        return True, "Reminder added successfully!"
    except Exception as e:
        return False, f"Error adding reminder: {str(e)}"
    finally:
        if 'conn' in locals():
            conn.close()

def get_user_reminders(user_id):
    """Get user reminders with error handling"""
    try:
        conn = sqlite3.connect('parkinsons_app.db')
        c = conn.cursor()
        c.execute("SELECT * FROM reminders WHERE user_id = ? AND active = 1 ORDER BY time", (user_id,))
        reminders = c.fetchall()
        conn.close()
        return reminders
    except Exception as e:
        st.error(f"Error retrieving reminders: {str(e)}")
        return []

def delete_reminder(reminder_id):
    """Delete a reminder"""
    try:
        conn = sqlite3.connect('parkinsons_app.db')
        c = conn.cursor()
        c.execute("UPDATE reminders SET active = 0 WHERE id = ?", (reminder_id,))
        conn.commit()
        return True, "Reminder deleted successfully!"
    except Exception as e:
        return False, f"Error deleting reminder: {str(e)}"
    finally:
        if 'conn' in locals():
            conn.close()

# Export functions with better error handling
def create_pdf_report(user_id):
    """Create PDF report (simplified for reliability)"""
    try:
        symptoms_df = get_user_symptoms(user_id, days=90)
        
        if symptoms_df.empty:
            return None, "No data available for report generation"
        
        # Create simple text report
        report_content = f"""
PARKINSON'S HEALTH REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY (Last 90 days):
- Total Entries: {len(symptoms_df)}
- Average Hand Tremors: {symptoms_df['hand_tremors'].mean():.1f}/10
- Average Speech Clarity: {symptoms_df['speech_clarity'].mean():.1f}/10
- Average Mood: {symptoms_df['mood'].mean():.1f}/10
- Average Stiffness: {symptoms_df['stiffness'].mean():.1f}/10
- Average Balance: {symptoms_df['balance'].mean():.1f}/10

TRENDS:
- Best Day: {symptoms_df.loc[symptoms_df['mood'].idxmax(), 'date'] if not symptoms_df.empty else 'N/A'}
- Most Recent Entry: {symptoms_df['date'].max() if not symptoms_df.empty else 'N/A'}
        """
        
        return report_content, None
    except Exception as e:
        return None, f"Error generating report: {str(e)}"

def create_csv_export(user_id):
    """Create CSV export"""
    try:
        symptoms_df = get_user_symptoms(user_id, days=365)
        if symptoms_df.empty:
            return None, "No data available for export"
        
        # Clean the data
        export_df = symptoms_df.drop(['id', 'user_id', 'created_at'], axis=1, errors='ignore')
        
        # Convert to CSV
        csv_buffer = io.StringIO()
        export_df.to_csv(csv_buffer, index=False)
        
        return csv_buffer.getvalue(), None
    except Exception as e:
        return None, f"Error creating CSV export: {str(e)}"

# Enhanced exercise recommendations
def get_exercise_recommendations(user_symptoms=None):
    """Get personalized exercise recommendations"""
    base_exercises = {
        'low_intensity': [
            "Walking 15-20 minutes daily",
            "Gentle stretching and flexibility exercises",
            "Tai Chi or gentle Qigong movements",
            "Simple balance exercises at home",
            "Light resistance exercises with bands"
        ],
        'moderate_intensity': [
            "Brisk walking 30-45 minutes",
            "Swimming or water aerobics",
            "Yoga with balance challenges",
            "Dance therapy or rhythmic exercises",
            "Light weight training",
            "Voice and speech exercises"
        ],
        'high_intensity': [
            "Boxing therapy (with supervision)",
            "Interval training (supervised)",
            "Occupational therapy exercises",
            "Intensive speech therapy",
            "Progressive resistance training",
            "Cognitive-motor dual tasks"
        ]
    }
    
    if user_symptoms is None:
        return base_exercises['moderate_intensity']
    
    avg_severity = (user_symptoms.get('hand_tremors', 5) + 
                   user_symptoms.get('stiffness', 5)) / 2
    
    if avg_severity <= 3:
        return base_exercises['low_intensity']
    elif avg_severity <= 6:
        return base_exercises['moderate_intensity']
    else:
        return base_exercises['high_intensity']

def main():
    """Main application with enhanced error handling"""
    # Initialize database
    init_database()
    
    # Session state initialization
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'last_activity' not in st.session_state:
        st.session_state.last_activity = datetime.now()
    
    # Check for session timeout (24 hours)
    if st.session_state.user_id and (datetime.now() - st.session_state.last_activity).total_seconds() / 3600 > 24:
        st.session_state.user_id = None
        st.session_state.username = None
        st.warning("Session expired. Please log in again.")
    
    # Update last activity
    st.session_state.last_activity = datetime.now()
    
    # Sidebar with enhanced styling
    with st.sidebar:
        st.markdown('<h1 style="color: white;">🧠 Parkinson\'s Health Manager</h1>', unsafe_allow_html=True)
        
        if st.session_state.user_id is None:
            # Authentication section
            auth_tabs = st.tabs(["Login", "Sign Up"])
            
            with auth_tabs[0]:
                st.subheader("Login")
                with st.form("login_form"):
                    username = st.text_input("Username", placeholder="Enter your username")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    login_btn = st.form_submit_button("Login", use_container_width=True)
                    
                    if login_btn:
                        if username and password:
                            user_id = authenticate_user(username, password)
                            if user_id:
                                st.session_state.user_id = user_id
                                st.session_state.username = username
                                st.success("Successfully logged in!")
                                st.rerun()
                            else:
                                st.error("Invalid username or password!")
                        else:
                            st.error("Please fill in all fields!")
            
            with auth_tabs[1]:
                st.subheader("Sign Up")
                with st.form("signup_form"):
                    new_username = st.text_input("Username", placeholder="Choose a username")
                    new_email = st.text_input("Email", placeholder="your.email@example.com")
                    new_password = st.text_input("Password", type="password", placeholder="Minimum 6 characters")
                    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                    signup_btn = st.form_submit_button("Sign Up", use_container_width=True)
                    
                    if signup_btn:
                        if all([new_username, new_email, new_password, confirm_password]):
                            if new_password == confirm_password:
                                success, message = create_user(new_username, new_password, new_email)
                                if success:
                                    st.success(message)
                                else:
                                    st.error(message)
                            else:
                                st.error("Passwords don't match!")
                        else:
                            st.error("Please fill in all fields!")
        
        else:
            # Logged in user interface
            st.success(f"Welcome back, **{st.session_state.username}**!")
            
            if st.button("Logout", use_container_width=True):
                st.session_state.user_id = None
                st.session_state.username = None
                st.rerun()
            
            st.markdown("---")
            
            # Navigation
            pages = {
                "Dashboard": "dashboard",
                "Symptom Tracker": "tracker",
                "Health Analysis": "analysis", 
                "Medicine Reminders": "reminders",
                "Wellness Center": "wellness",
                "Reports & Export": "reports"
            }
            
            selected_page = st.selectbox(
                "Navigate to:",
                list(pages.keys()),
                index=0
            )
            # Ensure selected_page is not None
            if selected_page is None:
                selected_page = list(pages.keys())[0]
            page = pages[selected_page]
    
    # Main content area
    if st.session_state.user_id is None:
        # Landing page for non-authenticated users
        st.markdown('<h1 class="main-header">🧠 Parkinson\'s Health Manager</h1>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 2rem;">
                <h3>Your Personal Health Companion</h3>
                <p style="font-size: 1.1rem; color: #666;">
                    Track symptoms, manage medications, and monitor your health journey 
                    with our comprehensive Parkinson's management platform.
                </p>
                
                <div style="margin: 2rem 0;">
                    <h4>Key Features</h4>
                    <ul style="text-align: left; display: inline-block;">
                        <li>Daily symptom tracking with visual trends</li>
                        <li>AI-powered health analysis</li>
                        <li>Smart medication reminders</li>
                        <li>Personalized exercise recommendations</li>
                        <li>Comprehensive health reports</li>
                        <li>Secure and private data storage</li>
                    </ul>
                </div>
                
                <p style="color: #888;">
                    Please <strong>login</strong> or <strong>sign up</strong> using the sidebar to get started.
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        # Main application for authenticated users
        if page == "dashboard":
            st.title("Health Dashboard")
            
            # Get recent data
            symptoms_df = get_user_symptoms(st.session_state.user_id, days=30)
            
            if not symptoms_df.empty:
                # Metrics row
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    avg_tremors = symptoms_df['hand_tremors'].mean()
                    st.metric("Hand Tremors", f"{avg_tremors:.1f}/10", 
                             delta=f"{avg_tremors - symptoms_df['hand_tremors'].iloc[-7:].mean():.1f}" if len(symptoms_df) > 7 else None)
                
                with col2:
                    avg_mood = symptoms_df['mood'].mean()
                    st.metric("Mood Score", f"{avg_mood:.1f}/10",
                             delta=f"{avg_mood - symptoms_df['mood'].iloc[-7:].mean():.1f}" if len(symptoms_df) > 7 else None)
                
                with col3:
                    avg_balance = symptoms_df['balance'].mean()
                    st.metric("Balance", f"{avg_balance:.1f}/10",
                             delta=f"{avg_balance - symptoms_df['balance'].iloc[-7:].mean():.1f}" if len(symptoms_df) > 7 else None)
                
                with col4:
                    st.metric("Total Entries", len(symptoms_df))
                
                st.markdown("---")
                
                # Charts
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Symptom Trends (30 days)")
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=symptoms_df['date'], 
                        y=symptoms_df['hand_tremors'], 
                        mode='lines+markers', 
                        name='Hand Tremors',
                        line=dict(color='#ff6b6b')
                    ))
                    fig.add_trace(go.Scatter(
                        x=symptoms_df['date'], 
                        y=symptoms_df['mood'], 
                        mode='lines+markers', 
                        name='Mood',
                        line=dict(color='#4ecdc4')
                    ))
                    fig.add_trace(go.Scatter(
                        x=symptoms_df['date'], 
                        y=symptoms_df['balance'], 
                        mode='lines+markers', 
                        name='Balance',
                        line=dict(color='#45b7d1')
                    ))
                    
                    fig.update_layout(
                        height=400,
                        yaxis_title="Score (1-10)",
                        showlegend=True,
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("Average Scores")
                    
                    # Create radar chart
                    categories = ['Hand Tremors', 'Speech', 'Mood', 'Stiffness', 'Balance', 'Energy']
                    values = [
                        symptoms_df['hand_tremors'].mean(),
                        symptoms_df['speech_clarity'].mean(), 
                        symptoms_df['mood'].mean(),
                        10 - symptoms_df['stiffness'].mean(),  # Invert so higher is better
                        symptoms_df['balance'].mean(),
                        10 - symptoms_df['fatigue'].mean()    # Invert so higher is better
                    ]
                    
                    fig = go.Figure(data=go.Scatterpolar(
                        r=values,
                        theta=categories,
                        fill='toself',
                        name='Current Average'
                    ))
                    
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0, 10]
                            )),
                        showlegend=True,
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Recent entries
                st.subheader("Recent Entries")
                recent_entries = symptoms_df.head(5)
                
                for _, entry in recent_entries.iterrows():
                    with st.expander(f"{entry['date']} - Overall: {(entry['mood'] + entry['balance'] + (10-entry['hand_tremors']))/3:.1f}/10"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Tremors:** {entry['hand_tremors']}/10")
                            st.write(f"**Speech:** {entry['speech_clarity']}/10")
                        with col2:
                            st.write(f"**Mood:** {entry['mood']}/10")
                            st.write(f"**Balance:** {entry['balance']}/10")
                        with col3:
                            st.write(f"**Stiffness:** {entry['stiffness']}/10")
                            st.write(f"**Energy:** {10-entry['fatigue']}/10")
                        
                        if entry.get('notes'):
                            st.write(f"**Notes:** {entry['notes']}")
            
            else:
                st.info("Welcome! Start by recording your first symptom entry to see your personalized dashboard.")
                if st.button("Record Symptoms Now", type="primary"):
                    st.session_state.selected_page = "tracker"
                    st.rerun()
        
        elif page == "tracker":
            st.title("Daily Symptom Tracker")
            
            # Quick stats
            symptoms_df = get_user_symptoms(st.session_state.user_id, days=7)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info(f"**This Week:** {len(symptoms_df)} entries")
            with col2:
                if not symptoms_df.empty:
                    streak = len(symptoms_df)
                    st.success(f"**Streak:** {streak} days")
                else:
                    st.warning("**Start your tracking journey!**")
            with col3:
                today_entry = symptoms_df[symptoms_df['date'] == date.today().strftime("%Y-%m-%d")]
                if not today_entry.empty:
                    st.success("**Today's entry:** Complete")
                else:
                    st.warning("**Today's entry:** Pending")
            
            st.markdown("---")
            
            # Main tracking form
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("Record Your Symptoms")
                
                with st.form("symptom_form", clear_on_submit=True):
                    selected_date = st.date_input(
                        "Date", 
                        value=date.today(),
                        max_value=date.today()
                    )
                    
                    st.markdown("**Rate each symptom from 1-10:**")
                    
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        hand_tremors = st.slider(
                            "Hand Tremors", 1, 10, 5, 
                            help="1=None, 10=Severe"
                        )
                        speech_clarity = st.slider(
                            "Speech Clarity", 1, 10, 5,
                            help="1=Very Unclear, 10=Very Clear"
                        )
                        mood = st.slider(
                            "Mood", 1, 10, 5,
                            help="1=Very Low, 10=Excellent"
                        )
                        balance = st.slider(
                            "Balance", 1, 10, 5,
                            help="1=Very Poor, 10=Excellent"
                        )
                    
                    with col_b:
                        stiffness = st.slider(
                            "Muscle Stiffness", 1, 10, 5,
                            help="1=None, 10=Severe"
                        )
                        fatigue = st.slider(
                            "Fatigue Level", 1, 10, 5,
                            help="1=Very Energetic, 10=Exhausted"
                        )
                        sleep_quality = st.slider(
                            "Sleep Quality", 1, 10, 5,
                            help="1=Very Poor, 10=Excellent"
                        )
                    
                    notes = st.text_area(
                        "Additional Notes",
                        placeholder="Any observations, medications taken, activities, etc.",
                        height=100
                    )
                    
                    submit_btn = st.form_submit_button("Save Symptoms", type="primary", use_container_width=True)
                    
                    if submit_btn:
                        symptoms_data = {
                            'hand_tremors': hand_tremors,
                            'speech_clarity': speech_clarity,
                            'mood': mood,
                            'stiffness': stiffness,
                            'balance': balance,
                            'fatigue': fatigue,
                            'sleep_quality': sleep_quality,
                            'notes': notes
                        }
                        
                        # Ensure selected_date is a date object, not a tuple or None
                        date_value = None
                        if isinstance(selected_date, tuple):
                            if selected_date and isinstance(selected_date[0], date):
                                date_value = selected_date[0]
                        elif isinstance(selected_date, date):
                            date_value = selected_date
                        if date_value is not None:
                            formatted_date = date_value.strftime("%Y-%m-%d")
                        else:
                            formatted_date = date.today().strftime("%Y-%m-%d")

                        success, message = save_symptoms(
                            st.session_state.user_id, 
                            formatted_date, 
                            symptoms_data
                        )
                        
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
            
            with col2:
                st.subheader("Recent Entries")
                recent_symptoms = get_user_symptoms(st.session_state.user_id, days=7)
                
                if not recent_symptoms.empty:
                    for _, row in recent_symptoms.head(5).iterrows():
                        with st.expander(f"{row['date']}"):
                            st.write(f"**Tremors:** {row['hand_tremors']}/10")
                            st.write(f"**Speech:** {row['speech_clarity']}/10")
                            st.write(f"**Mood:** {row['mood']}/10")
                            st.write(f"**Balance:** {row['balance']}/10")
                            if row.get('notes'):
                                st.write(f"**Notes:** {row['notes']}")
                else:
                    st.info("No entries yet. Start tracking your symptoms!")
        
        elif page == "analysis":
            st.title("Health Analysis & Predictions")
            
            tab1, tab2 = st.tabs(["Voice Analysis", "Symptom Analysis"])
            
            with tab1:
                st.subheader("Voice/Motor Feature Analysis")
                st.info("Input voice analysis features for Parkinson's risk assessment")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Fundamental Frequency Features**")
                    mdvp_fo = st.number_input("MDVP:Fo(Hz)", 80.0, 300.0, 150.0)
                    mdvp_fhi = st.number_input("MDVP:Fhi(Hz)", 100.0, 600.0, 200.0)
                    mdvp_flo = st.number_input("MDVP:Flo(Hz)", 50.0, 200.0, 100.0)
                    
                    st.markdown("**Jitter Measures**")
                    jitter_percent = st.number_input("Jitter (%)", 0.0, 10.0, 0.5)
                    jitter_abs = st.number_input("Jitter (Abs)", 0.0, 0.001, 0.00003)
                    jitter_rap = st.number_input("RAP", 0.0, 1.0, 0.1)
                    jitter_ppq = st.number_input("PPQ", 0.0, 1.0, 0.1)
                    jitter_ddp = st.number_input("Jitter:DDP", 0.0, 1.0, 0.2)
                    
                    st.markdown("**Shimmer Measures**")
                    shimmer = st.number_input("Shimmer", 0.0, 1.0, 0.1)
                    shimmer_db = st.number_input("Shimmer(dB)", 0.0, 3.0, 0.5)
                    shimmer_apq3 = st.number_input("APQ3", 0.0, 1.0, 0.1)
                
                with col2:
                    shimmer_apq5 = st.number_input("APQ5", 0.0, 1.0, 0.1)
                    apq = st.number_input("MDVP:APQ", 0.0, 1.0, 0.1)
                    shimmer_dda = st.number_input("Shimmer:DDA", 0.0, 1.0, 0.2)
                    
                    st.markdown("**Harmonic Measures**")
                    nhr = st.number_input("NHR", 0.0, 1.0, 0.1)
                    hnr = st.number_input("HNR", 0.0, 40.0, 20.0)
                    
                    st.markdown("**Nonlinear Measures**")
                    rpde = st.number_input("RPDE", 0.0, 1.0, 0.5)
                    dfa = st.number_input("DFA", 0.0, 1.0, 0.7)
                    spread1 = st.number_input("Spread1", -10.0, 0.0, -5.0)
                    spread2 = st.number_input("Spread2", 0.0, 1.0, 0.2)
                    d2 = st.number_input("D2", 0.0, 5.0, 2.5)
                    ppe = st.number_input("PPE", 0.0, 1.0, 0.2)
                
                if st.button("Analyze Features", type="primary", use_container_width=True):
                    features = [
                        mdvp_fo, mdvp_fhi, mdvp_flo, jitter_percent, jitter_abs,
                        jitter_rap, jitter_ppq, jitter_ddp, shimmer, shimmer_db,
                        shimmer_apq3, shimmer_apq5, apq, shimmer_dda, nhr, hnr,
                        rpde, dfa, spread1, spread2, d2, ppe
                    ]
                    
                    result = make_prediction(features)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if result['prediction'] == 1:
                            st.error("Risk indicators detected")
                        else:
                            st.success("No significant risk indicators")
                    
                    with col2:
                        st.metric("Confidence", f"{result['confidence']:.1%}")
                    
                    with col3:
                        st.metric("Risk Score", f"{result['risk_score']:.1%}")
                    
                    # Save prediction to database
                    try:
                        conn = sqlite3.connect('parkinsons_app.db')
                        c = conn.cursor()
                        c.execute("""INSERT INTO predictions (user_id, date, prediction_result, confidence, features)
                                     VALUES (?, ?, ?, ?, ?)""",
                                  (st.session_state.user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                   result['prediction'], result['confidence'], str(features)))
                        conn.commit()
                        conn.close()
                    except Exception as e:
                        st.warning(f"Could not save prediction: {str(e)}")
            
            with tab2:
                st.subheader("Symptom Pattern Analysis")
                
                symptoms_df = get_user_symptoms(st.session_state.user_id, days=90)
                
                if not symptoms_df.empty:
                    # Correlation analysis
                    st.markdown("**Symptom Correlations**")
                    numeric_cols = ['hand_tremors', 'speech_clarity', 'mood', 'stiffness', 'balance', 'fatigue']
                    corr_matrix = symptoms_df[numeric_cols].corr()
                    
                    fig = px.imshow(
                        corr_matrix,
                        text_auto=True,
                        aspect="auto",
                        title="Correlation Between Symptoms",
                        color_continuous_scale="RdBu"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Trend analysis
                    st.markdown("**Symptom Trends Analysis**")
                    
                    # Calculate weekly averages
                    symptoms_df['date'] = pd.to_datetime(symptoms_df['date'])
                    symptoms_df['week'] = symptoms_df['date'].dt.isocalendar().week
                    weekly_avg = symptoms_df.groupby('week')[numeric_cols].mean().reset_index()
                    
                    fig = go.Figure()
                    for col in numeric_cols:
                        fig.add_trace(go.Scatter(
                            x=weekly_avg['week'],
                            y=weekly_avg[col],
                            mode='lines+markers',
                            name=col.replace('_', ' ').title()
                        ))
                    
                    fig.update_layout(
                        title="Weekly Average Trends",
                        xaxis_title="Week Number",
                        yaxis_title="Average Score",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Insights
                    st.markdown("**AI Insights**")
                    
                    avg_mood = symptoms_df['mood'].mean()
                    avg_tremors = symptoms_df['hand_tremors'].mean()
                    
                    insights = []
                    if avg_mood < 5:
                        insights.append("Your mood scores suggest room for improvement. Consider speaking with your healthcare provider about mood management strategies.")
                    if avg_tremors > 7:
                        insights.append("Tremor levels are consistently high. This may warrant medication adjustment discussions with your doctor.")
                    
                    mood_trend = symptoms_df['mood'].diff().mean()
                    if mood_trend > 0.1:
                        insights.append("Your mood shows a positive upward trend - keep up the good work!")
                    elif mood_trend < -0.1:
                        insights.append("Your mood shows a declining trend. Consider reviewing recent changes in routine or medication.")
                    
                    if not insights:
                        insights.append("Your symptoms appear stable. Continue with your current management plan.")
                    
                    for insight in insights:
                        st.info(insight)
                
                else:
                    st.warning("Not enough data for analysis. Track symptoms for at least a week to see patterns.")
        
        elif page == "reminders":
            st.title("Medicine Reminders")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("Add New Reminder")
                
                with st.form("reminder_form", clear_on_submit=True):
                    medicine_name = st.text_input("Medicine Name", placeholder="e.g., Carbidopa-Levodopa")
                    dosage = st.text_input("Dosage", placeholder="e.g., 25-100mg")
                    frequency = st.selectbox(
                        "Frequency", 
                        ["Once daily", "Twice daily", "Three times daily", "Four times daily", "As needed"]
                    )
                    reminder_time = st.time_input("Reminder Time", value=datetime.now().time())
                    
                    submit_reminder = st.form_submit_button("Add Reminder", type="primary", use_container_width=True)
                    
                    if submit_reminder:
                        if medicine_name.strip():
                            success, message = save_reminder(
                                st.session_state.user_id,
                                medicine_name,
                                dosage,
                                frequency,
                                reminder_time.strftime("%H:%M")
                            )
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                        else:
                            st.error("Please enter a medicine name")
            
            with col2:
                st.subheader("Active Reminders")
                reminders = get_user_reminders(st.session_state.user_id)
                
                if reminders:
                    for reminder in reminders:
                        with st.expander(f"{reminder[2]} - {reminder[5]}"):
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                st.write(f"**Dosage:** {reminder[3]}")
                                st.write(f"**Frequency:** {reminder[4]}")
                                st.write(f"**Time:** {reminder[5]}")
                            with col_b:
                                if st.button("Delete", key=f"del_{reminder[0]}", type="secondary"):
                                    success, message = delete_reminder(reminder[0])
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
                else:
                    st.info("No active reminders. Add some using the form on the left!")
            
            # Today's reminders
            st.markdown("---")
            st.subheader("Today's Schedule")
            
            if reminders:
                current_time = datetime.now().strftime("%H:%M")
                todays_reminders = []
                
                for reminder in reminders:
                    reminder_time = reminder[5]
                    status = "Upcoming" if reminder_time > current_time else "Due/Passed"
                    todays_reminders.append({
                        'time': reminder_time,
                        'medicine': reminder[2],
                        'dosage': reminder[3],
                        'status': status
                    })
                
                todays_reminders.sort(key=lambda x: x['time'])
                
                for reminder in todays_reminders:
                    col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                    with col1:
                        st.write(f"**{reminder['time']}**")
                    with col2:
                        st.write(reminder['medicine'])
                    with col3:
                        st.write(reminder['dosage'])
                    with col4:
                        if reminder['status'] == "Due/Passed":
                            st.error("Due")
                        else:
                            st.success("Upcoming")
            else:
                st.info("No reminders scheduled for today.")
        
        elif page == "wellness":
            st.title("Wellness Center")
            
            tab1, tab2, tab3 = st.tabs(["Exercise Recommendations", "Lifestyle Tips", "Goals & Progress"])
            
            with tab1:
                st.subheader("Personalized Exercise Recommendations")
                
                # Get recent symptoms for personalization
                recent_symptoms = get_user_symptoms(st.session_state.user_id, days=7)
                
                if not recent_symptoms.empty:
                    avg_symptoms = {
                        'hand_tremors': recent_symptoms['hand_tremors'].mean(),
                        'stiffness': recent_symptoms['stiffness'].mean(),
                        'balance': recent_symptoms['balance'].mean()
                    }
                    
                    severity_level = (avg_symptoms['hand_tremors'] + avg_symptoms['stiffness']) / 2
                    
                    if severity_level <= 3:
                        level_text = "Low Impact"
                        level_color = "success"
                    elif severity_level <= 6:
                        level_text = "Moderate Impact" 
                        level_color = "info"
                    else:
                        level_text = "High Support Needed"
                        level_color = "warning"
                    
                    st.markdown(f"**Recommended Level:** :{level_color}[{level_text}]")
                else:
                    avg_symptoms = None
                    st.info("Add symptom data for personalized recommendations")
                
                exercises = get_exercise_recommendations(avg_symptoms)
                
                st.markdown("**Recommended Exercises:**")
                for i, exercise in enumerate(exercises, 1):
                    st.write(f"{i}. {exercise}")
                
                # Exercise tracker
                st.markdown("---")
                st.subheader("Exercise Tracker")
                
                with st.form("exercise_form"):
                    exercise_date = st.date_input("Date", value=date.today())
                    exercise_type = st.selectbox("Exercise Type", [
                        "Walking", "Swimming", "Yoga", "Tai Chi", "Stretching",
                        "Strength Training", "Balance Exercises", "Dance", "Other"
                    ])
                    duration = st.number_input("Duration (minutes)", 1, 300, 30)
                    intensity = st.select_slider("Intensity", ["Low", "Moderate", "High"], "Moderate")
                    exercise_notes = st.text_area("Notes", placeholder="How did you feel? Any observations?")
                    
                    if st.form_submit_button("Log Exercise", type="primary"):
                        # For now, just show success - in full implementation, save to database
                        st.success(f"Logged {duration} minutes of {exercise_type}!")
            
            with tab2:
                st.subheader("Lifestyle & Wellness Tips")
                
                tips_categories = {
                    "Nutrition": [
                        "Eat a balanced diet rich in antioxidants (berries, leafy greens)",
                        "Stay hydrated - aim for 8-10 glasses of water daily",
                        "Consider Mediterranean diet patterns",
                        "Limit processed foods and excess sugar",
                        "Take medications with food if recommended by your doctor"
                    ],
                    "Sleep": [
                        "Maintain a regular sleep schedule (7-9 hours)",
                        "Create a relaxing bedtime routine",
                        "Keep your bedroom cool, dark, and quiet",
                        "Avoid screens 1 hour before bedtime",
                        "Consider a warm bath before sleep"
                    ],
                    "Stress Management": [
                        "Practice deep breathing exercises daily",
                        "Try meditation or mindfulness apps",
                        "Engage in hobbies you enjoy",
                        "Connect with support groups",
                        "Consider counseling if needed"
                    ],
                    "Social & Mental Health": [
                        "Stay connected with family and friends",
                        "Engage in cognitive activities (puzzles, reading)",
                        "Listen to music or play instruments",
                        "Join Parkinson's support groups",
                        "Maintain a positive outlook and celebrate small wins"
                    ]
                }
                
                for category, tips in tips_categories.items():
                    with st.expander(f"{category}"):
                        for tip in tips:
                            st.write(f"• {tip}")
            
            with tab3:
                st.subheader("Goals & Progress Tracking")
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("**Set a New Goal**")
                    with st.form("goal_form"):
                        goal_type = st.selectbox("Goal Type", [
                            "Improve Mood Score", "Reduce Tremors", "Better Balance",
                            "Exercise Minutes", "Sleep Quality", "Medication Adherence"
                        ])
                        target_value = st.number_input("Target Value", 1.0, 10.0, 7.0)
                        target_date = st.date_input("Target Date", value=date.today() + timedelta(days=30))
                        
                        if st.form_submit_button("Set Goal", type="primary"):
                            # In full implementation, save to goals table
                            st.success(f"Goal set: {goal_type} target of {target_value} by {target_date}")
                
                with col2:
                    st.markdown("**Progress Overview**")
                    
                    # Mock progress data - in real app, load from database
                    progress_data = [
                        {"goal": "Improve Mood", "current": 6.2, "target": 7.5, "progress": 72},
                        {"goal": "Daily Exercise", "current": 25, "target": 30, "progress": 83},
                        {"goal": "Sleep Quality", "current": 5.8, "target": 7.0, "progress": 65}
                    ]
                    
                    for goal in progress_data:
                        st.write(f"**{goal['goal']}**")
                        st.progress(goal['progress']/100)
                        st.write(f"Current: {goal['current']} | Target: {goal['target']} | {goal['progress']}%")
                        st.markdown("---")
        
        elif page == "reports":
            st.title("Reports & Export")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Generate Reports")
                
                report_period = st.selectbox("Report Period", [
                    "Last 30 days", "Last 90 days", "Last 6 months", "All time"
                ])
                
                days_map = {
                    "Last 30 days": 30,
                    "Last 90 days": 90, 
                    "Last 6 months": 180,
                    "All time": 3650
                }
                
                if st.button("Generate Text Report", type="primary", use_container_width=True):
                    report_content, error = create_pdf_report(st.session_state.user_id)
                    
                    if report_content:
                        st.download_button(
                            label="Download Text Report",
                            data=report_content,
                            file_name=f"parkinsons_report_{datetime.now().strftime('%Y%m%d')}.txt",
                            mime="text/plain"
                        )
                        st.success("Report generated successfully!")
                    else:
                        st.error(error if error else "Could not generate report")
                
                if st.button("Export Data (CSV)", use_container_width=True):
                    csv_data, error = create_csv_export(st.session_state.user_id)
                    
                    if csv_data:
                        st.download_button(
                            label="Download CSV Data",
                            data=csv_data,
                            file_name=f"parkinsons_data_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                        st.success("Data exported successfully!")
                    else:
                        st.error(error if error else "Could not export data")
            
            with col2:
                st.subheader("Data Summary")
                
                symptoms_df = get_user_symptoms(st.session_state.user_id, days=365)
                
                if not symptoms_df.empty:
                    st.metric("Total Entries", len(symptoms_df))
                    st.metric("Date Range", f"{symptoms_df['date'].min()} to {symptoms_df['date'].max()}")
                    
                    # Data completeness
                    st.markdown("**Data Completeness**")
                    numeric_cols = ['hand_tremors', 'speech_clarity', 'mood', 'stiffness', 'balance', 'fatigue']
                    
                    for col in numeric_cols:
                        if col in symptoms_df.columns:
                            completeness = (1 - symptoms_df[col].isnull().sum() / len(symptoms_df)) * 100
                            st.progress(completeness / 100, text=f"{col.replace('_', ' ').title()}: {completeness:.1f}%")
                    
                    # Quick stats
                    st.markdown("**Quick Statistics**")
                    avg_stats = symptoms_df[numeric_cols].mean()
                    
                    for col in numeric_cols:
                        if col in avg_stats:
                            st.write(f"**{col.replace('_', ' ').title()}:** {avg_stats[col]:.1f}/10")
                
                else:
                    st.info("No data available for summary yet.")
            
            # Data visualization
            st.markdown("---")
            st.subheader("Data Visualization")
            
            if not symptoms_df.empty:
                # Time series chart
                fig = go.Figure()
                
                for col in ['hand_tremors', 'mood', 'balance']:
                    if col in symptoms_df.columns:
                        fig.add_trace(go.Scatter(
                            x=symptoms_df['date'],
                            y=symptoms_df[col],
                            mode='lines+markers',
                            name=col.replace('_', ' ').title(),
                            connectgaps=True
                        ))
                
                fig.update_layout(
                    title="Symptom Trends Over Time",
                    xaxis_title="Date",
                    yaxis_title="Score (1-10)",
                    height=400,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data available for visualization.")

if __name__ == "__main__":
    main()