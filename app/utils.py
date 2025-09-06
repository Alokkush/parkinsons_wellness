# app/utils.py
from pathlib import Path
import streamlit as st
import pandas as pd
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
DATA_DIR = ROOT / "data"

def toast(msg, kind="info"):
    if kind == "success": st.toast(msg, icon="✅")
    elif kind == "error": st.toast(msg, icon="❌")
    elif kind == "warning": st.toast(msg, icon="⚠️")
    else: st.toast(msg, icon="ℹ️")

@st.cache_data(show_spinner=False)
def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)

def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")