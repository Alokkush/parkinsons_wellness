# app/utils/css_utils.py
"""
Fixed CSS Utilities for the Parkinson's AI Wellness Hub
Handles CSS loading, theme management, and style utilities
"""

import os
import streamlit as st
from typing import Dict, Optional, Union, List
from pathlib import Path


class CSSManager:
    """Manages CSS files and themes for the application"""
    
    def __init__(self, styles_dir: str = "styles"):
        self.styles_dir = styles_dir
        self.base_path = Path(__file__).parent.parent / styles_dir
        self.themes = {
            "default": "wellness_hub_styles.css",
            "dark": "dark_theme.css",
            "high_contrast": "high_contrast.css",
            "minimal": "minimal_theme.css"
        }
        self.current_theme = "default"
        
    def get_comprehensive_css(self) -> str:
        """Return comprehensive CSS that works with Streamlit"""
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@300;400;500;600;700&display=swap');
            
            :root {
                --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                --warning-gradient: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
                --glass-bg: rgba(255, 255, 255, 0.25);
                --glass-border: rgba(255, 255, 255, 0.18);
                --shadow-medium: 0 8px 32px rgba(31, 38, 135, 0.37);
                --shadow-light: 0 4px 15px rgba(0, 0, 0, 0.1);
                --border-radius: 15px;
                --border-radius-large: 25px;
                --spacing-lg: 1.5rem;
                --spacing-xl: 2rem;
                --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                --font-display: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
                --transition-smooth: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }
            
            .stApp {
                font-family: var(--font-primary) !important;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
            }
            
            .main .block-container {
                padding: var(--spacing-xl) var(--spacing-lg) !important;
                max-width: 100% !important;
            }
            
            /* Sidebar styling */
            section[data-testid="stSidebar"] {
                background: var(--glass-bg) !important;
                backdrop-filter: blur(10px) !important;
                border-right: 1px solid var(--glass-border) !important;
            }
            
            section[data-testid="stSidebar"] > div {
                background: transparent !important;
            }
            
            /* Button styling */
            .stButton > button {
                border-radius: var(--border-radius-large) !important;
                border: none !important;
                padding: 0.75rem 2rem !important;
                font-weight: 600 !important;
                font-size: 16px !important;
                transition: var(--transition-smooth) !important;
                background: var(--primary-gradient) !important;
                color: white !important;
                box-shadow: var(--shadow-light) !important;
                font-family: var(--font-primary) !important;
            }
            
            .stButton > button:hover {
                transform: translateY(-3px) scale(1.05) !important;
                box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4) !important;
            }
            
            /* Metric containers */
            [data-testid="metric-container"] {
                background: var(--glass-bg) !important;
                border: 1px solid var(--glass-border) !important;
                padding: 1rem !important;
                border-radius: var(--border-radius) !important;
                box-shadow: var(--shadow-light) !important;
                backdrop-filter: blur(10px) !important;
                transition: var(--transition-smooth) !important;
            }
            
            [data-testid="metric-container"]:hover {
                transform: translateY(-5px);
                box-shadow: var(--shadow-medium) !important;
            }
            
            [data-testid="metric-container"] [data-testid="metric-value"] {
                font-size: 2.5rem !important;
                font-weight: 700 !important;
                background: var(--primary-gradient) !important;
                -webkit-background-clip: text !important;
                -webkit-text-fill-color: transparent !important;
                background-clip: text !important;
            }
            
            /* Text inputs */
            .stTextInput > div > div > input {
                border-radius: 8px !important;
                border: 2px solid var(--glass-border) !important;
                background: var(--glass-bg) !important;
                backdrop-filter: blur(10px) !important;
                transition: var(--transition-smooth) !important;
            }
            
            .stTextInput > div > div > input:focus {
                border-color: #667eea !important;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
                transform: translateY(-1px);
            }
            
            /* Alerts */
            .stAlert {
                border-radius: var(--border-radius) !important;
                backdrop-filter: blur(10px) !important;
                border: none !important;
            }
            
            [data-testid="stSuccess"] {
                background: rgba(79, 172, 254, 0.1) !important;
                border-left: 4px solid #4facfe !important;
            }
            
            [data-testid="stError"] {
                background: rgba(245, 87, 108, 0.1) !important;
                border-left: 4px solid #f5576c !important;
            }
            
            [data-testid="stWarning"] {
                background: rgba(255, 234, 167, 0.3) !important;
                border-left: 4px solid #ffeaa7 !important;
            }
            
            [data-testid="stInfo"] {
                background: rgba(102, 126, 234, 0.1) !important;
                border-left: 4px solid #667eea !important;
            }
            
            /* Custom scrollbar */
            ::-webkit-scrollbar {
                width: 8px;
            }
            
            ::-webkit-scrollbar-track {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb {
                background: var(--primary-gradient);
                border-radius: 4px;
            }
            
            /* Responsive */
            @media (max-width: 768px) {
                .main .block-container {
                    padding: 1rem !important;
                }
            }
        </style>
        """
    
    def get_dark_theme_css(self) -> str:
        """Return dark theme CSS"""
        return """
        <style>
            :root {
                --primary-gradient: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
                --secondary-gradient: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
                --success-gradient: linear-gradient(135deg, #10b981 0%, #06b6d4 100%);
                --glass-bg: rgba(31, 41, 55, 0.8);
                --glass-border: rgba(255, 255, 255, 0.1);
                --bg-primary: #0f172a;
                --text-primary: #f8fafc;
                --text-secondary: #cbd5e1;
            }
            
            .stApp {
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%) !important;
                color: var(--text-primary) !important;
            }
            
            /* Dark theme specific overrides */
            h1, h2, h3, h4, h5, h6, p, span, div {
                color: var(--text-primary) !important;
            }
            
            section[data-testid="stSidebar"] {
                background: var(--glass-bg) !important;
            }
            
            [data-testid="metric-container"] {
                background: var(--glass-bg) !important;
                border: 1px solid var(--glass-border) !important;
            }
            
            .stTextInput > div > div > input {
                background: rgba(51, 65, 85, 0.8) !important;
                color: var(--text-primary) !important;
                border: 2px solid var(--glass-border) !important;
            }
        </style>
        """
    
    def apply_css(self, css_content: str) -> None:
        """Apply CSS to the Streamlit app"""
        if css_content and css_content.strip():
            st.markdown(css_content, unsafe_allow_html=True)
        else:
            st.error("No CSS content to apply")
    
    def load_theme(self, theme_name: str = "default") -> str:
        """Load a specific theme"""
        if theme_name == "dark":
            return self.get_dark_theme_css()
        else:
            return self.get_comprehensive_css()
    
    def get_theme_selector(self) -> str:
        """Create a theme selector widget"""
        theme_options = {
            "🎨 Default Light": "default",
            "🌙 Dark Mode": "dark",
            "🔍 High Contrast": "high_contrast",
            "⚪ Minimal": "minimal"
        }
        
        if "selected_theme" not in st.session_state:
            st.session_state.selected_theme = "default"
        
        selected_display = st.selectbox(
            "Choose Theme",
            list(theme_options.keys()),
            index=0,
            key="theme_selector"
        )
        
        selected_theme = theme_options[selected_display]
        
        if selected_theme != st.session_state.selected_theme:
            st.session_state.selected_theme = selected_theme
            css_content = self.load_theme(selected_theme)
            self.apply_css(css_content)
        
        return selected_theme

# Convenience functions
def apply_theme(theme_name: str = "default") -> None:
    """Apply a theme to the current Streamlit app"""
    css_manager = CSSManager()
    css_content = css_manager.load_theme(theme_name)
    css_manager.apply_css(css_content)

def load_and_apply_css(theme: str = "default") -> None:
    """Load and apply CSS with session state management"""
    css_manager = CSSManager()
    
    if "current_theme" not in st.session_state:
        st.session_state.current_theme = theme
    
    css_content = css_manager.load_theme(st.session_state.current_theme)
    css_manager.apply_css(css_content)

# Helper functions for creating components that work properly
def create_styled_card(content: str, card_type: str = "info") -> str:
    """Create a styled card that renders properly in Streamlit"""
    card_styles = {
        "info": {
            "background": "rgba(102, 126, 234, 0.1)",
            "border": "4px solid #667eea",
            "color": "#2d3436"
        },
        "success": {
            "background": "rgba(79, 172, 254, 0.1)", 
            "border": "4px solid #4facfe",
            "color": "#2d3436"
        },
        "warning": {
            "background": "rgba(255, 234, 167, 0.3)",
            "border": "4px solid #ffeaa7",
            "color": "#2d3436"
        },
        "error": {
            "background": "rgba(245, 87, 108, 0.1)",
            "border": "4px solid #f5576c", 
            "color": "#2d3436"
        }
    }
    
    style = card_styles.get(card_type, card_styles["info"])
    
    return f"""
    <div style="
        background: {style['background']};
        border-left: {style['border']};
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        color: {style['color']};
        font-family: 'Inter', sans-serif;
        line-height: 1.6;
    ">
        {content}
    </div>
    """