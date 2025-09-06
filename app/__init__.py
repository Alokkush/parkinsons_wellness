"""
Parkinson's Prediction & Wellness App
-------------------------------------
This package contains all modules for the Streamlit application:
- Authentication (auth.py)
- Database connection (db.py)
- Prediction & ML models (model.py)
- Symptom tracking (tracker.py)
- Reminders (reminders.py)
- Data analysis & explorer (analysis.py)
- Wellness features (wellness.py)
- Reports export (reports.py)
- Utility functions (utils.py)
"""

__app_name__ = "Parkinson's Prediction & Wellness"
__version__ = "1.0.0"
__author__ = "Akanksha"

def get_app_info():
    return {
        "name": __app_name__,
        "version": __version__,
        "author": __author__,
    }