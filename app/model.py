# app/model.py
import os
import joblib
import pandas as pd
import shap
import matplotlib.pyplot as plt
import io
from pathlib import Path

# Paths
ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
MODEL_PATH = MODELS_DIR / "parkinsons_model.pkl"
SCALER_PATH = MODELS_DIR / "scaler.pkl"
SHAP_VALUES_PATH = MODELS_DIR / "shap_values.pkl"
SHAP_PLOT_PATH = MODELS_DIR / "shap_summary.png"

# ---------- Load Model ----------
def load_model():
    """Load trained model & scaler from disk."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Model file not found. Please run training script first.")
    model = joblib.load(MODEL_PATH)

    if SCALER_PATH.exists():
        scaler = joblib.load(SCALER_PATH)
    else:
        scaler = None

    return model, scaler

# ---------- Predict ----------
def predict_df(model, scaler, df: pd.DataFrame):
    """Run predictions on uploaded dataframe."""
    df_copy = df.copy()

    # Drop name/status if present
    X = df_copy.drop(columns=[c for c in ["name", "status"] if c in df_copy.columns], errors="ignore")

    # Scale if available
    if scaler is not None:
        X_scaled = scaler.transform(X)
    else:
        X_scaled = X.values

    y_pred = model.predict(X_scaled)
    y_prob = None
    try:
        y_prob = model.predict_proba(X_scaled)[:, 1]
    except Exception:
        pass

    df_copy["Prediction"] = y_pred
    if y_prob is not None:
        df_copy["Probability"] = y_prob

    return df_copy

# ---------- SHAP: Global ----------
def load_shap():
    """Load SHAP values if available."""
    if SHAP_VALUES_PATH.exists():
        cols, shap_values = joblib.load(SHAP_VALUES_PATH)
        return cols, shap_values
    return None, None

def shap_summary_plot():
    """Return SHAP summary plot as PNG bytes (if available)."""
    if SHAP_PLOT_PATH.exists():
        with open(SHAP_PLOT_PATH, "rb") as f:
            return f.read()
    return None

# ---------- SHAP: Patient-Specific ----------
def shap_force_plot_for_row(model, scaler, X_df, row_idx: int):
    """
    Generate a SHAP waterfall plot explanation for a single row.
    Returns a matplotlib figure.
    """
    # Scale input
    if scaler is not None:
        X_scaled = scaler.transform(X_df)
    else:
        X_scaled = X_df.values

    # SHAP Explainer
    explainer = shap.Explainer(model, X_scaled)
    shap_values = explainer(X_scaled)

    # Select one row
    shap_row = shap_values[row_idx]

    fig, ax = plt.subplots(figsize=(10, 3))
    shap.plots.waterfall(shap_row, max_display=10, show=False)
    plt.tight_layout()
    return fig