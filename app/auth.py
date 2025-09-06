# app/auth.py
import streamlit as st
import bcrypt
from sqlite3 import Connection
from typing import Optional

def hash_pw(pw: str) -> bytes:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt())

def verify_pw(pw: str, pw_hash: bytes) -> bool:
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), pw_hash)
    except Exception:
        return False

def signup(con: Connection):
    st.subheader("Create account")
    with st.form("signup_form", clear_on_submit=False):
        username = st.text_input("Username")
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        pw2 = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Sign up", type="primary")

    if submitted:
        if not username or not email or not pw:
            st.error("Please fill all fields.")
            return
        if pw != pw2:
            st.error("Passwords do not match.")
            return
        try:
            con.execute(
                "INSERT INTO users (username,email,password_hash) VALUES (?,?,?)",
                (username, email, hash_pw(pw)),
            )
            con.commit()
            st.success("Account created. Please log in.")
        except Exception as e:
            st.error(f"Could not create account: {e}")

def login(con: Connection) -> Optional[dict]:
    st.subheader("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", type="primary")

    if submitted:
        row = con.execute(
            "SELECT id, username, email, password_hash FROM users WHERE username=?",
            (username,),
        ).fetchone()
        if row and verify_pw(pw, row[3]):
            user = {"id": row[0], "username": row[1], "email": row[2]}
            st.session_state.user = user
            st.success("Logged in")
            return user
        st.error("Invalid credentials.")
    return st.session_state.get("user")

def logout():
    st.session_state.pop("user", None)
    st.success("Logged out.")