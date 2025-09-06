# app/analysis.py
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from .utils import DATA_DIR, load_csv

def uci_explorer():
    st.subheader("UCI Dataset Explorer")
    parkinson_path = DATA_DIR / "parkinsons.csv"
    telemon_path = DATA_DIR / "parkinsons_updrs.csv"

    tabs = st.tabs(["Classification dataset", "Telemonitoring dataset"])
    with tabs[0]:
        if parkinson_path.exists():
            df = load_csv(parkinson_path)
            st.write(df.head())
            numeric_cols = [c for c in df.columns if c not in ["name", "status"]]
            if numeric_cols:
                c1, c2 = st.columns(2)
                with c1:
                    feat = st.selectbox("Feature", numeric_cols)
                with c2:
                    color_options = ["status"] + numeric_cols[:4]
                    color = st.selectbox("Color by", color_options)
                fig = px.histogram(df, x=feat, color=color, nbins=40, barmode="overlay", opacity=0.7)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Place parkinsons.csv in /data to explore.")

    with tabs[1]:
        if telemon_path.exists():
            df2 = load_csv(telemon_path)
            st.write(df2.head())
            if {"subject#", "motor_UPDRS", "total_UPDRS"}.issubset(df2.columns):
                pid = st.selectbox("Patient", sorted(df2["subject#"].unique().tolist()))
                p = df2[df2["subject#"] == pid]
                st.plotly_chart(px.line(p, y="motor_UPDRS", title=f"Motor UPDRS - subject {pid}"), use_container_width=True)
                st.plotly_chart(px.line(p, y="total_UPDRS", title=f"Total UPDRS - subject {pid}"), use_container_width=True)
        else:
            st.info("Place parkinsons_updrs.csv in /data to explore.")