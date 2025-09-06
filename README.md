# 🧠 Parkinson's AI Wellness Hub

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3+-orange.svg)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An advanced AI-powered wellness tracking application designed specifically for Parkinson's disease patients. This comprehensive platform combines machine learning predictions, symptom tracking, smart medication reminders, and personalized wellness insights to empower patients in managing their health journey.

## 🌟 Key Features

### 🤖 AI-Powered Health Prediction
- **Single Person Manual Input**: Interactive form for individual voice analysis
- **Batch CSV Processing**: Upload and analyze multiple patient records
- **Real-time Risk Assessment**: Advanced ML models for Parkinson's detection
- **SHAP Explanations**: Transparent AI decision-making with feature importance
- **Preset Configurations**: Quick-load healthy, mild, and severe symptom profiles

### 📊 Smart Symptom Tracking
- **Multi-dimensional Monitoring**: Track tremor, rigidity, bradykinesia, speech, and mood
- **Visual Analytics**: Interactive charts and trend analysis
- **Historical Data**: Long-term symptom progression tracking
- **Export Capabilities**: PDF and Excel report generation

### 💊 Intelligent Medication Reminders
- **Smart Scheduling**: Flexible reminder system
- **Medication Tracking**: Monitor adherence and effectiveness
- **Customizable Alerts**: Personalized notification preferences

### 🏃‍♂️ Wellness Center
- **Exercise Programs**: Tailored fitness routines for Parkinson's patients
- **Voice Therapy**: LSVT LOUD protocol guidance
- **Nutrition Guidance**: Diet recommendations and meal planning
- **Progress Monitoring**: Track wellness improvements over time

### 📈 Advanced Analytics
- **Data Visualization**: Interactive Plotly charts and dashboards
- **Trend Analysis**: Identify patterns in symptom progression
- **Predictive Insights**: ML-powered health forecasting
- **Comparative Analysis**: Benchmark against population data

## 🏗️ Project Architecture

```
parkinsons_wellness/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Main Streamlit application
│   ├── auth.py                 # User authentication system
│   ├── db.py                   # Database connection and setup
│   ├── tracker.py              # Symptom tracking functionality
│   ├── reminders.py            # Medication reminder system
│   ├── analysis.py             # Data analysis and visualization
│   ├── wellness.py             # Wellness center features
│   ├── model.py                # ML model loading and prediction
│   ├── reports.py              # PDF/Excel report generation
│   └── utils.py                # Utility functions and helpers
├── scripts/
│   └── model_training.py       # ML model training pipeline
├── data/
│   └── parkinsons.csv          # UCI Parkinson's dataset
├── models/
│   ├── parkinsons_model.pkl    # Trained ML model
│   └── scaler.pkl              # Feature scaler
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
└── .gitignore                  # Git ignore rules
```

## 🛠️ Technology Stack

### Backend & ML
- **Python 3.8+**: Core programming language
- **scikit-learn**: Machine learning framework
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **SQLite**: Lightweight database for user data
- **SHAP**: Model explainability and interpretability

### Frontend & UI
- **Streamlit**: Web application framework
- **Plotly**: Interactive data visualizations
- **Plotly Express**: Simplified plotting interface
- **Custom CSS**: Enhanced UI styling and theming

### Data Processing & Reports
- **ReportLab**: PDF report generation
- **openpyxl**: Excel file creation and manipulation
- **Pillow**: Image processing capabilities
- **io/BytesIO**: In-memory file handling

## 📋 Installation Guide

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)

### Step-by-Step Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/parkinsons_wellness.git
   cd parkinsons_wellness
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Database**
   ```bash
   python -c "from app.db import get_connection; get_connection()"
   ```

5. **Train ML Model** (Optional - pre-trained model included)
   ```bash
   python scripts/model_training.py
   ```

6. **Launch Application**
   ```bash
   streamlit run app/main.py
   ```

7. **Access Application**
   Open your browser and navigate to `http://localhost:8501`

## 🚀 Usage Workflow

### 1. User Registration & Authentication
```python
# Navigate to Account tab
# Create new account or login with existing credentials
# Secure session management with user isolation
```

### 2. AI Health Prediction
```python
# Choose input method: Manual Entry or CSV Upload
# For manual entry:
#   - Select feature groups (Jitter, Shimmer, etc.)
#   - Use preset profiles or custom values
#   - Submit for AI analysis
# Get comprehensive results with risk assessment
```

### 3. Symptom Tracking
```python
# Daily symptom logging
# Rate severity on 1-5 scale
# Add contextual notes
# View historical trends and patterns
```

### 4. Medication Management
```python
# Set up medication reminders
# Track adherence patterns
# Monitor effectiveness over time
```

### 5. Wellness Activities
```python
# Access exercise programs
# Follow voice therapy protocols
# Track progress and improvements
```

### 6. Data Analysis & Reports
```python
# Generate comprehensive health reports
# Export data in PDF or Excel format
# Analyze long-term trends
```

## 🧪 Development Workflow

