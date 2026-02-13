import streamlit as st
import os
import sys
import time
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
import base64
import random

# ── Safe imports with error messages ─────────────────────────────────────────
try:
    import cv2
except ImportError:
    st.error("Missing: opencv-python-headless. Add to requirements.txt")
    st.stop()

try:
    import numpy as np
except ImportError:
    st.error("Missing: numpy. Add to requirements.txt")
    st.stop()

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
except ImportError:
    st.error("Missing: cryptography. Add to requirements.txt")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG & SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="CardioSecure – Heart Rate Monitor",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = "landing"
if 'user' not in st.session_state:
    st.session_state.user = None

# Navigation helper
def go(page_name: str):
    st.session_state.page = page_name
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# BASIC STYLING (reduced & stable version)
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    :root {
        --bg: #0f172a;
        --card: #1e293b;
        --accent: #ef4444;
        --green: #22c55e;
        --text: #e2e8f0;
        --text2: #94a3b8;
    }
    .stApp {
        background: var(--bg);
        color: var(--text);
    }
    h1, h2, h3 { color: var(--accent); }
    .big-title {
        font-size: 5rem;
        text-align: center;
        margin: 3rem 0 1rem;
    }
    .subtitle {
        font-size: 1.5rem;
        color: var(--text2);
        text-align: center;
        max-width: 800px;
        margin: 0 auto 3rem;
    }
    .center { text-align: center; }
    .card {
        background: var(--card);
        border-radius: 12px;
        padding: 1.8rem;
        margin: 1.5rem 0;
        border: 1px solid #334155;
    }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def get_db_path():
    candidates = [
        os.path.join(os.getcwd(), "cardiosecure.db"),
        os.path.join(os.path.expanduser("~"), "cardiosecure.db"),
        os.path.join(tempfile.gettempdir(), "cardiosecure.db"),
    ]
    for path in candidates:
        try:
            conn = sqlite3.connect(path, timeout=5)
            conn.close()
            return path
        except:
            pass
    return ":memory:"

DB_PATH = get_db_path()

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        is_admin INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS test_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        encrypted_data BLOB,
        encryption_key BLOB,
        raw_bpm REAL,
        test_date TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    
    # Seed admin
    admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password_hash, full_name, is_admin) VALUES (?,?,?,?)",
              ("admin", admin_hash, "Admin User", 1))
    
    conn.commit()
    conn.close()

init_db()

def register_user(username, password, full_name):
    conn = get_conn()
    c = conn.cursor()
    try:
        h = hashlib.sha256(password.encode()).hexdigest()
        c.execute("INSERT INTO users (username, password_hash, full_name) VALUES (?,?,?)",
                  (username, h, full_name))
        conn.commit()
        return True, "Registered successfully"
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    finally:
        conn.close()

def login_user(username, password):
    conn = get_conn()
    c = conn.cursor()
    h = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT id, username, full_name, is_admin FROM users WHERE username=? AND password_hash=?", 
              (username, h))
    row = c.fetchone()
    conn.close()
    if row:
        return True, dict(row)
    return False, None

# ─────────────────────────────────────────────────────────────────────────────
# ENCRYPTION
# ─────────────────────────────────────────────────────────────────────────────

class HybridEncryption:
    @staticmethod
    def encrypt(data: str, key: bytes = None) -> tuple[bytes, bytes]:
        if key is None:
            key = os.urandom(32)
        nonce = os.urandom(12)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, data.encode(), None)
        return nonce + ciphertext, key

    @staticmethod
    def decrypt(enc: bytes, key: bytes) -> str:
        nonce = enc[:12]
        ct = enc[12:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ct, None).decode()

