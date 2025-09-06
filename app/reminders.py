# app/reminders.py
import streamlit as st
import pandas as pd
from sqlite3 import Connection

def list_reminders(con: Connection, user_id: int):
    st.subheader("Medication Reminders")
    rows = con.execute(
        "SELECT id, title, dosage, schedule_time, schedule_days, is_active FROM reminders WHERE user_id=? ORDER BY id DESC",
        (user_id,),
    ).fetchall()
    df = pd.DataFrame(rows, columns=["id", "title", "dosage", "time", "days", "active"])
    if df.empty:
        st.info("No reminders yet.")
    else:
        st.dataframe(df.drop(columns=["id"]), use_container_width=True)
        for rid, title, *_ in rows:
            cols = st.columns([6, 2, 2])
            with cols[1]:
                if st.button(f"Toggle {rid}", key=f"toggle_{rid}"):
                    con.execute("UPDATE reminders SET is_active = 1 - is_active WHERE id=?", (rid,))
                    con.commit()
                    st.rerun()
            with cols[2]:
                if st.button(f"Delete {rid}", key=f"del_{rid}", type="secondary"):
                    con.execute("DELETE FROM reminders WHERE id=?", (rid,))
                    con.commit()
                    st.rerun()

def add_reminder(con: Connection, user_id: int):
    st.subheader("Add Reminder")
    with st.form("rem_form"):
        title = st.text_input("Medicine / Title")
        dosage = st.text_input("Dosage (e.g., 1 tablet)")
        schedule_time = st.time_input("Time")
        schedule_days = st.multiselect(
            "Days", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], default=["Mon", "Wed", "Fri"]
        )
        submitted = st.form_submit_button("Save", type="primary")
    if submitted:
        con.execute(
            "INSERT INTO reminders (user_id, title, dosage, schedule_time, schedule_days) VALUES (?,?,?,?,?)",
            (user_id, title, dosage, schedule_time.strftime("%H:%M"), ",".join(schedule_days)),
        )
        con.commit()
        st.success("Saved.")