### Project Creation Process

1. **Research & Planning**
   - Studied Parkinson's disease symptoms and progression
   - Analyzed UCI Parkinson's voice dataset
   - Designed user-centric application architecture

2. **Database Design**
   ```sql
   -- User management with secure authentication
   -- Symptom tracking with temporal data
   -- Prediction storage with JSON metadata
   -- Reminder system with flexible scheduling
   ```

3. **ML Pipeline Development**
   ```python
   # Data preprocessing and feature engineering
   # Model selection and hyperparameter tuning
   # SHAP integration for explainability
   # Model serialization and deployment
   ```

4. **Frontend Development**
   ```python
   # Streamlit application with custom CSS
   # Interactive forms and data input
   # Real-time visualizations with Plotly
   # Responsive design for all screen sizes
   ```

5. **Feature Integration**
   ```python
   # Modular component architecture
   # User session management
   # Data validation and error handling
   # Export and reporting capabilities
   ```

### Code Quality Standards

- **Type Hints**: Comprehensive type annotations
- **Error Handling**: Robust exception management
- **Documentation**: Inline comments and docstrings
- **Security**: Input validation and SQL injection prevention
- **Performance**: Efficient data processing and caching

## 📊 Machine Learning Model

### Dataset
- **Source**: UCI Machine Learning Repository
- **Features**: 22 voice biomarkers (jitter, shimmer, HNR, etc.)
- **Target**: Binary classification (Parkinson's vs. Healthy)
- **Samples**: 195 voice recordings from 31 subjects

### Model Architecture
```python
# Feature preprocessing with StandardScaler
# Random Forest Classifier with optimized hyperparameters
# Cross-validation for robust performance estimation
# SHAP values for feature importance and explainability
```

### Performance Metrics
- **Accuracy**: 85-90% (varies with cross-validation)
- **Precision**: High precision to minimize false positives
- **Recall**: Balanced sensitivity for early detection
- **F1-Score**: Optimized for medical diagnosis context

## 🎨 UI/UX Design Philosophy

### Modern Glassmorphism Theme
```css
/* Custom gradient backgrounds */
/* Frosted glass effect cards */
/* Smooth animations and transitions */
/* Accessible color schemes */
```

### Responsive Design
- Mobile-first approach
- Tablet and desktop optimization
- Touch-friendly interface elements
- High contrast accessibility support

### User Experience Features
- **Intuitive Navigation**: Clear menu structure
- **Visual Feedback**: Loading states and success messages
- **Error Prevention**: Input validation and helpful hints
- **Progressive Disclosure**: Complex features revealed gradually

## 🔒 Security & Privacy

### Data Protection
- **Local Storage**: SQLite database with user isolation
- **Session Management**: Secure authentication tokens
- **Input Validation**: Prevent SQL injection and XSS
- **Privacy by Design**: Minimal data collection principles

### Medical Compliance Considerations
- **Disclaimer**: Clear medical advice limitations
- **Data Ownership**: Users control their health data
- **Export Rights**: Full data portability
- **Audit Trail**: Prediction history and timestamps

## 🧪 Testing & Quality Assurance

### Testing Strategy
```python
# Unit tests for core functionality
# Integration tests for database operations
# UI testing with Streamlit's testing framework
# Performance testing with large datasets
```

### Quality Metrics
- **Code Coverage**: Comprehensive test coverage
- **Performance**: Sub-second response times
- **Accessibility**: WCAG 2.1 compliance
- **Cross-browser**: Chrome, Firefox, Safari support

## 📈 Future Enhancements

### Planned Features
- **Mobile Application**: React Native companion app
- **IoT Integration**: Wearable device data collection
- **Telemedicine**: Video consultation booking
- **Community Features**: Patient support forums
- **Advanced ML**: Deep learning models for voice analysis

### Scalability Improvements
- **Cloud Deployment**: AWS/Azure hosting
- **Database Migration**: PostgreSQL for production
- **API Development**: RESTful API for third-party integration
- **Microservices**: Container-based architecture

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes and test thoroughly
4. Submit pull request with detailed description

### Contribution Guidelines
- Follow PEP 8 Python style guide
- Add tests for new functionality
- Update documentation as needed
- Ensure compatibility with existing features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Medical Disclaimer

This application is for educational and informational purposes only. It is not intended to diagnose, treat, cure, or prevent any disease. Always consult with qualified healthcare professionals for medical advice. The AI predictions should not replace professional medical evaluation.

## 📞 Support & Contact

- **Issues**: GitHub Issues page
- **Documentation**: Wiki section
- **Email**: support@parkinsonswellness.com
- **Website**: https://parkinsonswellness.com

## 🙏 Acknowledgments

- UCI Machine Learning Repository for the Parkinson's dataset
- Streamlit community for excellent documentation
- scikit-learn developers for robust ML tools
- SHAP team for model interpretability framework
- Parkinson's disease research community for domain expertise

---

**Built with ❤️ for the Parkinson's disease community**

*Empowering patients through AI-driven health insights*