# ─────────────────────────────────────────────────────────────────────────────
# LANDING PAGE
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.page == "landing":
    st.markdown('<div class="big-title">❤️ CardioSecure</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="subtitle">
        Real-time heart rate monitoring via webcam (rPPG)<br>
        protected with AES-256-GCM hybrid encryption
    </div>
    """, unsafe_allow_html=True)

    col = st.columns((1,2,1))[1]
    with col:
        if st.button("🚀 Get Started", type="primary", use_container_width=True):
            go("login")

    st.markdown("""
    <div class="center" style="margin-top:4rem; color:#64748b;">
        Research & educational prototype — not a certified medical device
    </div>
    """, unsafe_allow_html=True)
    
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# LOGIN / REGISTER
# ─────────────────────────────────────────────────────────────────────────────

elif st.session_state.page == "login":
    st.title("Welcome to CardioSecure")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", type="primary"):
            success, user = login_user(username, password)
            if success:
                st.session_state.user = user
                go("monitor")
            else:
                st.error("Invalid username or password")

    with tab_register:
        reg_user = st.text_input("Choose username")
        reg_pass = st.text_input("Choose password", type="password")
        reg_name = st.text_input("Full name")
        if st.button("Create Account"):
            success, msg = register_user(reg_user, reg_pass, reg_name)
            if success:
                st.success(msg + " — you can now log in")
            else:
                st.error(msg)

    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# MONITOR (placeholder)
# ─────────────────────────────────────────────────────────────────────────────

elif st.session_state.page == "monitor":
    st.title("Heart Rate Monitor")
    st.info("Webcam rPPG heart rate detection would appear here")

    col1, col2, col3 = st.columns(3)
    col1.metric("Current BPM", "—")
    col2.metric("Status", "Ready")
    col3.metric("Last reading", "No data")

    if st.button("Start Measurement"):
        st.info("Measurement simulation – real implementation uses OpenCV + signal processing")

    if st.button("View Past Results"):
        go("results")

    if st.button("Encryption Lab"):
        go("enc_demo")

    if st.session_state.user and st.session_state.user["is_admin"]:
        if st.button("Admin Dashboard"):
            go("admin")

    if st.button("Logout"):
        st.session_state.user = None
        go("login")

    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# RESULTS (placeholder)
# ─────────────────────────────────────────────────────────────────────────────

elif st.session_state.page == "results":
    st.title("Your Test Results")
    st.info("Past measurements would be listed here (encrypted in DB)")
    if st.button("Back"):
        go("monitor")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# ENCRYPTION DEMO / LAB
# ─────────────────────────────────────────────────────────────────────────────

elif st.session_state.page == "enc_demo":
    st.title("Encryption Laboratory")
    st.markdown("Demonstration of AES-GCM encryption used in CardioSecure")

    message = st.text_area("Data to encrypt", "Heart rate: 76 BPM | Timestamp: 2025-02-13")
    
    if st.button("Encrypt Sample"):
        enc, key = HybridEncryption.encrypt(message)
        st.session_state["demo_enc"] = enc
        st.session_state["demo_key"] = key
        st.code("Encrypted (hex): " + enc.hex(), language="text")
        st.code("Key (hex, never share): " + key.hex(), language="text")

    if "demo_enc" in st.session_state and st.button("Decrypt"):
        try:
            dec = HybridEncryption.decrypt(st.session_state["demo_enc"], st.session_state["demo_key"])
            st.success("Decrypted correctly: " + dec)
        except Exception as e:
            st.error("Decryption failed (tampered or wrong key?)")

    if st.button("Back to Monitor"):
        go("monitor")

    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# ADMIN DASHBOARD (stub)
# ─────────────────────────────────────────────────────────────────────────────

elif st.session_state.page == "admin" and st.session_state.user and st.session_state.user.get("is_admin"):
    st.title("Admin Dashboard")
    st.warning("Admin area – user & data management would go here")
    
    if st.button("Back"):
        go("monitor")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# FALLBACK
# ─────────────────────────────────────────────────────────────────────────────

else:
    st.session_state.page = "landing"
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.caption(
    "CardioSecure • AES-256-GCM protected heart rate prototype • "
    "EBSU/PG/PhD/2021/10930 • Research use only"
)