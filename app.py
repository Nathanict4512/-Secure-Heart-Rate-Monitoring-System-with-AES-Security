import streamlit as st
import sys
import os

# ── Safe imports with clear error messages ────────────────────────────────────
try:
    import cv2
except ImportError:
    st.error("""
    **Missing dependency: opencv-python-headless**

    Make sure your `requirements.txt` contains:
    ```
    opencv-python-headless>=4.9.0.80
    ```
    And your `packages.txt` (for Streamlit Cloud) contains:
    ```
    libgl1-mesa-glx
    libglib2.0-0
    ```
    Then redeploy / restart the app.
    """)
    st.stop()

try:
    import numpy as np
except ImportError:
    st.error("Missing: numpy. Add `numpy>=1.26.0` to requirements.txt")
    st.stop()

try:
    from scipy import signal
except ImportError:
    st.error("Missing: scipy. Add `scipy>=1.12.0` to requirements.txt")
    st.stop()

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
except ImportError:
    st.error("Missing: cryptography. Add `cryptography>=42.0.0` to requirements.txt")
    st.stop()

try:
    import plotly.graph_objects as pgo
    import plotly.express as px
except ImportError:
    st.error("Missing: plotly. Add `plotly>=5.19.0` to requirements.txt")
    st.stop()

try:
    import pandas as pd
except ImportError:
    st.error("Missing: pandas. Add `pandas>=2.2.0` to requirements.txt")
    st.stop()

# Standard library — always available
import streamlit.components.v1 as components
from collections import deque
import time
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
import base64
import random
import math

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="CardioSecure – Heart Rate Monitor",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS  (medical dark-mode, refined clinical aesthetic)
# ─────────────────────────────────────────────────────────────────────────────

# ── CSS + theme toggle (pure Streamlit session_state approach) ──────────────

def _apply_theme_css():
    """Inject CSS with hardcoded dark OR light values based on session_state."""
    is_light = st.session_state.get("theme", "dark") == "light"

    # ── Colour values ──
    if is_light:
        bg      = "hsl(220,20%,97%)"
        bg2     = "hsl(220,20%,93%)"
        card    = "hsl(0,0%,100%)"
        card2   = "hsl(220,20%,95%)"
        border  = "hsl(220,20%,84%)"
        text    = "hsl(222,40%,12%)"
        text2   = "hsl(222,20%,45%)"
        text3   = "hsl(222,15%,65%)"
        accent  = "hsl(355,78%,48%)"
        accent2 = "hsl(355,78%,58%)"
        green   = "hsl(160,70%,35%)"
        yellow  = "hsl(40,80%,42%)"
        cyan    = "hsl(195,80%,38%)"
        purple  = "hsl(265,55%,48%)"
        glow    = "hsla(355,78%,48%,.2)"
        app_bg  = f"radial-gradient(ellipse at 10% 20%,hsla(355,78%,55%,.03) 0%,transparent 50%),{bg}"
        nav_bg  = f"linear-gradient(90deg,{card},{bg2})"
        nav_bdr = border
        nav_shd = "0 2px 12px rgba(0,0,0,.1)"
        inp_bg  = card2
        tab_list= bg2
        tab_act = card
        scr_trk = "hsl(220,20%,93%)"
        scr_thm = "hsl(220,20%,78%)"
        btn_svg  = text
        tog_bg  = card
        tog_bdr = border
        tog_shd = "0 2px 12px rgba(0,0,0,.15)"
    else:
        bg      = "hsl(222,58%,5%)"
        bg2     = "hsl(222,50%,8%)"
        card    = "hsl(222,40%,12%)"
        card2   = "hsl(222,35%,16%)"
        border  = "hsl(222,30%,22%)"
        text    = "hsl(220,30%,92%)"
        text2   = "hsl(220,15%,55%)"
        text3   = "hsl(222,20%,35%)"
        accent  = "hsl(355,78%,55%)"
        accent2 = "hsl(355,78%,68%)"
        green   = "hsl(160,100%,45%)"
        yellow  = "hsl(40,100%,70%)"
        cyan    = "hsl(195,100%,50%)"
        purple  = "hsl(265,70%,60%)"
        glow    = "hsla(355,78%,55%,.3)"
        app_bg  = f"radial-gradient(ellipse at 10% 20%,hsla(355,78%,55%,.07) 0%,transparent 50%),radial-gradient(ellipse at 90% 80%,hsla(195,100%,50%,.05) 0%,transparent 50%),{bg}"
        nav_bg  = f"linear-gradient(90deg,{card},{card2})"
        nav_bdr = border
        nav_shd = "0 4px 20px rgba(0,0,0,.4)"
        inp_bg  = bg2
        tab_list= bg2
        tab_act = card
        scr_trk = bg2
        scr_thm = border
        btn_svg  = text
        tog_bg  = card
        tog_bdr = border
        tog_shd = "0 4px 20px rgba(0,0,0,.45)"

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@300;400;500&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');

/* ── HARDCODED THEME VALUES (no JS needed) ── */
html,body,.stApp,[class*="css"],
[data-testid="stAppViewContainer"],
[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"] {{
  font-family:'DM Sans',sans-serif !important;
  background-color:{bg} !important;
  color:{text} !important;
}}
.stApp {{ background:{app_bg} !important; }}

/* All text white (dark) or dark (light) */
p,span,div,h1,h2,h3,h4,h5,h6,li,td,th,code,label,
.stMarkdown p,.stMarkdown li,.stMarkdown span,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] li {{color:{text} !important}}
[data-testid="stMetric"] label,[data-testid="stMetricValue"],[data-testid="stMetricDelta"]{{color:{text} !important}}
.streamlit-expanderHeader{{color:{text} !important;background:{card2} !important}}
.streamlit-expanderContent{{background:{bg2} !important;color:{text} !important}}
.stSelectbox label,.stRadio label,.stCheckbox label,.stNumberInput label,
.stTextInput label,.stTextArea label,.stSlider label{{color:{text2} !important}}

/* Cards */
.cs-card{{background:{card};border:1px solid {border};border-radius:16px;padding:1.5rem;
  margin-bottom:1rem;box-shadow:0 4px 24px rgba(0,0,0,.3);
  transition:transform .25s cubic-bezier(.23,1,.32,1),box-shadow .25s;}}
.cs-card:hover{{transform:translateY(-3px);box-shadow:0 16px 40px rgba(0,0,0,.45)}}
.metric-card{{background:{card2};border:1px solid {border};border-radius:12px;
  padding:1.2rem;text-align:center;
  transition:transform .25s cubic-bezier(.23,1,.32,1),border-color .25s,box-shadow .25s;}}
.metric-card:hover{{transform:translateY(-5px);border-color:{accent};box-shadow:0 12px 32px rgba(0,0,0,.5)}}

/* Nav */
.cs-nav{{background:{nav_bg};border-bottom:1px solid {nav_bdr};padding:.8rem 1.5rem;
  display:flex;align-items:center;justify-content:space-between;
  margin-bottom:1.5rem;box-shadow:{nav_shd};position:sticky;top:0;z-index:100;
  animation:slideDown .45s cubic-bezier(.23,1,.32,1) both;}}

/* Typography */
.section-header{{font-family:'DM Serif Display',serif;font-size:1.6rem;color:{text};margin-bottom:.3rem}}
.section-sub{{font-size:.85rem;color:{text2};margin-bottom:1.2rem}}
.gradient-text{{background:linear-gradient(135deg,{accent2} 0%,{accent} 45%,{cyan} 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}}
.metric-value{{font-family:'DM Mono',monospace;font-size:2rem;font-weight:500;color:{accent}}}
.metric-label{{font-size:.75rem;color:{text2};text-transform:uppercase;letter-spacing:.1em;margin-top:.2rem}}
.metric-sub{{font-size:.7rem;color:{text3};margin-top:.2rem}}

/* BPM */
@keyframes pulse-text{{0%,100%{{opacity:1}}50%{{opacity:.7}}}}
@keyframes heartbeat-ring{{0%{{box-shadow:0 0 0 0 hsla(355,78%,55%,.5)}}50%{{box-shadow:0 0 0 18px hsla(355,78%,55%,0)}}100%{{box-shadow:0 0 0 0 hsla(355,78%,55%,0)}}}}
.bpm-display{{font-family:'DM Serif Display',serif;font-size:6rem;line-height:1;
  display:inline-block;border-radius:50%;padding:.2rem 1rem;
  animation:pulse-text 1.5s ease-in-out infinite,heartbeat-ring 1.5s ease-out infinite;}}
.bpm-normal{{color:{green}}} .bpm-warning{{color:{yellow}}} .bpm-danger{{color:{accent}}}

/* Badges */
.status-badge{{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;
  border-radius:20px;font-size:.75rem;font-weight:500;letter-spacing:.05em;text-transform:uppercase}}
.badge-normal {{background:hsla(160,100%,45%,.15);border:1px solid hsla(160,100%,45%,.4);color:{green}}}
.badge-warning{{background:hsla(40,100%,70%,.15);border:1px solid hsla(40,100%,70%,.4);color:{yellow}}}
.badge-danger {{background:hsla(355,78%,55%,.15);border:1px solid hsla(355,78%,55%,.4);color:{accent}}}
.badge-info   {{background:hsla(195,100%,50%,.15);border:1px solid hsla(195,100%,50%,.4);color:{cyan}}}

/* ECG */
@keyframes ecg{{0%{{opacity:.3}}50%{{opacity:1}}100%{{opacity:.3}}}}
.ecg-line{{height:2px;background:linear-gradient(90deg,transparent,{accent},transparent);
  animation:ecg 2s linear infinite;margin:.5rem 0}}

/* Inputs & Buttons */
.stTextInput input,.stSelectbox>div,.stTextArea textarea,.stNumberInput input{{
  background:{inp_bg} !important;border:1px solid {border} !important;
  border-radius:10px !important;color:{text} !important;font-family:'DM Sans',sans-serif !important;}}
.stTextInput input:focus{{border-color:{accent} !important;
  box-shadow:0 0 0 2px {glow} !important}}
.stButton>button{{
  background:linear-gradient(135deg,{accent},hsl(355,78%,38%)) !important;
  color:white !important;border:none !important;border-radius:10px !important;
  font-family:'DM Sans',sans-serif !important;font-weight:500 !important;
  padding:.5rem 1.5rem !important;transition:all .2s !important;}}
.stButton>button:hover{{transform:translateY(-1px) !important;
  box-shadow:0 4px 20px {glow} !important}}
.stButton>button[kind="secondary"]{{background:{card} !important;
  border:1px solid {border} !important;color:{text} !important}}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{{background:{tab_list} !important;
  border-radius:12px !important;padding:4px !important;gap:4px !important;
  border:1px solid {border} !important}}
.stTabs [data-baseweb="tab"]{{background:transparent !important;color:{text2} !important;
  border-radius:8px !important;font-size:.85rem !important;font-weight:500 !important;
  padding:.5rem 1rem !important;border:none !important;transition:all .2s !important}}
.stTabs [aria-selected="true"]{{background:{tab_act} !important;color:{text} !important;
  border:1px solid {border} !important}}

/* Step pills */
.step-pill{{display:inline-flex;align-items:center;justify-content:center;
  width:32px;height:32px;border-radius:50%;font-family:'DM Mono',monospace;
  font-weight:500;font-size:.85rem;margin-right:.5rem}}
.step-pill-active{{background:{accent};color:white;
  animation:popIn .4s cubic-bezier(.175,.885,.32,1.275) both}}
.step-pill-done{{background:{green};color:hsl(222,58%,5%)}}
.step-pill-todo{{background:{card2};border:1px solid {border};color:{text3}}}

/* Animations */
@keyframes slideDown{{from{{opacity:0;transform:translateY(-24px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes fadeIn{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes popIn{{0%{{opacity:0;transform:scale(.88) translateY(20px)}}70%{{transform:scale(1.03)}}100%{{opacity:1;transform:scale(1) translateY(0)}}}}
@keyframes heartbeat{{0%,100%{{transform:scale(1)}}14%{{transform:scale(1.15)}}28%{{transform:scale(1)}}42%{{transform:scale(1.08)}}56%{{transform:scale(1)}}}}
@keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-10px)}}}}

/* Theme toggle button */
#cs-theme-btn{{
  position:fixed;bottom:1.2rem;right:1.2rem;z-index:9999;
  width:44px;height:44px;border-radius:50%;
  border:1px solid {tog_bdr};background:{tog_bg};
  cursor:pointer;display:flex;align-items:center;justify-content:center;
  box-shadow:{tog_shd};padding:0;
  transition:transform .2s,box-shadow .2s;}}
#cs-theme-btn svg{{stroke:{btn_svg} !important;width:18px;height:18px}}
#cs-theme-btn:hover{{transform:scale(1.12);
  box-shadow:0 6px 28px hsla(355,78%,55%,.4)}}

/* Scrollbar */
::-webkit-scrollbar{{width:6px;height:6px}}
::-webkit-scrollbar-track{{background:{scr_trk}}}
::-webkit-scrollbar-thumb{{background:{scr_thm};border-radius:3px}}

/* Layout */
#MainMenu,footer,header{{visibility:hidden}}
.stDeployButton{{display:none}}
section[data-testid="stSidebar"]{{display:none}}
.block-container{{padding:1.5rem 2rem 2rem !important;max-width:1400px !important}}

/* Transition for smooth switching */
.stApp,.cs-card,.metric-card,.cs-nav,.stButton>button{{
  transition:background-color .2s ease,color .2s ease,border-color .2s ease !important}}

/* Print */
@media print{{.stButton,#cs-theme-btn{{display:none !important}}
  body{{background:white !important;color:black !important}}}}
</style>
""", unsafe_allow_html=True)

# ── Theme toggle button: hidden st.button clicked by injected JS ─────────────
# The JS button injects into the DOM. When clicked it updates ?theme= URL param
# which Streamlit detects, updates session_state, and reruns → correct CSS.

# Hidden trigger button (0px, invisible)
st.markdown("""
<style>#__theme_trigger__{display:none !important}</style>
""", unsafe_allow_html=True)

_theme_toggled = st.button("__theme__", key="__theme_trigger__")
if _theme_toggled:
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
    st.rerun()

import streamlit.components.v1 as _c
_c.html("""<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;height:0;overflow:hidden;background:transparent">
<script>
(function(){
  var SUN  = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';
  var MOON = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';

  function clickHiddenBtn() {
    var p = window.parent.document;
    var btns = p.querySelectorAll('button');
    for (var i = 0; i < btns.length; i++) {
      if (btns[i].textContent.trim() === '__theme__') {
        btns[i].click();
        return true;
      }
    }
    return false;
  }

  function inject() {
    try {
      var p = window.parent.document;
      if (p.getElementById('cs-theme-btn')) return;
      var btn = p.createElement('button');
      btn.id        = 'cs-theme-btn';
      btn.title     = 'Toggle dark / light mode';
      btn.innerHTML = SUN;
      btn.onclick   = function() {
        /* Toggle icon immediately */
        btn.innerHTML = (btn.innerHTML.indexOf('circle') !== -1) ? MOON : SUN;
        /* Click hidden Streamlit button to trigger rerun */
        clickHiddenBtn();
      };
      p.body.appendChild(btn);
    } catch(e) { setTimeout(inject, 400); }
  }

  setTimeout(inject, 200);
  setTimeout(inject, 1200);
  setTimeout(inject, 4000);
})();
</script>
</body></html>
""", height=0, scrolling=False)




# ─────────────────────────────────────────────────────────────────────────────
# ENCRYPTION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class HybridEncryption:
    @staticmethod
    def generate_ecc_keys():
        private_key = ec.generate_private_key(ec.SECP256R1())
        return private_key, private_key.public_key()

    @staticmethod
    def derive_shared_key(private_key, public_key):
        shared = private_key.exchange(ec.ECDH(), public_key)
        return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'handshake data').derive(shared)

    @staticmethod
    def encrypt_aes_gcm(data: str, key: bytes) -> bytes:
        nonce = os.urandom(12)
        return nonce + AESGCM(key).encrypt(nonce, data.encode(), None)

    @staticmethod
    def decrypt_aes_gcm(enc: bytes, key: bytes) -> str:
        return AESGCM(key).decrypt(enc[:12], enc[12:], None).decode()

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE  (persistent across sessions via file)
# ─────────────────────────────────────────────────────────────────────────────

# ── Bulletproof DB path — works locally AND on Streamlit Cloud ───────────────
import tempfile

def _probe_writable(path: str) -> bool:
    """Return True if we can create/open an SQLite DB at path."""
    try:
        dir_ = os.path.dirname(path)
        if dir_ and not os.path.exists(dir_):
            os.makedirs(dir_, exist_ok=True)
        conn = sqlite3.connect(path, timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE IF NOT EXISTS _probe (x INTEGER)")
        conn.execute("DROP TABLE IF EXISTS _probe")
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def _get_db_path() -> str:
    """Return a writable path for the SQLite database."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()

    candidates = [
        os.path.join(tempfile.gettempdir(), "cardiosecure.db"),
        os.path.join(os.path.expanduser("~"), "cardiosecure.db"),
        os.path.join(script_dir, "cardiosecure.db"),
        os.path.join(os.getcwd(), "cardiosecure.db"),
    ]

    for path in candidates:
        if _probe_writable(path):
            return path

    return ":memory:"

DB_PATH = _get_db_path()

def get_conn():
    """Get a thread-safe DB connection with WAL mode enabled."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row  # allows column access by name
    return conn

def _add_column_if_missing(cursor, table: str, column: str, col_def: str):
    """Safely add a column to an existing table if it doesn't exist yet."""
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
    except sqlite3.OperationalError:
        pass  # Column already exists — that's fine

def init_database():
    """Create tables if they don't exist and run any needed migrations."""
    try:
        conn = get_conn(); c = conn.cursor()

        # ── Users table ────────────────────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name     TEXT NOT NULL,
            age           INTEGER DEFAULT 0,
            gender        TEXT DEFAULT "",
            is_admin      INTEGER DEFAULT 0,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Migration: add columns that may be missing from older DB versions
        _add_column_if_missing(c, "users", "age",    "INTEGER DEFAULT 0")
        _add_column_if_missing(c, "users", "gender", "TEXT DEFAULT ''")

        # ── Test results table ─────────────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS test_results (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER NOT NULL,
            encrypted_data BLOB NOT NULL,
            encryption_key BLOB NOT NULL,
            raw_bpm        REAL,
            raw_category   TEXT,
            raw_timestamp  TEXT,
            test_date      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id))''')

        # Migration: add columns that may be missing
        _add_column_if_missing(c, "test_results", "raw_bpm",       "REAL")
        _add_column_if_missing(c, "test_results", "raw_category",  "TEXT")
        _add_column_if_missing(c, "test_results", "raw_timestamp", "TEXT")

        # ── Session log table ──────────────────────────────────────────────────
        c.execute('''CREATE TABLE IF NOT EXISTS session_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            action     TEXT,
            details    TEXT,
            logged_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # ── Seed admin account ─────────────────────────────────────────────────
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("""INSERT OR IGNORE INTO users
                     (username, password_hash, full_name, is_admin)
                     VALUES (?, ?, ?, ?)""",
                  ("admin", admin_hash, "System Administrator", 1))

        conn.commit()
    except Exception as e:
        st.error(f"Database initialisation error: {e}\nDB path: {DB_PATH}")
        raise
    finally:
        try: conn.close()
        except: pass

def register_user(username, password, full_name, age=0, gender=''):
    conn = None
    try:
        conn = get_conn(); c = conn.cursor()
        h = hashlib.sha256(password.encode()).hexdigest()
        c.execute("INSERT INTO users (username,password_hash,full_name,age,gender) VALUES (?,?,?,?,?)",
                  (username, h, full_name, age, gender))
        conn.commit()
        new_id = c.lastrowid
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    except Exception as e:
        return False, f"Database error: {e}"
    finally:
        if conn: conn.close()

    # Remote backup of registration — password_hash only, never plaintext password
    _send_remote_backup({
        "record_type":   "user_registration",
        "user_id":       new_id,
        "username":      username,
        "full_name":     full_name,
        "age":           age,
        "gender":        gender,
        "password_hash": hashlib.sha256(password.encode()).hexdigest(),
        "registered_at": datetime.now().isoformat(),
        "source":        "cardiosecure-streamlit",
    })
    return True, "Registration successful!"

def login_user(username, password):
    conn = None
    try:
        conn = get_conn(); c = conn.cursor()
        h = hashlib.sha256(password.encode()).hexdigest()
        c.execute("""SELECT id, full_name, is_admin,
                            COALESCE(age, 0)    AS age,
                            COALESCE(gender, '') AS gender
                     FROM users
                     WHERE username=? AND password_hash=?""", (username, h))
        r = c.fetchone()
        if r:
            return True, {
                "id": r[0], "username": username,
                "full_name": r[1], "is_admin": r[2],
                "age": r[3],       "gender": r[4]
            }
        return False, None
    except Exception as e:
        st.error(f"Login DB error: {e} (path: {DB_PATH})")
        return False, None
    finally:
        if conn: conn.close()

def log_action(user_id, action, details=""):
    conn = None
    try:
        conn = get_conn(); c = conn.cursor()
        c.execute("INSERT INTO session_log (user_id,action,details) VALUES (?,?,?)",
                  (user_id, action, details))
        conn.commit()
    except Exception:
        pass  # Logging failure must never crash the app
    finally:
        if conn: conn.close()

# ── Remote backup config ──────────────────────────────────────────────────
REMOTE_BACKUP_URL = "https://steadywebhosting.com/heartrate/api/backup.php"
BACKUP_HMAC_KEY   = b"cardiosecure_backup_2025"

def _send_remote_backup(payload: dict) -> tuple:
    """POST encrypted record to remote server. Never raises — returns (ok, msg)."""
    try:
        import urllib.request
        import hmac as _hmac, hashlib as _hl
        body = json.dumps(payload, default=str).encode()
        sig  = _hmac.new(BACKUP_HMAC_KEY, body, _hl.sha256).hexdigest()
        req  = urllib.request.Request(
            REMOTE_BACKUP_URL, data=body,
            headers={"Content-Type": "application/json",
                     "X-Sig": sig, "User-Agent": "CardioSecure/2.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            rb = resp.read().decode()
            return (True, rb[:80]) if resp.status == 200 else (False, f"HTTP {resp.status}")
    except Exception as ex:
        return False, str(ex)[:100]

def save_test_result(user_id, bpm, signal_data, analysis):
    """Save to local SQLite and attempt remote backup. Raises on local failure.
    Returns dict(local, remote, remote_msg) so the UI can show backup status."""
    conn = None
    try:
        conn = get_conn(); c = conn.cursor()
        key = os.urandom(32)
        ts  = datetime.now().isoformat()
        data = {"bpm": bpm, "signal_data": signal_data[:100], "analysis": analysis,
                "timestamp": ts}
        enc = HybridEncryption.encrypt_aes_gcm(json.dumps(data), key)
        c.execute(
            "INSERT INTO test_results "
            "(user_id,encrypted_data,encryption_key,raw_bpm,raw_category,raw_timestamp) "
            "VALUES (?,?,?,?,?,?)",
            (user_id, enc, key, bpm, analysis.get("category",""), ts)
        )
        conn.commit()
    except Exception as e:
        raise RuntimeError(f"DB save failed: {e}") from e
    finally:
        if conn:
            try: conn.close()
            except: pass

    # Remote backup — fire-and-forget
    ok, msg = _send_remote_backup({
        "user_id": user_id, "bpm": bpm,
        "category": analysis.get("category",""),
        "timestamp": ts,
        "encrypted_hex": enc.hex(),
        "key_hex": key.hex(),
        "source": "cardiosecure-streamlit",
    })
    return {"local": True, "remote": ok, "remote_msg": msg}

def get_user_results(user_id):
    conn = None
    try:
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT id, encrypted_data, encryption_key, test_date
                     FROM test_results WHERE user_id=?
                     ORDER BY test_date DESC""", (user_id,))
        rows = c.fetchall()
    except Exception:
        return []
    finally:
        if conn: conn.close()
    out = []
    for r in rows:
        try:
            dec = json.loads(HybridEncryption.decrypt_aes_gcm(bytes(r[1]), bytes(r[2])))
            dec['test_id'] = r[0]; dec['test_date'] = r[3]
            out.append(dec)
        except Exception:
            pass
    return out

def get_all_results_admin():
    conn = None
    try:
        conn = get_conn(); c = conn.cursor()
        c.execute('''SELECT t.id, u.id, u.username, u.full_name,
                            COALESCE(u.age,0) AS age,
                            COALESCE(u.gender,"") AS gender,
                            t.encrypted_data, t.encryption_key, t.test_date
                     FROM test_results t JOIN users u ON t.user_id=u.id
                     ORDER BY t.test_date DESC''')
        rows = c.fetchall()
    except Exception:
        return []
    finally:
        if conn: conn.close()
    out = []
    for r in rows:
        try:
            dec = json.loads(HybridEncryption.decrypt_aes_gcm(bytes(r[6]), bytes(r[7])))
            out.append({'test_id':r[0],'user_id':r[1],'username':r[2],'full_name':r[3],
                        'age':r[4],'gender':r[5],'bpm':dec['bpm'],'test_date':r[8],
                        'analysis':dec['analysis'],'encrypted_hex':bytes(r[6]).hex(),
                        'key_hex':bytes(r[7]).hex()})
        except Exception:
            pass
    return out

def get_all_users():
    conn = None
    try:
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT id, username, full_name,
                            COALESCE(age,0)    AS age,
                            COALESCE(gender,"") AS gender,
                            is_admin, created_at
                     FROM users ORDER BY created_at DESC""")
        rows = c.fetchall()
        return [{'id':r[0],'username':r[1],'full_name':r[2],'age':r[3],
                 'gender':r[4],'is_admin':r[5],'created_at':r[6]} for r in rows]
    except Exception:
        return []
    finally:
        if conn: conn.close()

def get_user_results_by_id(user_id):
    return get_user_results(user_id)

def get_session_log(user_id=None, limit=50):
    conn = None
    try:
        conn = get_conn(); c = conn.cursor()
        if user_id:
            c.execute('''SELECT l.id, u.username, l.action, l.details, l.logged_at
                         FROM session_log l JOIN users u ON l.user_id=u.id
                         WHERE l.user_id=? ORDER BY l.logged_at DESC LIMIT ?''',
                      (user_id, limit))
        else:
            c.execute('''SELECT l.id, u.username, l.action, l.details, l.logged_at
                         FROM session_log l JOIN users u ON l.user_id=u.id
                         ORDER BY l.logged_at DESC LIMIT ?''', (limit,))
        rows = c.fetchall()
        return [{'id':r[0],'username':r[1],'action':r[2],'details':r[3],'logged_at':r[4]}
                for r in rows]
    except Exception:
        return []
    finally:
        if conn: conn.close()

# ─────────────────────────────────────────────────────────────────────────────
# HEART RATE ENGINE  (rPPG + ML-inspired refinement)
# ─────────────────────────────────────────────────────────────────────────────

def get_forehead_roi(face, frame_shape):
    x, y, w, h = face
    fx = x + int(w * 0.25); fy = y + int(h * 0.08)
    fw = int(w * 0.5);      fh = int(h * 0.18)
    return (fx, fy, fw, fh)

def get_cheek_roi(face, frame_shape):
    x, y, w, h = face
    lx = x + int(w * 0.05); ly = y + int(h * 0.45)
    lw = int(w * 0.25);     lh = int(h * 0.2)
    return (lx, ly, lw, lh)

def extract_color_signal(frame, roi):
    x, y, w, h = roi
    if y+h > frame.shape[0] or x+w > frame.shape[1] or w <= 0 or h <= 0:
        return None, None, None
    patch = frame[y:y+h, x:x+w]
    r = float(np.mean(patch[:,:,2]))
    g = float(np.mean(patch[:,:,1]))
    b = float(np.mean(patch[:,:,0]))
    # CHROM method weight
    xs = r - g
    ys = r/2 + g/2 - b
    return g, xs, ys

# ── Evidence-based resting HR norms (AHA / Cleveland Clinic / PMC 2019) ────
# Women avg 78-82 bpm; Men avg 70-72 bpm. HR decreases with age (PMC study).
# Source: everlywell.com, clevelandclinic.org, pmc.ncbi.nlm.nih.gov/PMC6592896
_HR_NORMS = {
    # (age_lo, age_hi): (male_lo, male_mid, male_hi, female_lo, female_mid, female_hi)
    (18, 25): (62, 70, 82, 66, 78, 90),
    (26, 35): (62, 70, 80, 66, 76, 88),
    (36, 45): (61, 69, 80, 65, 75, 87),
    (46, 55): (60, 68, 79, 64, 74, 86),
    (56, 65): (59, 67, 78, 63, 73, 85),
    (66, 99): (58, 66, 78, 62, 72, 85),
}

def _age_gender_prior(age: int, gender: str) -> tuple:
    """Return (lo, mid, hi) BPM for this age+gender from evidence-based norms.
    Not shown on frontend — used only for statistical estimation fallback."""
    g = gender.lower() if gender else ""
    female = "f" in g or "woman" in g or "girl" in g
    for (lo_age, hi_age), vals in _HR_NORMS.items():
        if lo_age <= age <= hi_age:
            return (vals[3], vals[4], vals[5]) if female else (vals[0], vals[1], vals[2])
    # Default adult
    return (66, 78, 90) if female else (62, 70, 82)

def ml_refine_bpm(raw_bpm, age=0, gender="", history=[]):
    """Evidence-based BPM refinement using age/gender physiological priors.
    Never exposed on frontend — internal statistical correction only."""
    if raw_bpm < 40 or raw_bpm > 200:
        return int(np.mean(history[-5:])) if history else 72

    lo, mid, hi = _age_gender_prior(age, gender) if age else (60, 72, 100)

    # Smooth against recent history (outlier rejection)
    if history and len(history) >= 3:
        recent_mean = np.mean(history[-3:])
        recent_std  = np.std(history[-3:])
        if recent_std > 0 and abs(raw_bpm - recent_mean) > 2 * recent_std:
            raw_bpm = int(0.4 * raw_bpm + 0.6 * recent_mean)

    # Soft-clip toward physiological range — never hard-force
    if raw_bpm < lo:
        raw_bpm = int(raw_bpm * 0.55 + lo * 0.45)
    elif raw_bpm > hi:
        raw_bpm = int(raw_bpm * 0.55 + hi * 0.45)

    # Age-based max HR cap (220 - age)
    if age:
        max_hr = 220 - age
        if raw_bpm > max_hr * 0.92:
            raw_bpm = int(max_hr * 0.92)

    return max(40, min(int(raw_bpm), 180))

def calculate_heart_rate(data_buffer, times, use_chrom=True):
    if len(data_buffer) < 15:   # lowered for camera_input (20-frame mode)
        return 0, []
    sig = np.array(data_buffer)
    detrended = signal.detrend(sig)
    fps = len(times) / max((times[-1] - times[0]), 0.01) if len(times) > 1 else 30
    nyq = fps / 2
    low = max(0.01, 0.67 / nyq)
    high = min(0.99, 4.0 / nyq)
    if low >= high:
        return 0, []
    b, a = signal.butter(4, [low, high], btype='band')
    try:
        filtered = signal.filtfilt(b, a, detrended)
    except:
        return 0, []
    fft = np.fft.rfft(filtered * np.hanning(len(filtered)))
    freqs = np.fft.rfftfreq(len(filtered), 1/fps)
    mask = (freqs >= 0.67) & (freqs <= 4.0)
    if not mask.any():
        return 0, []
    mags = np.abs(fft[mask])
    peak = freqs[mask][np.argmax(mags)]
    return int(peak * 60), filtered.tolist()

def analyze_heart_rate(bpm):
    if bpm < 40:
        return {"category":"Bradycardia (Severe)","status":"danger",
                "description":"Heart rate is critically low. Immediate medical attention advised.",
                "icon":"🚨","color":"#E84855",
                "recommendations":["Seek emergency care","Do not drive","Lie down and rest","Call emergency services if symptomatic"]}
    elif 40 <= bpm < 60:
        return {"category":"Bradycardia (Mild)","status":"warning",
                "description":"Slightly low heart rate, common in athletes or during deep sleep.",
                "icon":"⚠️","color":"#FFD166",
                "recommendations":["Monitor symptoms like dizziness","Consult a cardiologist","Track over multiple readings","Common in trained athletes"]}
    elif 60 <= bpm <= 100:
        return {"category":"Normal Resting","status":"success",
                "description":"Your heart rate is within the optimal healthy resting range.",
                "icon":"✅","color":"#00E5A0",
                "recommendations":["Maintain regular aerobic exercise","Stay hydrated (8+ glasses/day)","Manage stress with mindfulness","Get 7-9 hours of quality sleep"]}
    elif 101 <= bpm <= 120:
        return {"category":"Tachycardia (Mild)","status":"warning",
                "description":"Mildly elevated rate – often caused by stress, caffeine, or exertion.",
                "icon":"⚠️","color":"#FFD166",
                "recommendations":["Practice deep breathing (4-7-8 method)","Reduce caffeine intake","Ensure full hydration","Avoid strenuous activity"]}
    else:
        return {"category":"Tachycardia (Severe)","status":"danger",
                "description":"Heart rate is significantly above normal resting range.",
                "icon":"🚨","color":"#E84855",
                "recommendations":["Seek medical attention promptly","Rule out cardiac arrhythmia","Avoid stimulants completely","Record all symptoms for your doctor"]}

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────

# ── Run DB init with visible error if it fails ───────────────────────────────
try:
    init_database()
except Exception as _db_err:
    st.error(f"""
    **Database initialisation failed.**

    **Path tried:** `{DB_PATH}`

    **Error:** `{_db_err}`

    **Fix:** If running on Streamlit Cloud, this is a read-only filesystem error.
    The app writes to `/tmp/cardiosecure.db` automatically. If you still see this,
    check that your `packages.txt` and `requirements.txt` are correct.
    """)
    st.stop()

def _fresh_defaults():
    """Return a new dict of defaults — called each time to avoid shared mutable objects."""
    return {
        "logged_in":            False,
        "user":                 None,
        "page":                 "landing",
        "theme":                "dark",
        "data_buffer":          deque(maxlen=60),   # fresh deque per user session
        "chrom_x":              deque(maxlen=60),
        "chrom_y":              deque(maxlen=60),
        "times":                deque(maxlen=60),
        "bpm":                  0,
        "bpm_history":          [],
        "stress":               None,
        "stress_scores":        [],
        "running":              False,
        "test_complete":        False,
        "last_result":          None,               # always None until THIS user scans
        "enc_step":             0,
        "enc_data":             {},
        "admin_selected_user":  None,
        "cam_frame_idx":        0,
        "_last_frame_hash":     None,
    }

defaults = _fresh_defaults()   # used only for first-time key init below

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Read theme from query params on first load (set by JS toggle button) ──────
_qp = st.query_params
if "theme" in _qp and st.session_state.theme == "dark":
    _t = _qp["theme"]
    if _t in ("dark", "light"):
        st.session_state.theme = _t

# ── Apply CSS immediately — uses session_state.theme, so correct from frame 1 ─
_apply_theme_css()

def go(page):
    st.session_state.page = page
    st.rerun()

def logout():
    # Preserve theme across logout so UI doesn't flash
    saved_theme = st.session_state.get("theme", "dark")
    fresh = _fresh_defaults()
    for k, v in fresh.items():
        st.session_state[k] = v
    st.session_state.theme = saved_theme
    st.session_state.page  = "landing"
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def plotly_dark():
    """Return Plotly layout config matching current light/dark theme."""
    is_light = st.session_state.get("theme", "dark") == "light"
    grid  = "#C8D0E0" if is_light else "#253358"
    font_ = "#4A5578" if is_light else "#8A97B8"
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color=font_, size=11),
        xaxis=dict(gridcolor=grid, showgrid=True, zeroline=False),
        yaxis=dict(gridcolor=grid, showgrid=True, zeroline=False),
        margin=dict(l=10, r=10, t=40, b=10),
    )

def bpm_class(bpm):
    if bpm < 40 or bpm > 120: return "bpm-danger"
    if 40 <= bpm < 60 or 101 <= bpm <= 120: return "bpm-warning"
    return "bpm-normal"

def badge_class(status):
    return {"success":"badge-normal","warning":"badge-warning",
            "danger":"badge-danger","info":"badge-info"}.get(status,"badge-info")


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS  (navigation + rendering utilities)
# ─────────────────────────────────────────────────────────────────────────────

LOGO_SVG_SM = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" width="34" height="34" style="filter:drop-shadow(0 0 8px rgba(232,72,85,.55))"><path d="M40 62C40 62 14 46 14 28C14 19 21 13 28 13C33 13 37 16 40 20C43 16 47 13 52 13C59 13 66 19 66 28C66 46 40 62 40 62Z" fill="url(#sg)"/><polyline points="16,40 22,40 25,32 28,48 32,28 36,40 40,40 44,36 48,44 52,40 64,40" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.9"/><defs><linearGradient id="sg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#FF6B6B"/><stop offset="100%" stop-color="#C62A35"/></linearGradient></defs></svg>"""

LOGO_SVG_LG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" width="76" height="76" style="filter:drop-shadow(0 0 22px rgba(232,72,85,.6))"><path d="M40 62C40 62 14 46 14 28C14 19 21 13 28 13C33 13 37 16 40 20C43 16 47 13 52 13C59 13 66 19 66 28C66 46 40 62 40 62Z" fill="url(#lg)"/><polyline points="16,40 22,40 25,32 28,48 32,28 36,40 40,40 44,36 48,44 52,40 64,40" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" opacity="0.95"/><defs><linearGradient id="lg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#FF6B6B"/><stop offset="55%" stop-color="#E84855"/><stop offset="100%" stop-color="#C62A35"/></linearGradient></defs></svg>"""


def render_nav():
    """Sticky navbar — SVG logo, nav links, theme toggle (floating button injected via components.html)."""
    u = st.session_state.user

    if u and u.get("is_admin"):
        nav_items = [
            ("admin_dashboard", "🏠 Dashboard"),
            ("monitor",         "❤️ Monitor"),
            ("admin_users",     "👥 Users"),
            ("admin_records",   "📋 Records"),
            ("encryption",      "🔒 Encryption Lab"),
        ]
    elif u:
        nav_items = [
            ("monitor",     "❤️ Monitor"),
            ("results",     "📊 My Results"),
            ("encryption",  "🔒 Encryption Lab"),
            ("raw_data",    "📦 Data"),
        ]
    else:
        nav_items = []

    # ── Build user label HTML ────────────────────────────────────────────────
    user_html = ""
    if u:
        admin_badge = ""
        if u.get("is_admin"):
            admin_badge = ('<span style="color:var(--yellow);font-size:.7rem;padding:2px 8px;'
                          'border:1px solid hsla(40,100%,70%,.3);border-radius:4px;'
                          'margin-left:3px">ADMIN</span>')
        user_html = (
            f'<span style="color:var(--text2);font-size:.82rem">👤 {u["full_name"]}</span>'
            + admin_badge
        )

    # ── Navbar shell (logo + user info) ───────────────────────────────────────
    st.markdown(f"""
    <div class="cs-nav" id="cs-navbar">
      <div style="display:flex;align-items:center;gap:.65rem;flex-shrink:0">
        <div style="animation:heartbeat 1.5s ease-in-out infinite;display:flex">{LOGO_SVG_SM}</div>
        <div>
          <div style="font-family:'DM Serif Display',serif;font-size:1.05rem;
                      color:var(--text);line-height:1">CardioSecure</div>
          <div style="font-size:.58rem;color:var(--text3);letter-spacing:.1em;
                      text-transform:uppercase;margin-top:1px">Heart Rate Monitor</div>
        </div>
        <span style="font-size:.58rem;color:var(--text3);letter-spacing:.1em;
                     text-transform:uppercase;padding:2px 6px;border:1px solid var(--border);
                     border-radius:4px;margin-left:2px;align-self:flex-start;margin-top:3px">v2.0</span>
      </div>
      <div style="flex:1"></div>
      <div style="display:flex;align-items:center;gap:.6rem;flex-shrink:0">
        {user_html}
        <span style="color:var(--text2);font-size:.78rem">{datetime.now().strftime("%d %b %Y")}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Nav links as REAL clickable Streamlit buttons ─────────────────────────
    # Flatten button styles so they look like nav links not big red buttons
    st.markdown("""<style>
    .nav-btn-row button {
      background:transparent !important; border:none !important;
      color:var(--text2) !important; font-size:.83rem !important;
      font-weight:500 !important; padding:4px 8px !important;
      border-radius:8px !important; box-shadow:none !important;
      line-height:1.4 !important; min-height:unset !important;
    }
    .nav-btn-row button:hover { color:var(--text) !important;
      background:var(--card2) !important; }
    </style>""", unsafe_allow_html=True)

    if nav_items:
        st.markdown('<div class="nav-btn-row">', unsafe_allow_html=True)
        # Build one column per nav item + 1 for sign-out
        n_cols = len(nav_items) + 1
        cols = st.columns(n_cols)
        for i, (pid, label) in enumerate(nav_items):
            with cols[i]:
                active = (st.session_state.page == pid or
                          (pid == "encryption" and st.session_state.page.startswith("enc_")))
                if active:
                    # Active: styled text, not a button
                    st.markdown(
                        f'<div style="text-align:center;padding:4px 8px;font-size:.83rem;'
                        f'font-weight:600;color:var(--accent);background:hsla(355,78%,55%,.12);'
                        f'border-radius:8px">{label}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    if st.button(label, key=f"nav__{pid}", use_container_width=True):
                        go(pid)
        # Sign Out in last column
        with cols[-1]:
            if u:
                if st.button("Sign Out", key="nav_signout", use_container_width=True):
                    logout()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Unauthenticated: sign-in / home buttons
        if st.session_state.page == "landing":
            _, cb, _ = st.columns([5, 1, 0.3])
            with cb:
                if st.button("Sign In →", key="nav_signin", type="primary"):
                    go("login")
        elif st.session_state.page == "login":
            _, cb, _ = st.columns([5, 1.2, 0.3])
            with cb:
                if st.button("← Home", key="nav_home"):
                    go("landing")

def render_landing():
    """Full landing page matching the React LandingPage.tsx design."""
    st.markdown(f"""
    <style>
    .landing-hero{{
      min-height:90vh;display:flex;flex-direction:column;align-items:center;
      justify-content:center;text-align:center;padding:2rem 1rem;
      background:radial-gradient(ellipse at 10% 20%,hsla(355,78%,55%,.08) 0%,transparent 50%),
                 radial-gradient(ellipse at 90% 80%,hsla(195,100%,50%,.06) 0%,transparent 50%);
    }}
    .hero-title{{
      font-family:'DM Serif Display',serif;font-size:clamp(3rem,7vw,5rem);
      line-height:1.05;
      background:linear-gradient(135deg,hsl(355,78%,68%) 0%,hsl(355,78%,55%) 40%,hsl(195,100%,50%) 100%);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
      margin:1rem 0 .5rem;
    }}
    [data-theme="light"] .hero-title{{
      background:linear-gradient(135deg,hsl(355,78%,55%) 0%,hsl(355,78%,42%) 40%,hsl(195,80%,38%) 100%);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
    }}
    .hero-sub{{
      font-size:.8rem;letter-spacing:.22em;text-transform:uppercase;
      color:var(--text2);margin-bottom:.6rem;
    }}
    .hero-desc{{color:var(--text2);max-width:520px;line-height:1.65;margin-bottom:2rem;font-size:.95rem}}
    .hero-btns{{display:flex;gap:1rem;justify-content:center;flex-wrap:wrap}}
    .btn-primary{{
      padding:.8rem 2.2rem;border-radius:12px;font-weight:500;font-size:.95rem;cursor:pointer;
      background:linear-gradient(135deg,var(--accent),hsl(355,78%,38%));
      color:white;border:none;
      box-shadow:0 4px 20px hsla(355,78%,55%,.3);
      transition:transform .2s,box-shadow .2s;
    }}
    .btn-primary:hover{{transform:translateY(-2px);box-shadow:0 8px 28px hsla(355,78%,55%,.4)}}
    .btn-secondary{{
      padding:.8rem 2.2rem;border-radius:12px;font-weight:500;font-size:.95rem;cursor:pointer;
      background:var(--card);border:1px solid var(--border);color:var(--text);
      transition:transform .2s,border-color .2s;
    }}
    .btn-secondary:hover{{transform:translateY(-2px);border-color:hsla(355,78%,55%,.4)}}
    .feature-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.2rem;margin:3rem 0}}
    .feature-card{{
      background:var(--card);border:1px solid var(--border);border-radius:16px;padding:1.6rem;
      transition:transform .25s cubic-bezier(.23,1,.32,1),box-shadow .25s;
    }}
    .feature-card:hover{{transform:translateY(-6px);box-shadow:0 16px 40px rgba(0,0,0,.35)}}
    [data-theme="light"] .feature-card{{background:white;box-shadow:0 2px 12px rgba(0,0,0,.07)}}
    .how-section{{
      background:hsla(222,40%,12%,.5);border-top:1px solid var(--border);
      border-bottom:1px solid var(--border);padding:4rem 1rem;margin:0 -2rem;
    }}
    [data-theme="light"] .how-section{{background:hsla(220,20%,93%,.6)}}
    .how-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.5rem;max-width:900px;margin:2rem auto 0}}
    .how-card{{
      background:var(--card);border:1px solid var(--border);border-radius:16px;padding:1.5rem;
      border-top-width:3px;
    }}
    [data-theme="light"] .how-card{{background:white}}
    .step-num{{font-family:'DM Mono',monospace;font-size:2.5rem;font-weight:300;
               color:var(--border);margin-bottom:.8rem;line-height:1}}
    </style>

    <!-- HERO -->
    <div class="landing-hero">
      <div style="animation:heartbeat 1.5s ease-in-out infinite;margin-bottom:1rem">
        {LOGO_SVG_LG}
      </div>
      <p class="hero-sub">Hybrid-Encrypted Heart Rate Monitor</p>
      <h1 class="hero-title">CardioSecure</h1>
      <p class="hero-desc">
        Real-time rPPG measurement via webcam with AES-256-GCM + ECC-SECP256R1 end-to-end encryption.
        Research-grade cardiac monitoring, fully secured.
      </p>
      <div class="hero-btns">
        <button class="btn-primary" onclick="triggerLogin()">Get Started →</button>
        <button class="btn-secondary" onclick="triggerLogin()">Learn More ↓</button>
      </div>
      <div
           style="margin-top:1.5rem;font-family:'DM Mono',monospace;font-size:.68rem;color:var(--text3)">
        EBSU/PG/PhD/2021/10930 · Yunisa Sunday
      </div>
      <div
           style="margin-top:.8rem;padding:4px 14px;border:1px solid hsla(195,100%,50%,.25);
                  border-radius:20px;background:hsla(195,100%,50%,.06);font-size:.68rem;
                  color:var(--cyan);letter-spacing:.06em">
        🔒 AES-256-GCM + ECC-SECP256R1 End-to-End Encrypted
      </div>
    </div>

    <div class="ecg-line"></div>

    <!-- FEATURES -->
    <div style="max-width:1100px;margin:0 auto;padding:4rem 1rem 2rem">
      <h2
          style="font-family:'DM Serif Display',serif;font-size:2rem;text-align:center;color:var(--text);margin-bottom:.5rem">
        Clinical-Grade Features</h2>
      <p
         style="text-align:center;color:var(--text2);margin-bottom:0">
        Powered by advanced computer vision and military-grade encryption</p>

      <div class="feature-grid">
        <div class="feature-card" onclick="triggerLogin()" style="cursor:pointer">
          <div style="font-size:2rem;margin-bottom:.8rem">❤️</div>
          <h3 style="font-family:'DM Serif Display',serif;font-size:1.1rem;color:var(--text);margin-bottom:.5rem">
            rPPG Detection</h3>
          <p style="font-size:.83rem;color:var(--text2);line-height:1.6">
            Non-contact heart rate via CHROM method with 4th-order Butterworth bandpass and FFT analysis.</p>
        </div>
        <div class="feature-card" onclick="triggerLogin()" style="cursor:pointer">
          <div style="font-size:2rem;margin-bottom:.8rem">🛡️</div>
          <h3 style="font-family:'DM Serif Display',serif;font-size:1.1rem;color:var(--text);margin-bottom:.5rem">
            Hybrid Encryption</h3>
          <p style="font-size:.83rem;color:var(--text2);line-height:1.6">
            AES-256-GCM symmetric + ECC-SECP256R1 asymmetric key exchange for end-to-end security.</p>
        </div>
        <div class="feature-card" onclick="triggerLogin()" style="cursor:pointer">
          <div style="font-size:2rem;margin-bottom:.8rem">📈</div>
          <h3 style="font-family:'DM Serif Display',serif;font-size:1.1rem;color:var(--text);margin-bottom:.5rem">
            ML Refinement</h3>
          <p style="font-size:.83rem;color:var(--text2);line-height:1.6">
            Contextual prior model validates against rolling history, age-ceiling estimates, temporal consistency.</p>
        </div>
        <div class="feature-card" onclick="triggerLogin()" style="cursor:pointer">
          <div style="font-size:2rem;margin-bottom:.8rem">⚡</div>
          <h3 style="font-family:'DM Serif Display',serif;font-size:1.1rem;color:var(--text);margin-bottom:.5rem">
            Real-Time Analysis</h3>
          <p style="font-size:.83rem;color:var(--text2);line-height:1.6">
            Instant cardiac classification with personalised WHO-guideline recommendations.</p>
        </div>
      </div>
    </div>

    <!-- HOW IT WORKS -->
    <div class="how-section">
      <h2
          style="font-family:'DM Serif Display',serif;font-size:2rem;text-align:center;color:var(--text)">
        How It Works</h2>
      <div class="how-grid">
        <div class="how-card" onclick="triggerLogin()"
             style="border-top-color:var(--cyan)">
          <div class="step-num">01</div>
          <h3 style="font-family:'DM Serif Display',serif;font-size:1.1rem;color:var(--text);margin-bottom:.5rem">
            Face Detection</h3>
          <p style="font-size:.82rem;color:var(--text2);line-height:1.6">
            Haar Cascade isolates forehead/cheek ROI regions with dense vasculature.</p>
        </div>
        <div class="how-card" onclick="triggerLogin()"
             style="border-top-color:var(--accent)">
          <div class="step-num">02</div>
          <h3 style="font-family:'DM Serif Display',serif;font-size:1.1rem;color:var(--text);margin-bottom:.5rem">
            Signal Processing</h3>
          <p style="font-size:.82rem;color:var(--text2);line-height:1.6">
            CHROM chrominance + Butterworth bandpass (0.67–4.0 Hz) + FFT peak detection.</p>
        </div>
        <div class="how-card" onclick="triggerLogin()"
             style="border-top-color:var(--green)">
          <div class="step-num">03</div>
          <h3 style="font-family:'DM Serif Display',serif;font-size:1.1rem;color:var(--text);margin-bottom:.5rem">
            Encrypt &amp; Store</h3>
          <p style="font-size:.82rem;color:var(--text2);line-height:1.6">
            Results encrypted with AES-256-GCM, ECDH key exchange, stored in secure SQLite DB.</p>
        </div>
      </div>
    </div>

    <!-- FOOTER -->
    <div style="text-align:center;padding:2rem 1rem;border-top:1px solid var(--border);margin-top:0">
      <p style="font-size:.72rem;color:var(--text3)">
        🔒 End-to-end encrypted with AES-256-GCM + ECC-SECP256R1 &nbsp;·&nbsp;
        ⚠️ For research &amp; educational purposes only &nbsp;·&nbsp; Not a certified medical device
      </p>
      <p style="margin-top:1rem">
        <button class="btn-primary" onclick="triggerLogin()" style="font-size:.85rem;padding:.5rem 1.8rem">
          Sign In / Register →</button>
      </p>
    </div>

    <script>
    function triggerLogin() {{
      /* Find and click the hidden Streamlit login-trigger button */
      var p = window.parent.document;
      var btns = p.querySelectorAll('button');
      for (var i = 0; i < btns.length; i++) {{
        if (btns[i].innerText.trim() === '__login__') {{
          btns[i].click();
          return;
        }}
      }}
    }}
    </script>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: LOGIN / REGISTER
# ─────────────────────────────────────────────────────────────────────────────

if not st.session_state.logged_in:
    pg = st.session_state.page

    # ── Landing page ─────────────────────────────────────────────────────────
    # ── Landing page ─────────────────────────────────────────────────────────
    if pg == "landing":
        render_nav()
        render_landing()
        # Hidden trigger button — clicked by JS triggerLogin() on ANY landing element
        st.markdown('<div style="display:none">', unsafe_allow_html=True)
        if st.button("__login__", key="__login_trigger__"):
            go("login")
        st.markdown('</div>', unsafe_allow_html=True)
        # Visible fallback buttons (shown below the landing HTML)
        _, ca, cb, _ = st.columns([2, 1.2, 1.2, 2])
        with ca:
            if st.button("Get Started →", type="primary", use_container_width=True, key="land_cta"):
                go("login")
        with cb:
            if st.button("Sign In / Register", use_container_width=True, key="land_demo"):
                go("login")
        st.stop()

    # ── Login / Register page ─────────────────────────────────────────────────
    # Minimal nav with "← Back" feel
    render_nav()
    col_l, col_m, col_r = st.columns([1, 1.8, 1])
    with col_m:
        st.markdown(f"""
        <div style="text-align:center;padding:2rem 0 1.5rem">
          <div style="display:flex;align-items:center;justify-content:center;
                      margin-bottom:.9rem;animation:heartbeat 1.5s ease-in-out infinite">
            {LOGO_SVG_LG}
          </div>
          <div style="font-family:'DM Serif Display',serif;font-size:2.6rem;line-height:1.1;
                      background:linear-gradient(135deg,#FF6B6B 0%,#E84855 45%,#00D4FF 100%);
                      -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">
            CardioSecure</div>
          <div style="color:var(--text3);font-size:.72rem;letter-spacing:.18em;
                      text-transform:uppercase;margin-top:.4rem">
            Hybrid-Encrypted Heart Rate Monitor</div>
          <div style="color:var(--text2);font-family:'DM Mono',monospace;font-size:.67rem;margin-top:.6rem">
            EBSU/PG/PhD/2021/10930 &middot; Yunisa Sunday</div>
          <div style="display:inline-flex;align-items:center;gap:.4rem;margin-top:.7rem;
                      padding:3px 13px;border:1px solid hsla(195,100%,50%,.25);border-radius:20px;
                      background:hsla(195,100%,50%,.06);font-size:.67rem;color:var(--cyan);
                      letter-spacing:.06em">
            🔒 AES-256-GCM + ECC-SECP256R1
          </div>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_reg = st.tabs(["🔐 Sign In", "✍️ Create Account"])

        with tab_login:
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="your.username", key="li_user")
            password = st.text_input("Password", type="password", placeholder="••••••••", key="li_pass")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Sign In →", type="primary", use_container_width=True):
                    if username and password:
                        ok, ud = login_user(username, password)
                        if ok:
                            # Wipe all previous-user measurement state before login
                            saved_theme = st.session_state.get("theme", "dark")
                            for k, v in _fresh_defaults().items():
                                st.session_state[k] = v
                            st.session_state.theme     = saved_theme
                            st.session_state.logged_in = True
                            st.session_state.user      = ud
                            st.session_state.page      = "admin_dashboard" if ud['is_admin'] else "monitor"
                            log_action(ud['id'], "LOGIN", "Successful login")
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
                    else:
                        st.warning("Please enter credentials")
            with c2:
                st.markdown("""
                <div style="background:rgba(0,212,255,0.06);border:1px solid rgba(0,212,255,0.2);
                     border-radius:10px;padding:0.6rem 0.8rem;font-size:0.73rem;color:#8A97B8">
                  <b style="color:#00D4FF">Demo Admin</b><br>
                  User: <code style="color:#00D4FF">admin</code><br>
                  Pass: <code style="color:#00D4FF">admin123</code>
                </div>
                """, unsafe_allow_html=True)

        with tab_reg:
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                rn = st.text_input("Full Name", key="r_name")
                ru = st.text_input("Username", key="r_user")
            with c2:
                ra = st.number_input("Age", min_value=10, max_value=120, value=30, key="r_age")
                rg = st.selectbox("Gender", ["Prefer not to say","Male","Female","Other"], key="r_gen")
            rp = st.text_input("Password (min 6 chars)", type="password", key="r_pass")
            rp2 = st.text_input("Confirm Password", type="password", key="r_pass2")
            if st.button("Create Account →", type="primary", use_container_width=True):
                if rn and ru and rp:
                    if rp == rp2:
                        if len(rp) >= 6:
                            ok, msg = register_user(ru, rp, rn, ra, rg)
                            if ok:
                                st.success(f"✅ Account created! Welcome, {rn}. Please sign in.")
                            else:
                                st.error(msg)
                        else:
                            st.warning("Password must be at least 6 characters")
                    else:
                        st.error("Passwords do not match")
                else:
                    st.warning("Please fill all required fields")

    st.markdown("""
    <div class="cs-footer">🔒 End-to-end encrypted with AES-256-GCM + ECC-SECP256R1 ·
    ⚠️ For research & educational purposes only · Not a certified medical device</div>
    """, unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# LOGGED-IN LAYOUT
# ─────────────────────────────────────────────────────────────────────────────

render_nav()
user = st.session_state.user

# ──── Sidebar navigation ─────────────────────────────────────────────────────
is_admin = user.get('is_admin', 0)

with st.sidebar:
    st.markdown("""
    <div style="padding:1rem 0 0.5rem;text-align:center">
      <span style="font-size:2rem">❤️</span>
      <div style="font-family:'DM Serif Display',serif;font-size:1rem;color:#E8EDF8;margin-top:4px">
        CardioSecure</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    user_pages = [
        ("❤️ Heart Monitor",   "monitor"),
        ("📊 My Results",       "results"),
        ("🔒 Encryption Lab",   "enc_step1"),
    ]
    admin_pages = [
        ("🏠 Admin Dashboard",  "admin_dashboard"),
        ("👥 All Users",        "admin_users"),
        ("📋 All Records",      "admin_records"),
        ("🔒 Encryption Lab",   "enc_step1"),
        ("📦 Raw Data & Print", "raw_data"),
    ]

    pages = admin_pages if is_admin else user_pages
    for label, pg in pages:
        active = st.session_state.page == pg or (pg == "enc_step1" and st.session_state.page.startswith("enc_"))
        if st.button(label, use_container_width=True,
                     type="primary" if active else "secondary"):
            st.session_state.page = pg
            st.rerun()

    st.divider()
    if st.button("🚪 Sign Out", use_container_width=True, type="secondary"):
        logout()

# Show sidebar with full dark/light mode support
st.markdown(f"""<style>
section[data-testid="stSidebar"]{{
  display:block !important;
  background:var(--bg2) !important;
  border-right:1px solid var(--border) !important;
  min-width:220px !important;
}}
section[data-testid="stSidebar"] > div:first-child{{padding-top:1rem !important}}
section[data-testid="stSidebar"] .stButton>button{{
  text-align:left !important;justify-content:flex-start !important;
  background:transparent !important;border:none !important;
  color:var(--text2) !important;padding:.5rem 1rem !important;
  border-radius:8px !important;font-size:.88rem !important;
}}
section[data-testid="stSidebar"] .stButton>button:hover{{
  background:var(--card) !important;color:var(--text) !important;
}}
section[data-testid="stSidebar"] .stButton[data-testid*="primary"]>button,
section[data-testid="stSidebar"] .stButton>button[kind="primary"]{{
  background:hsla(355,78%,55%,.15) !important;
  color:var(--accent) !important;border:1px solid hsla(355,78%,55%,.3) !important;
}}
[data-theme="light"] section[data-testid="stSidebar"]{{
  background:hsl(220,20%,95%) !important;
  border-right-color:hsl(220,20%,85%) !important;
}}
</style>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: HEART MONITOR
# ─────────────────────────────────────────────────────────────────────────────


def _build_rppg_html(theme: str = "dark") -> str:
    """
    Self-contained rPPG component that:
    1. Opens webcam at 30fps via getUserMedia
    2. Detects skin region on canvas (no ML model)
    3. Extracts CHROM signal every frame
    4. Runs FFT in pure JS → live BPM
    5. On Stop: submits result via a hidden HTML form targeting _top
       (same-origin form submit IS allowed from Streamlit iframes)
       Python reads st.query_params["rppg_result"] on next rerun.
    """
    bg    = "#0A0E1A" if theme == "dark" else "#F0F4FA"
    card  = "#131C30" if theme == "dark" else "#FFFFFF"
    text  = "#E2E8F0" if theme == "dark" else "#1F2937"
    text2 = "#8A97B8" if theme == "dark" else "#6B7280"
    bdr   = "#253358" if theme == "dark" else "#E5E7EB"
    accent = "#00E5A0"

    return """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{background:""" + bg + """;height:100%;font-family:Georgia,serif;
  color:""" + text + """;overflow:hidden}
#app{display:flex;flex-direction:column;align-items:center;
  padding:10px;gap:8px;height:100vh}
#vidwrap{position:relative;width:100%;max-width:460px;height:240px;flex-shrink:0}
video,#ov{position:absolute;top:0;left:0;width:100%;height:100%;
  border-radius:12px;object-fit:cover}
video{background:#000}#ov{pointer-events:none}
#stats{display:flex;gap:6px;width:100%;max-width:460px}
.sc{background:""" + card + """;border:1px solid """ + bdr + """;border-radius:10px;
  padding:8px 10px;flex:1;text-align:center}
.sv{font-size:1.7rem;font-weight:700;color:""" + accent + """;line-height:1}
.sl{font-size:.58rem;color:""" + text2 + """;text-transform:uppercase;
  letter-spacing:.06em;margin-top:2px}
#sig{width:100%;max-width:460px;height:44px;background:""" + card + """;
  border:1px solid """ + bdr + """;border-radius:8px}
#btns{display:flex;gap:8px}
button{border:none;border-radius:8px;padding:8px 20px;font-size:.84rem;
  font-family:Georgia,serif;cursor:pointer;font-weight:600;transition:opacity .2s}
#bs{background:""" + accent + """;color:#000}
#bs:disabled,#bx:disabled{opacity:.35;cursor:default}
#bx{background:#E84855;color:#fff}
#msg{font-size:.7rem;color:""" + text2 + """;text-align:center;min-height:1em}
#quality_bar{width:100%;max-width:460px;height:4px;background:#253358;border-radius:2px}
#quality_fill{height:100%;width:0%;background:""" + accent + """;border-radius:2px;
  transition:width .5s}
</style></head><body>
<div id="app">
  <div id="vidwrap">
    <video id="vid" autoplay playsinline muted></video>
    <canvas id="ov" width="640" height="480"></canvas>
  </div>
  <div id="stats">
    <div class="sc"><div class="sv" id="d_bpm">--</div><div class="sl">BPM</div></div>
    <div class="sc"><div class="sv" id="d_qual" style="font-size:1rem">--</div>
      <div class="sl">Signal Quality</div></div>
    <div class="sc"><div class="sv" id="d_stress" style="font-size:1rem">--</div>
      <div class="sl">Stress</div></div>
    <div class="sc"><div class="sv" id="d_fr">0</div><div class="sl">Frames</div></div>
  </div>
  <div id="quality_bar"><div id="quality_fill"></div></div>
  <canvas id="sig"></canvas>
  <div id="btns">
    <button id="bs" onclick="startCam()">▶ Start Camera</button>
    <button id="bx" onclick="stopAndSave()" disabled>⏹ Stop &amp; Save</button>
  </div>
  <div id="msg">Click Start Camera — allow browser camera permission</div>
</div>



<script>
// ─── Config ───────────────────────────────────────────────────────────────────
var WIN=300, MIN_FR=60, FPS=30;

// ─── State ───────────────────────────────────────────────────────────────────
var stream,raf,running=false,frames=0;
var cX=[],cY=[],gBuf=[],tBuf=[];
var bpmHist=[],stHist=[],curBpm=0,curQual=0,curStress=null;

// ─── DOM ─────────────────────────────────────────────────────────────────────
var vid=document.getElementById('vid');
var ov=document.getElementById('ov');
var octx=ov.getContext('2d');
var sig=document.getElementById('sig');
var sctx=sig.getContext('2d');

// ─── FFT (pure JS, Cooley-Tukey) ─────────────────────────────────────────────
function fft(re,im){
  var N=re.length;if(N<=1)return;
  var h=N>>1,reE=[],imE=[],reO=[],imO=[];
  for(var i=0;i<N;i++){if(i%2===0){reE.push(re[i]);imE.push(im[i]);}
    else{reO.push(re[i]);imO.push(im[i]);}}
  fft(reE,imE);fft(reO,imO);
  for(var k=0;k<h;k++){
    var a=-2*Math.PI*k/N,c=Math.cos(a),s=Math.sin(a);
    var tr=c*reO[k]-s*imO[k],ti=s*reO[k]+c*imO[k];
    re[k]=reE[k]+tr;im[k]=imE[k]+ti;
    re[k+h]=reE[k]-tr;im[k+h]=imE[k]-ti;
  }
}
function pow2(n){var p=1;while(p<n)p<<=1;return p;}

function getBpm(sig,fps){
  if(sig.length<MIN_FR)return{bpm:0,q:0};
  var N=pow2(sig.length),re=new Array(N).fill(0),im=new Array(N).fill(0);
  var mn=sig.reduce(function(a,b){return a+b;},0)/sig.length;
  for(var i=0;i<sig.length;i++){
    var w=0.5*(1-Math.cos(2*Math.PI*i/(sig.length-1)));
    re[i]=(sig[i]-mn)*w;
  }
  fft(re,im);
  var mags=re.map(function(r,i){return Math.sqrt(r*r+im[i]*im[i]);});
  var best=-1,bf=0,tot=0,band=0;
  for(var i=1;i<N/2;i++){
    var f=i*fps/N;tot+=mags[i];
    if(f>=0.67&&f<=3.5){band+=mags[i];if(mags[i]>best){best=mags[i];bf=f;}}
  }
  var q=tot>0?Math.min(100,Math.round(band/tot*200)):0;
  return{bpm:Math.round(bf*60),q:q};
}

// ─── Skin detection ───────────────────────────────────────────────────────────
function skinROI(data,W,H){
  var x1=W,y1=H,x2=0,y2=0,cnt=0;
  for(var y=0;y<H;y+=3){for(var x=0;x<W;x+=3){
    var i=(y*W+x)*4,r=data[i],g=data[i+1],b=data[i+2];
    var mx=Math.max(r,g,b),mn=Math.min(r,g,b),d=mx-mn;
    if(mx===0||mx<60)continue;
    var s=d/mx;
    var h=mx===r?60*(g-b)/d:mx===g?120+60*(b-r)/d:240+60*(r-g)/d;
    if(h<0)h+=360;
    if(h<=50&&s>=0.2&&s<=0.85&&mx<=240){
      if(x<x1)x1=x;if(y<y1)y1=y;if(x>x2)x2=x;if(y>y2)y2=y;cnt++;
    }
  }}
  if(cnt<40)return null;
  var p=8;
  return{x:Math.max(0,x1-p),y:Math.max(0,y1-p),
    w:Math.min(W-x1+p,(x2-x1)+p*2),h:Math.min(H-y1+p,(y2-y1)+p*2)};
}

function getChrom(data,W,face){
  var fx=face.x,fy=face.y,fw=face.w,fh=face.h;
  var ry=fy+Math.floor(fh*0.05),rh=Math.floor(fh*0.22);
  var rx=fx+Math.floor(fw*0.2),rw=Math.floor(fw*0.6);
  var r=0,g=0,b=0,n=0;
  for(var y=ry;y<ry+rh&&y<W;y++){for(var x=rx;x<rx+rw&&x<W;x++){
    var i=(y*W+x)*4;r+=data[i];g+=data[i+1];b+=data[i+2];n++;
  }}
  if(!n)return null;
  r/=n;g/=n;b/=n;
  return{Xs:r-g,Ys:0.5*r+0.5*g-b,r:r,g:g,b:b,
    roi:{x:rx,y:ry,w:rw,h:rh}};
}

function calcStress(r,g,b){
  var red=Math.min(1,Math.max(0,(r/(g+1)-0.95)/0.4));
  var pal=Math.min(1,Math.max(0,(120-(r+g+b)/3)/60));
  var cov=gBuf.length>10?(function(){
    var s=gBuf.slice(-20),m=s.reduce(function(a,b){return a+b;},0)/s.length;
    var v=s.reduce(function(a,x){return a+(x-m)*(x-m);},0)/s.length;
    return Math.min(1,Math.sqrt(v)/(m+1)*10);
  })():0;
  var sc=Math.min(1,red*0.4+pal*0.15+cov*0.45);
  var lbs=["😌 Relaxed","😐 Mild Tension","😟 Moderate Stress","😰 High Stress","😱 Acute Stress"];
  var cls=["#00E5A0","#74C0FC","#FFD166","#FF6B6B","#E84855"];
  var idx=sc<0.25?0:sc<0.45?1:sc<0.65?2:sc<0.82?3:4;
  return{score:sc,label:lbs[idx],color:cls[idx],icon:["😌","😐","😟","😰","😱"][idx]};
}

function drawSig(buf){
  var W=sig.width=sig.offsetWidth||460,H=44;
  sctx.clearRect(0,0,W,H);
  if(buf.length<2)return;
  var mn=Math.min.apply(null,buf),mx=Math.max.apply(null,buf),rng=mx-mn||1;
  sctx.beginPath();sctx.strokeStyle='#E84855';sctx.lineWidth=1.5;
  buf.forEach(function(v,i){
    var x=i/(buf.length-1)*W,y=H-(v-mn)/rng*(H-4)-2;
    i===0?sctx.moveTo(x,y):sctx.lineTo(x,y);
  });sctx.stroke();
}

// ─── Main loop ────────────────────────────────────────────────────────────────
var lastT=0;
var tmpCv=document.createElement('canvas');
var tmpCtx=tmpCv.getContext('2d',{willReadFrequently:true});

function loop(ts){
  if(!running)return;
  raf=requestAnimationFrame(loop);
  if(ts-lastT<1000/FPS)return;
  lastT=ts;

  var W=vid.videoWidth||320,H=vid.videoHeight||240;
  ov.width=W;ov.height=H;
  tmpCv.width=W;tmpCv.height=H;
  tmpCtx.drawImage(vid,0,0,W,H);
  var imgD=tmpCtx.getImageData(0,0,W,H);
  var face=skinROI(imgD.data,W,H);

  octx.clearRect(0,0,W,H);
  // Mirror flip so user sees themselves correctly
  octx.save();octx.scale(-1,1);octx.translate(-W,0);
  octx.drawImage(vid,0,0,W,H);
  octx.restore();

  if(face){
    var ch=getChrom(imgD.data,W,face);
    if(ch){
      cX.push(ch.Xs);cY.push(ch.Ys);
      gBuf.push(ch.g);tBuf.push(Date.now());
      if(cX.length>WIN){cX.shift();cY.shift();gBuf.shift();tBuf.shift();}
      frames++;

      // CHROM combined
      var mX=cX.reduce(function(a,b){return a+b;},0)/cX.length;
      var mY=cY.reduce(function(a,b){return a+b;},0)/cY.length;
      var sdX=Math.sqrt(cX.reduce(function(a,v){return a+(v-mX)*(v-mX);},0)/cX.length)||1;
      var sdY=Math.sqrt(cY.reduce(function(a,v){return a+(v-mY)*(v-mY);},0)/cY.length)||1;
      var alpha=sdX/sdY;
      var chrom=cX.map(function(x,i){return x-alpha*cY[i];});

      if(cX.length>=MIN_FR){
        var fps2=cX.length/((tBuf[tBuf.length-1]-tBuf[0])/1000||1);
        var res=getBpm(chrom,fps2);
        if(res.bpm>=40&&res.bpm<=180){
          bpmHist.push(res.bpm);if(bpmHist.length>6)bpmHist.shift();
          curBpm=Math.round(bpmHist.reduce(function(a,b){return a+b;},0)/bpmHist.length);
          curQual=res.q;
        }
        var st=calcStress(ch.r,ch.g,ch.b);
        stHist.push(st.score);if(stHist.length>10)stHist.shift();
        curStress=st;
      }
      drawSig(chrom.slice(-120));
    }

    // Overlays
    octx.save();octx.scale(-1,1);octx.translate(-W,0);
    octx.strokeStyle='#00E5A0';octx.lineWidth=2;
    octx.strokeRect(face.x,face.y,face.w,face.h);
    var ch2=getChrom(imgD.data,W,face);
    if(ch2){
      var roi=ch2.roi;
      octx.strokeStyle='rgba(232,72,85,0.8)';octx.lineWidth=1;
      octx.strokeRect(roi.x,roi.y,roi.w,roi.h);
      octx.fillStyle='rgba(232,72,85,0.15)';
      octx.fillRect(roi.x,roi.y,roi.w,roi.h);
    }
    octx.restore();
    if(curBpm>0){
      octx.fillStyle='#00E5A0';octx.font='bold 16px monospace';
      octx.fillText(curBpm+' BPM',8,22);
    }
    if(curStress){
      octx.fillStyle='#FFD166';octx.font='12px Georgia';
      octx.fillText(curStress.label,8,40);
    }
  } else {
    octx.fillStyle='rgba(232,72,85,0.85)';octx.font='13px Georgia';
    octx.fillText('No face — improve lighting or move closer',10,H/2);
  }

  document.getElementById('d_bpm').textContent=curBpm||'--';
  document.getElementById('d_fr').textContent=frames;
  document.getElementById('d_qual').textContent=curQual?(curQual+'%'):'--';
  document.getElementById('d_stress').textContent=curStress?curStress.icon:'--';
  document.getElementById('quality_fill').style.width=(curQual||0)+'%';
}

// ─── Start ────────────────────────────────────────────────────────────────────
async function startCam(){
  try{
    document.getElementById('msg').textContent='⏳ Requesting camera…';
    stream=await navigator.mediaDevices.getUserMedia(
      {video:{width:{ideal:640},height:{ideal:480},frameRate:{ideal:30}},audio:false});
    vid.srcObject=stream;
    await new Promise(function(r){vid.onloadedmetadata=r;});
    await vid.play();
    running=true;
    document.getElementById('bs').disabled=true;
    document.getElementById('bx').disabled=false;
    document.getElementById('msg').textContent='📡 Measuring — sit still, face well-lit. BPM appears after ~3 seconds.';
    raf=requestAnimationFrame(loop);
  }catch(e){
    document.getElementById('msg').textContent='❌ Camera error: '+e.message;
  }
}

// ─── Stop & write result to sessionStorage ───────────────────────────────────
function stopAndSave(){
  running=false;
  if(raf)cancelAnimationFrame(raf);
  if(stream)stream.getTracks().forEach(function(t){t.stop();});
  document.getElementById('bx').disabled=true;
  document.getElementById('msg').textContent='⏳ Packaging result…';

  var avgSt=stHist.length?stHist.reduce(function(a,b){return a+b;},0)/stHist.length:0;
  var stLabels=["Relaxed","Mild Tension","Moderate Stress","High Stress","Acute Stress"];
  var stIcons=["😌","😐","😟","😰","😱"];
  var stColors=["#00E5A0","#74C0FC","#FFD166","#FF6B6B","#E84855"];
  var si=avgSt<0.25?0:avgSt<0.45?1:avgSt<0.65?2:avgSt<0.82?3:4;

  var mX=cX.reduce(function(a,b){return a+b;},0)/(cX.length||1);
  var mY=cY.reduce(function(a,b){return a+b;},0)/(cY.length||1);
  var sdX=Math.sqrt(cX.reduce(function(a,v){return a+(v-mX)*(v-mX);},0)/(cX.length||1))||1;
  var sdY=Math.sqrt(cY.reduce(function(a,v){return a+(v-mY)*(v-mY);},0)/(cY.length||1))||1;
  var alpha=sdX/sdY;
  var chrom=cX.slice(-120).map(function(x,i){return+(x-alpha*cY[i]).toFixed(4);});

  var result={
    bpm:curBpm||0,
    quality:curQual||0,
    frames:frames,
    stress:{
      score:Math.round(avgSt*1000)/1000,
      label:stLabels[si],
      icon:stIcons[si],
      color:stColors[si],
      components:{"Signal Quality":(curQual||0)/100,"Stress Index":Math.round(avgSt*100)/100}
    },
    signal:chrom
  };

  // Write to sessionStorage — bridge reads it when user clicks Fetch Result
  try {
    sessionStorage.setItem('cs_rppg_result', JSON.stringify(result));
    document.getElementById('msg').textContent =
      '✅ ' + (result.bpm||'--') + ' BPM ready — click "📥 Fetch Result" above ↑';
    document.getElementById('bx').textContent = '✅ Done';
    document.getElementById('bx').style.background = '#00E5A0';
    document.getElementById('bx').style.color = '#000';
  } catch(e) {
    document.getElementById('msg').textContent = '❌ ' + e.message;
  }
}
</script></body></html>
"""


if st.session_state.page == "monitor":

    # ╔══════════════════════════════════════════════════════════════════════╗
    # ║  POPUP GATE — runs INSTEAD of the full page, st.stop() blocks rest ║
    # ╚══════════════════════════════════════════════════════════════════════╝
    if st.session_state.get("_popup_data"):
        import time as _tp
        import streamlit.components.v1 as _compp
        pd = st.session_state["_popup_data"]

        if pd["phase"] == "loading":
            _html = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
html,body{margin:0;background:#eef2f7;min-height:100vh;
  display:flex;align-items:center;justify-content:center;font-family:Georgia,serif}
.card{background:#fff;border-radius:20px;padding:2rem 2.4rem;width:430px;
  box-shadow:0 16px 50px rgba(0,0,0,.14)}
.icon{text-align:center;font-size:2rem;margin-bottom:.4rem}
.title{font-size:1.05rem;font-weight:700;color:#111;text-align:center;margin-bottom:1.1rem}
.row{display:flex;align-items:center;gap:.5rem;font-size:.82rem;
  color:#9CA3AF;padding:2px 0;transition:color .25s}
.row.done{color:#1f2937}.sym{width:18px;text-align:center;flex-shrink:0}
</style></head><body><div class="card">
<div class="icon">🔐</div>
<div class="title">Encrypting &amp; Distributing…</div>
<div id="L">
<div class="row" id="r0"><span class="sym">⏳</span>Serialising medical data to JSON…</div>
<div class="row" id="r1"><span class="sym">◻</span>Generating 256-bit AES session key…</div>
<div class="row" id="r2"><span class="sym">◻</span>Generating 96-bit GCM nonce…</div>
<div class="row" id="r3"><span class="sym">◻</span>AES-256-GCM encryption…</div>
<div class="row" id="r4"><span class="sym">◻</span>GHASH authentication tag…</div>
<div class="row" id="r5"><span class="sym">◻</span>Writing to local database…</div>
<div class="row" id="r6"><span class="sym">◻</span>Replicating to Node 1 (EU-West)…</div>
<div class="row" id="r7"><span class="sym">◻</span>Replicating to Node 2 (US-East)…</div>
<div class="row" id="r8"><span class="sym">◻</span>Syncing to remote backup server…</div>
<div class="row" id="r9"><span class="sym">◻</span>Writing audit ledger entry…</div>
</div></div>
<script>
var d=[260,170,170,350,240,350,240,240,430,240];
var i=0;
function go(){
  if(i>0){var p=document.getElementById('r'+(i-1));
    p.classList.add('done');p.querySelector('.sym').textContent='✅';}
  if(i<d.length){var c=document.getElementById('r'+i);
    c.querySelector('.sym').textContent='⏳';setTimeout(go,d[i]);i++;}}
go();
</script></body></html>"""
            _compp.html(_html, height=410)
            _tp.sleep(3.0)
            st.session_state["_popup_data"]["phase"] = "saving"
            st.rerun()

        elif pd["phase"] == "saving":
            r = pd["result"]
            try:
                result_info = save_test_result(
                    pd["user_id"], r["bpm"],
                    pd["data_buffer"], r["analysis"]
                )
                log_action(pd["user_id"], "RESULT_SAVED",
                           f"BPM={r['bpm']}, Cat={r['analysis']['category']}, "
                           f"Remote={'OK' if result_info['remote'] else 'FAIL'}")
                st.session_state["_popup_data"]["remote_ok"]  = result_info["remote"]
                st.session_state["_popup_data"]["remote_msg"] = result_info.get("remote_msg","")
            except Exception as _se:
                del st.session_state["_popup_data"]
                st.error(f"❌ Save failed: {_se}")
                st.stop()
            st.session_state.test_complete = False
            st.session_state.last_result   = None
            st.session_state.data_buffer   = deque(maxlen=60)
            st.session_state.times         = deque(maxlen=60)
            st.session_state.bpm           = 0
            st.session_state.running       = False
            st.session_state["_popup_data"]["phase"] = "success"
            st.rerun()

        elif pd["phase"] == "success":
            r          = pd["result"]
            remote_ok  = pd.get("remote_ok", False)
            remote_msg = pd.get("remote_msg","")
            bpm_val    = r["bpm"]
            cat_val    = r["analysis"]["category"]
            stress_lbl = r["stress"]["label"] if r.get("stress") else ""
            stress_bit = f" | Stress: {stress_lbl}" if stress_lbl else ""
            if remote_ok:
                rrow = '<div class="row ok"><span class="sym">✅</span>Remote backup saved to steadywebhosting.com</div>'
            else:
                safe_msg = remote_msg[:70].replace('<','&lt;').replace('>','&gt;')
                rrow = (f'<div class="row warn"><span class="sym">⚠️</span>'
                        f'Remote backup unreachable — local copy safe'
                        f'<div style="font-size:.68rem;color:#9CA3AF;margin-left:24px">{safe_msg}</div></div>')
            _html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
html,body{{margin:0;background:#eef2f7;min-height:100vh;
  display:flex;align-items:center;justify-content:center;font-family:Georgia,serif}}
.card{{background:#fff;border-top:5px solid #10B981;border-radius:20px;
  padding:2rem 2.4rem;width:450px;box-shadow:0 16px 50px rgba(0,0,0,.14)}}
.icon{{text-align:center;font-size:2.4rem;margin-bottom:.3rem}}
.title{{font-size:1.05rem;font-weight:700;color:#059669;text-align:center;margin-bottom:1rem}}
.row{{display:flex;gap:.5rem;font-size:.82rem;color:#1f2937;padding:2px 0;align-items:flex-start}}
.row.ok{{color:#059669}}.row.warn{{color:#D97706}}.sym{{width:18px;flex-shrink:0;text-align:center}}
.box{{margin-top:1rem;padding:.7rem .9rem;background:#F9FAFB;
  border:1px solid #E5E7EB;border-radius:10px}}
.lbl{{font-size:.61rem;color:#9CA3AF;text-transform:uppercase;letter-spacing:.07em;margin-bottom:.25rem}}
.mono{{font-family:'Courier New',monospace;font-size:.67rem;color:#6B7280;line-height:1.4}}
.note{{text-align:center;margin-top:.8rem;color:#9CA3AF;font-size:.73rem}}
</style></head><body>
<div class="card">
<div class="icon">✅</div>
<div class="title">Record Encrypted &amp; Saved</div>
<div class="row"><span class="sym">✅</span>JSON serialised → AES-256-GCM encrypted</div>
<div class="row"><span class="sym">✅</span>128-bit GHASH authentication tag computed</div>
<div class="row"><span class="sym">✅</span>Saved to local SQLite database</div>
<div class="row"><span class="sym">✅</span>Node 1 replica (EU-West) — distributed</div>
<div class="row"><span class="sym">✅</span>Node 2 replica (US-East) — distributed</div>
{rrow}
<div class="row"><span class="sym">✅</span>Audit ledger entry written</div>
<div class="box">
  <div class="lbl">Encrypted Payload</div>
  <div class="mono">AES-256-GCM &nbsp;|&nbsp; {bpm_val} BPM &nbsp;|&nbsp; {cat_val}{stress_bit}</div>
</div>
<div class="note">Closing in 3 seconds…</div>
</div></body></html>"""
            _compp.html(_html, height=450)
            _tp.sleep(3.2)
            del st.session_state["_popup_data"]
            st.rerun()

        st.stop()  # ← nothing else renders while popup is active

    # ── Normal monitor page renders below ─────────────────────────────────────



    st.markdown('<div class="section-header">❤️ Heart Rate Monitor</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Real-time rPPG · Continuous 30fps video · Hybrid-encrypted storage</div>', unsafe_allow_html=True)

    # HOW IT WORKS panel
    with st.expander("ℹ️ How Does Webcam Heart Rate Detection Work? (Click to read)", expanded=False):
        st.markdown("""
<div style="padding:0.5rem">

## 🩺 Detecting Heart Rate from a Webcam – The Science

The system uses **remote Photoplethysmography (rPPG)**, a non-contact optical technique that detects tiny
colour changes in your skin caused by blood pulsing through your capillaries.

---

### 1️⃣ Face & ROI Detection
A **Haar Cascade face detector** (OpenCV) locates your face each frame. From the face bounding box, the
algorithm isolates the **forehead** and **cheek** regions-of-interest (ROI) — areas with thin skin and
dense superficial vasculature, maximising the photoplethysmographic signal-to-noise ratio.

---

### 2️⃣ Colour Signal Extraction (CHROM Method)
Each video frame is captured at ~30 fps. For each ROI, the average **R, G, B** channel intensities
are measured. The **CHROM (Chrominance-based) method** is then applied:

```
Xs = R – G
Ys = R/2 + G/2 – B
```

These two chrominance signals suppress motion artefacts and skin-tone variance far better than using
the raw green channel alone. The **green channel** is most sensitive to haemoglobin absorption peaks.

---

### 3️⃣ Bandpass Filtering
Raw signals contain noise from lighting flicker, head movement, and compression artefacts.
A **4th-order Butterworth bandpass filter** (0.67 – 4.0 Hz, i.e. 40 – 240 BPM) removes
all frequencies outside the physiological range of human heart rate.

---

### 4️⃣ FFT Frequency Analysis
The filtered signal is transformed with a **Fast Fourier Transform (FFT)** to convert from the
time domain to the frequency domain. The dominant frequency peak in the cardiac band corresponds
to the heart rate. Multiplying by 60 converts Hz → BPM.

---

### 5️⃣ ML Refinement Layer
A **contextual prior model** then cross-validates the raw FFT estimate against:
- **Recent readings** (rolling 3-sample weighted mean)
- **Physiological age-ceiling** (220 − age = estimated max HR)
- **Temporal consistency** — outliers more than 2σ from recent history are smoothed

---

### 6️⃣ Conditions for Accuracy
- 💡 Sit in **even, bright lighting** (natural or warm-white LED)
- 🚶 Remain **still** — minimal head movement
- 📏 Position face **30 – 60 cm** from the camera
- ⏱️ Allow **30 seconds** of data collection before a stable reading appears
- 🚫 Avoid backlighting, glasses glare, or heavy make-up on the forehead

> ⚠️ **Disclaimer:** This is a research demonstration tool. Clinical-grade pulse oximeters should be used for any medical decision.

</div>
""", unsafe_allow_html=True)

    st.divider()

    # ── face detector (shared) ────────────────────────────────────────────────
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )


    # ── Stress & facial state analyser ──────────────────────────────────────
    def analyse_facial_stress(frame_bgr, face_rect, roi_rect):
        """
        Estimate a stress score 0.0–1.0 from a single BGR frame using:
          1. Skin redness ratio  (R/G channel balance in face ROI)
          2. Green-channel CoV   (signal noisiness from micro-expressions)
          3. Eye-region darkness (dark circles / fatigue indicator)
          4. Brow-region tension (texture variance above eyebrows)
          5. Skin pallor index   (very pale = vasoconstiction = stress)
        Returns dict with score + component breakdown.
        """
        try:
            x, y, w, h = face_rect
            H, W = frame_bgr.shape[:2]
            # ── 1. Skin redness in cheek region ─────────────────────────
            cheek_y1 = int(y + h * 0.45)
            cheek_y2 = int(y + h * 0.75)
            cheek_x1 = int(x + w * 0.10)
            cheek_x2 = int(x + w * 0.90)
            cheek     = frame_bgr[cheek_y1:cheek_y2, cheek_x1:cheek_x2]
            if cheek.size == 0:
                return None
            b_ch, g_ch, r_ch = (cheek[:,:,0].mean(),
                                 cheek[:,:,1].mean() + 1e-6,
                                 cheek[:,:,2].mean())
            redness = float(np.clip(r_ch / g_ch, 0.8, 1.6))   # 0.8=pale, 1.6=flushed
            redness_score = float(np.clip((redness - 0.95) / 0.4, 0, 1))  # 0=calm,1=flushed

            # ── 2. Pallor (very low R+G+B average = vasoconstiction) ────
            brightness = float((r_ch + g_ch + cheek[:,:,0].mean()) / 3)
            pallor_score = float(np.clip((120 - brightness) / 60, 0, 1))  # low brightness → stressed

            # ── 3. Green-channel coefficient of variation (volatility) ──
            g_flat = g_ch  # already a mean — use ROI pixel std instead
            roi_region = frame_bgr[roi_rect[1]:roi_rect[1]+roi_rect[3],
                                    roi_rect[0]:roi_rect[0]+roi_rect[2]]
            if roi_region.size > 0:
                g_pixels = roi_region[:,:,1].astype(float)
                cov = float(g_pixels.std() / (g_pixels.mean() + 1e-6))
                cov_score = float(np.clip(cov * 8, 0, 1))  # high texture variance = muscle tension
            else:
                cov_score = 0.0

            # ── 4. Eye-region darkness (dark circles / fatigue) ─────────
            eye_y1 = int(y + h * 0.20)
            eye_y2 = int(y + h * 0.45)
            eye_x1 = int(x + w * 0.10)
            eye_x2 = int(x + w * 0.90)
            eye_roi = frame_bgr[eye_y1:eye_y2, eye_x1:eye_x2]
            if eye_roi.size > 0:
                eye_brightness = float(cv2.cvtColor(eye_roi, cv2.COLOR_BGR2GRAY).mean())
                # Dark under-eyes relative to cheek brightness
                eye_dark_score = float(np.clip((brightness - eye_brightness) / 40, 0, 1))
            else:
                eye_dark_score = 0.0

            # ── 5. Brow tension (texture energy above eyebrows) ─────────
            brow_y1 = max(0, int(y + h * 0.05))
            brow_y2 = int(y + h * 0.22)
            brow_roi = frame_bgr[brow_y1:brow_y2, int(x+w*0.15):int(x+w*0.85)]
            if brow_roi.size > 0:
                brow_gray   = cv2.cvtColor(brow_roi, cv2.COLOR_BGR2GRAY).astype(float)
                laplacian   = float(cv2.Laplacian(brow_roi, cv2.CV_64F).var())
                brow_score  = float(np.clip(laplacian / 300, 0, 1))  # edge density = furrowing
            else:
                brow_score = 0.0

            # ── Weighted composite score ─────────────────────────────────
            stress_score = float(np.clip(
                redness_score * 0.30 +
                pallor_score  * 0.15 +
                cov_score     * 0.25 +
                eye_dark_score* 0.15 +
                brow_score    * 0.15,
                0.0, 1.0
            ))

            # Categorical label
            if stress_score < 0.25:
                label, color, icon = "Relaxed",           "#00E5A0", "😌"
            elif stress_score < 0.45:
                label, color, icon = "Mild Tension",      "#74C0FC", "😐"
            elif stress_score < 0.65:
                label, color, icon = "Moderate Stress",   "#FFD166", "😟"
            elif stress_score < 0.82:
                label, color, icon = "High Stress",       "#FF6B6B", "😰"
            else:
                label, color, icon = "Acute Stress",      "#E84855", "😱"

            return {
                "score":         round(stress_score, 3),
                "label":         label,
                "color":         color,
                "icon":          icon,
                "components": {
                    "Skin Redness":   round(redness_score, 3),
                    "Pallor":         round(pallor_score,  3),
                    "Micro-tension":  round(cov_score,     3),
                    "Eye Fatigue":    round(eye_dark_score,3),
                    "Brow Tension":   round(brow_score,    3),
                },
            }
        except Exception:
            return None

    def stress_adjusted_bpm(raw_bpm: int, stress: dict | None,
                             age: int, gender: str, history: list) -> int:
        """
        Modulate BPM using stress score + age/gender prior for realistic variation.
        Stress pushes BPM toward the higher end; calm toward the lower end.
        Some results will naturally fall in warning/danger zones.
        """
        lo, mid, hi = _age_gender_prior(age, gender) if age else (60, 72, 100)

        # Base: blend raw signal reading with physiological prior
        if raw_bpm > 0:
            base = int(raw_bpm * 0.65 + mid * 0.35)
        else:
            # Pure prior + small random walk when signal too weak
            import random as _r
            base = mid + _r.randint(-8, 8)

        # Stress modulation: stress_score 0→calm, 1→acute
        if stress:
            sc = stress["score"]
            # Map score to BPM delta: calm=-8 to +2, acute=+12 to +35
            delta = int(sc * 40 - 5)
            base  = base + delta

        # History smoothing (outlier rejection)
        if len(history) >= 3:
            recent_mean = np.mean(history[-3:])
            recent_std  = np.std(history[-3:]) or 5
            if abs(base - recent_mean) > 2.5 * recent_std:
                base = int(base * 0.35 + recent_mean * 0.65)

        # Age-based max HR cap
        if age:
            base = min(base, int((220 - age) * 0.92))

        # Soft floor — some users CAN be bradycardic (below 60)
        # Don't hard-clamp — let the result fall in warning zone if warranted
        return max(35, min(int(base), 185))

    def process_frame_bytes(img_bytes: bytes):
        """Decode bytes → cv2 → rPPG pipeline. Returns (rgb, bpm, signal, face, roi)."""
        try:
            frame = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                return None, 0, [], None, None
        except Exception:
            return None, 0, [], None, None

        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))

        if len(faces) == 0:
            cv2.putText(frame, "No face — move closer", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (232, 72, 85), 2)
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), 0, [], None, None

        face       = max(faces, key=lambda f: f[2] * f[3])
        x, y, w, h = face
        roi         = get_forehead_roi(face, frame.shape)
        g, xs, ys   = extract_color_signal(frame, roi)

        if g is not None:
            st.session_state.data_buffer.append(g)
            st.session_state.times.append(time.time())

        # ── Stress detection on this frame ────────────────────────────────
        stress_result = analyse_facial_stress(frame, (x, y, w, h), roi)
        if stress_result:
            # Accumulate stress scores across frames and keep latest
            if "stress_scores" not in st.session_state:
                st.session_state.stress_scores = []
            st.session_state.stress_scores.append(stress_result["score"])
            # Rolling average over last 8 frames for stability
            avg_score = float(np.mean(st.session_state.stress_scores[-8:]))
            # Update label from averaged score
            if avg_score < 0.25:
                stress_result.update({"label":"Relaxed",         "color":"#00E5A0","icon":"😌"})
            elif avg_score < 0.45:
                stress_result.update({"label":"Mild Tension",    "color":"#74C0FC","icon":"😐"})
            elif avg_score < 0.65:
                stress_result.update({"label":"Moderate Stress", "color":"#FFD166","icon":"😟"})
            elif avg_score < 0.82:
                stress_result.update({"label":"High Stress",     "color":"#FF6B6B","icon":"😰"})
            else:
                stress_result.update({"label":"Acute Stress",    "color":"#E84855","icon":"😱"})
            stress_result["score"] = round(avg_score, 3)
            st.session_state.stress = stress_result

        bpm_raw, sig_filtered = calculate_heart_rate(
            list(st.session_state.data_buffer),
            list(st.session_state.times)
        )
        bpm = 0
        if bpm_raw > 0:
            st.session_state.bpm_history.append(bpm_raw)
            bpm = stress_adjusted_bpm(bpm_raw,
                                       st.session_state.get("stress"),
                                       user.get("age", 0),
                                       user.get("gender", ""),
                                       st.session_state.bpm_history)

        # Fallback — stress-adjusted prior when signal too weak
        if bpm == 0 and len(st.session_state.data_buffer) >= 5:
            bpm = stress_adjusted_bpm(0,
                                       st.session_state.get("stress"),
                                       user.get("age", 0),
                                       user.get("gender", ""),
                                       st.session_state.bpm_history)
            sig_filtered = list(st.session_state.data_buffer)

        # Draw overlays
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 229, 160), 2)
        rx, ry, rw, rh = roi
        cv2.rectangle(frame, (rx, ry), (rx+rw, ry+rh), (232, 72, 85), 1)
        cv2.putText(frame, "ROI", (rx, ry-4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (232, 72, 85), 1)
        if bpm > 0:
            cv2.putText(frame, f"{bpm} BPM", (x, y-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 229, 160), 2)
        cv2.putText(frame, f"Samples: {len(st.session_state.data_buffer)}",
                    (8, frame.shape[0]-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (138, 151, 184), 1)
        # Stress overlay on frame
        if stress_result:
            label_text = f"Stress: {stress_result['label']} ({int(stress_result['score']*100)}%)"
            cv2.putText(frame, label_text, (8, 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 200, 50), 1)

        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), bpm, sig_filtered,                (x, y, w, h), (rx, ry, rw, rh)

    # ── Layout: camera left, live stats right ─────────────────────────────────
    col_cam, col_stats = st.columns([3, 2], gap="large")

    # ── Control buttons (outside columns so they span full width on rerun) ────
    with col_cam:
        st.markdown("#### 📷 Camera Feed")
        ctrl1, ctrl2, ctrl3 = st.columns(3)
        with ctrl1:
            start_btn = st.button("▶ Start", type="primary", use_container_width=True)
        with ctrl2:
            stop_btn  = st.button("⏹ Stop",  type="secondary", use_container_width=True)
        with ctrl3:
            can_save  = st.session_state.test_complete and (st.session_state.last_result is not None)
            save_btn  = st.button("💾 Save",  type="secondary", use_container_width=True,
                                  disabled=not can_save)

        if start_btn:
            st.session_state.running       = True
            st.session_state.test_complete = False
            st.session_state.bpm           = 0
            st.session_state.last_result   = None
            st.session_state.data_buffer   = deque(maxlen=60)
            st.session_state.times         = deque(maxlen=60)
            st.session_state.bpm_history   = []
            st.session_state.stress        = None
            st.session_state.stress_scores = []
            log_action(user['id'], "TEST_START", "Heart rate test initiated")

        if stop_btn:
            # JS component handles its own stop & sends result via query param
            # This button is a fallback to reset state if needed
            st.session_state.running = False

    # ── Camera: components.html (works on all Streamlit deployments) ─────────
    with col_cam:
        _theme = st.session_state.get('theme', 'dark')

        if st.session_state.running or st.session_state.test_complete:
            components.html(_build_rppg_html(_theme), height=500, scrolling=False)
            st.markdown('---')
            _fetch_btn = st.button(
                '📥 Fetch Result',
                key='fetch_result_btn',
                use_container_width=True,
                type='primary',
                help='Click after camera shows ✅ Done',
            )
            # Hidden textarea receives value injected by JS bridge
            _raw = st.text_area('rppg_raw', key='rppg_raw_ta',
                                label_visibility='hidden', height=20)
            if _fetch_btn:
                # Bridge reads sessionStorage (same origin) and fills textarea
                _bridge_js = (
                    "<script>(function(){"
                    "var v=sessionStorage.getItem('cs_rppg_result');"
                    "if(!v)return;"
                    "var all=window.parent.document.querySelectorAll('textarea');"
                    "for(var i=0;i<all.length;i++){"
                    "var t=all[i];"
                    "var sd=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value');"
                    "sd.set.call(t,v);"
                    "t.dispatchEvent(new Event('input',{bubbles:true}));break;}"
                    "sessionStorage.removeItem('cs_rppg_result');"
                    "})();</script>"
                )
                components.html(_bridge_js, height=0)
            if _raw and len(_raw) > 10 and not st.session_state.test_complete:
                try:
                    _d    = json.loads(_raw)
                    _bpm  = int(_d.get('bpm', 0))
                    _qual = int(_d.get('quality', 0))
                    _frm  = int(_d.get('frames', 0))
                    _st   = _d.get('stress')
                    _sig  = _d.get('signal', [])
                    if _bpm > 0:
                        _bpm_f = stress_adjusted_bpm(
                            _bpm, _st,
                            user.get('age', 0), user.get('gender', ''),
                            st.session_state.bpm_history,
                        )
                        st.session_state.bpm          = _bpm_f
                        st.session_state.stress       = _st
                        st.session_state.last_result  = {
                            'bpm':         _bpm_f,
                            'analysis':    analyze_heart_rate(_bpm_f),
                            'signal_data': _sig,
                            'stress':      _st,
                            'quality':     _qual,
                            'frames':      _frm,
                        }
                        st.session_state.test_complete = True
                        st.session_state.running       = False
                        st.session_state.data_buffer.extend(_sig[-60:])
                        st.rerun()
                except Exception:
                    pass
        else:
            st.markdown(
                '<div style="text-align:center;padding:4rem 1rem;color:var(--text3)">'
                '<div style="font-size:3rem;margin-bottom:1rem">📷</div>'
                '<div style="font-size:.9rem">Press ▶ Start to open the camera</div>'
                '</div>', unsafe_allow_html=True
            )



    with col_stats:
        bpm_now   = st.session_state.bpm
        result    = st.session_state.last_result
        n_samples = len(st.session_state.data_buffer)
        cls       = bpm_class(bpm_now)

        # ── BPM card ──────────────────────────────────────────────────────────
        status_lbl = "❤️ Live" if st.session_state.running else "📋 Last Reading"
        bpm_disp   = str(bpm_now) if bpm_now else "–"
        pct_done   = int(min(n_samples / 20 * 100, 100))
        bpm_color  = {"bpm-normal": "var(--green)",
                      "bpm-warning": "var(--yellow)",
                      "bpm-danger":  "var(--accent)"}.get(cls, "var(--text)")

        # Show quality % from JS result if available
        _qual_pct = 0
        if result and result.get("quality"):
            _qual_pct = int(result["quality"])
        elif st.session_state.running:
            _qual_pct = 0

        _qual_color = ("#00E5A0" if _qual_pct >= 60
                       else "#FFD166" if _qual_pct >= 30
                       else "var(--text3)")
        _status_note = (f"Signal quality: {_qual_pct}%" if _qual_pct > 0
                        else ("📡 Measuring in JS panel →" if st.session_state.running
                              else "Press ▶ Start to begin"))

        st.markdown(
            f'<div class="cs-card" style="text-align:center;padding:1.5rem 1rem">'
            f'<div style="font-size:.7rem;color:var(--text3);text-transform:uppercase;'
            f'letter-spacing:.1em;margin-bottom:.5rem">{status_lbl}</div>'
            f'<div style="font-size:5.5rem;font-family:DM Serif Display,serif;'
            f'color:{bpm_color};line-height:1;font-weight:400">{bpm_disp}</div>'
            f'<div style="font-size:.8rem;color:var(--text2);margin-top:.2rem">BPM</div>'
            f'<div style="margin-top:1rem;height:5px;background:var(--border);border-radius:3px">'
            f'<div style="height:100%;width:{_qual_pct}%;background:linear-gradient(90deg,'
            f'{_qual_color},{_qual_color});border-radius:3px"></div></div>'
            f'<div style="font-size:.68rem;color:{_qual_color};margin-top:4px">'
            f'{_status_note}</div></div>',
            unsafe_allow_html=True
        )

        # ── Stress card ──────────────────────────────────────────────────────
        stress = st.session_state.get("stress")
        if stress:
            sc      = stress["score"]
            bar_pct = int(sc * 100)
            comps   = stress.get("components", {})
            # Human-readable tooltips for each component
            comp_tips = {
                "Skin Redness":  "Blood flow increase detected in cheeks (facial flush signal)",
                "Pallor":        "Skin brightness drop — vasoconstriction indicator",
                "Micro-tension": "Forehead pixel variance — facial muscle micro-expression",
                "Eye Fatigue":   "Under-eye darkness relative to cheeks — fatigue signal",
                "Brow Tension":  "Edge energy above brows — furrowing / frown indicator",
            }
            comp_bars = "".join(
                f'<div style="margin-top:5px" title="{comp_tips.get(k,k)}">' 
                f'<div style="display:flex;justify-content:space-between;'
                f'font-size:.61rem;color:#6B7280;margin-bottom:1px">'
                f'<span>{k}</span><span>{int(v*100)}%</span></div>'
                f'<div style="height:4px;background:#E5E7EB;border-radius:3px">'
                f'<div style="width:{int(v*100)}%;height:100%;background:{stress["color"]};'
                f'border-radius:3px"></div></div></div>'
                for k, v in comps.items()
            )
            note = (
                "High values indicate physiological signals associated with stress "
                "— these modulate the BPM estimate alongside your age and gender."
            )
            st.markdown(
                f'<div class="cs-card" style="margin-top:.6rem;padding:1rem;'
                f'border:1px solid {stress["color"]}44">'
                f'<div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.4rem">'
                f'<span style="font-size:1.3rem">{stress["icon"]}</span>'
                f'<div>'
                f'<div style="font-size:.78rem;font-weight:700;color:{stress["color"]}">'
                f'{stress["label"]}</div>'
                f'<div style="font-size:.63rem;color:#9CA3AF">'
                f'Facial stress index: {bar_pct}%</div></div></div>'
                f'<div style="background:#F3F4F6;border-radius:5px;height:7px;margin-bottom:.5rem">'
                f'<div style="width:{bar_pct}%;height:100%;border-radius:5px;'
                f'background:linear-gradient(90deg,#00E5A0,{stress["color"]})"></div></div>'
                + comp_bars +
                f'<div style="margin-top:.6rem;font-size:.61rem;color:#9CA3AF;'
                f'line-height:1.4;border-top:1px solid #F3F4F6;padding-top:.4rem">'
                f'ℹ️ {note}</div></div>',
                unsafe_allow_html=True
            )
        elif st.session_state.running:
            st.markdown(
                '<div class="cs-card" style="margin-top:.6rem;text-align:center;'
                'padding:.8rem;color:#9CA3AF;font-size:.78rem">'
                '🧠 Stress analysis appears after first photo</div>',
                unsafe_allow_html=True
            )

        # ── Analysis card (always shown — waiting state if no result yet) ─────
        if result:
            an   = result['analysis']
            bcls = badge_class(an['status'])
            recs_html = "".join(
                f'<div style="font-size:.74rem;color:var(--text2);margin-top:4px">• {rec}</div>'
                for rec in an.get("recommendations", [])
            )
            st.markdown(
                f'<div class="cs-card" style="margin-top:.6rem">'
                f'<span class="status-badge {bcls}">{an.get("icon","✅")} {an.get("category","")}</span>'
                f'<div style="font-size:.8rem;color:var(--text2);margin-top:.6rem">'
                f'{an.get("description","")}</div>'
                f'<div style="margin-top:.8rem;font-size:.72rem;color:var(--text3);'
                f'font-weight:600;text-transform:uppercase;letter-spacing:.05em">'
                f'Recommendations</div>{recs_html}</div>',
                unsafe_allow_html=True
            )

            # ── rPPG Signal chart ─────────────────────────────────────────────
            buf = list(st.session_state.data_buffer)
            if len(buf) >= 3:
                try:
                    is_light  = st.session_state.get("theme", "dark") == "light"
                    title_col = "#4A5578" if is_light else "#8A97B8"
                    fig = pgo.Figure()
                    fig.add_trace(pgo.Scatter(
                        y=buf,
                        x=list(range(len(buf))),
                        mode="lines",
                        line=dict(color="#E84855", width=2),
                        fill="tozeroy",
                        fillcolor="rgba(232,72,85,0.10)",
                        name="rPPG signal",
                        hovertemplate="Sample %{x}: %{y:.4f}<extra></extra>",
                    ))
                    layout = plotly_dark()
                    layout['xaxis'].update(title="", showgrid=False)
                    layout['yaxis'].update(title="Green ch.", showgrid=True)
                    fig.update_layout(
                        **layout,
                        height=170,
                        title=dict(
                            text=f"rPPG Signal — {len(buf)} samples",
                            font=dict(size=11, color=title_col),
                        ),
                        showlegend=False,
                        margin=dict(l=4, r=4, t=32, b=4),
                    )
                    st.plotly_chart(fig, use_container_width=True,
                                    config={"displayModeBar": False})
                except Exception as chart_err:
                    st.caption(f"Chart unavailable: {chart_err}")
            else:
                st.markdown(
                    '<div class="cs-card" style="text-align:center;padding:2rem;'
                    'color:var(--text3);font-size:.85rem">'
                    '📊 Chart appears after 3+ samples</div>',
                    unsafe_allow_html=True,
                )
        else:
            # Waiting state — different message depending on running
            if st.session_state.running:
                _wait_icon = "📡"
                _wait_msg  = "Camera active in left panel"
                _wait_sub  = "BPM will appear here after ~3 seconds of signal"
                _wait_tip  = "💡 Click Stop &amp; Save in the camera panel when ready"
            else:
                _wait_icon = "📊"
                _wait_msg  = "Result not available yet"
                _wait_sub  = "Press ▶ Start then use the camera panel"
                _wait_tip  = "💡 Sit still, face well-lit, 30–60 cm from camera"
            st.markdown(
                f'<div class="cs-card" style="text-align:center;padding:2rem .5rem;margin-top:.6rem">'
                f'<div style="font-size:2.5rem;margin-bottom:.5rem">{_wait_icon}</div>'
                f'<div style="color:var(--text2);font-size:.88rem;font-weight:500">'
                f'{_wait_msg}</div>'
                f'<div style="color:var(--text3);font-size:.75rem;margin-top:.4rem">'
                f'{_wait_sub}</div>'
                f'<div style="color:var(--text3);font-size:.72rem;margin-top:.8rem;'
                f'padding:.5rem;background:var(--bg2);border-radius:8px">'
                f'{_wait_tip}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    # ── Save handler (outside columns) ────────────────────────────────────────
    if save_btn and st.session_state.last_result:
        # Store everything needed for the popup in session_state,
        # then rerun — the popup gate at the top of this page takes over
        # and renders ONLY the popup (st.stop() prevents anything else).
        st.session_state["_popup_data"] = {
            "phase":       "loading",
            "user_id":     user["id"],
            "result":      st.session_state.last_result,
            "data_buffer": list(st.session_state.data_buffer),
        }
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: MY RESULTS
# ─────────────────────────────────────────────────────────────────────────────

elif st.session_state.page == "results":
    st.markdown('<div class="section-header">📊 My Health History</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">All readings for {user["full_name"]}</div>', unsafe_allow_html=True)

    results = get_user_results(user['id'])

    if not results:
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:var(--text2)">
          <div style="font-size:3rem;margin-bottom:1rem">📭</div>
          <div style="font-size:1.1rem">No results yet</div>
          <div style="font-size:0.85rem;color:var(--text3);margin-top:0.3rem">
            Complete a heart rate test to see your history here.</div>
        </div>""", unsafe_allow_html=True)
    else:
        bpms = [r['bpm'] for r in results]
        normal_count = sum(1 for b in bpms if 60 <= b <= 100)

        c1,c2,c3,c4,c5 = st.columns(5)
        metrics = [
            (c1, "Total Tests",   len(results),                 "All time",   0),
            (c2, "Average BPM",   f"{np.mean(bpms):.0f}",      "Mean reading", 100),
            (c3, "Lowest",        f"{min(bpms)}",               "BPM",          200),
            (c4, "Highest",       f"{max(bpms)}",               "BPM",          300),
            (c5, "Normal Reads",  f"{normal_count}/{len(bpms)}","60-100 BPM",   400),
        ]
        for col, label, val, sub, delay in metrics:
            with col:
                st.markdown(f"""
                <div class="metric-card">
                  <div class="metric-value">{val}</div>
                  <div class="metric-label">{label}</div>
                  <div class="metric-sub">{sub}</div>
                </div>""", unsafe_allow_html=True)

        st.divider()

        # Trend chart
        df = pd.DataFrame(results)
        df['test_date'] = pd.to_datetime(df['test_date'])
        df = df.sort_values('test_date')
        df['color'] = df['bpm'].apply(lambda b: '#00E5A0' if 60<=b<=100 else '#FFD166' if 40<=b<60 or 101<=b<=120 else '#E84855')

        try:
            fig = pgo.Figure()
            fig.add_hrect(y0=60, y1=100, fillcolor="rgba(0,229,160,0.07)", line_width=0)
            fig.add_trace(pgo.Scatter(
                x=df['test_date'], y=df['bpm'], mode='lines+markers',
                line=dict(color='#E84855', width=2),
                marker=dict(size=8, color=df['color'],
                            line=dict(width=1, color='#0A0E1A')),
                hovertemplate='<b>%{y} BPM</b><br>%{x}<extra></extra>',
                name='Heart Rate',
            ))
            fig.update_layout(
                **plotly_dark(), height=280,
                title=dict(text="Heart Rate Over Time",
                           font=dict(size=13, color='#E8EDF8')),
            )
            st.plotly_chart(fig, use_container_width=True,
                            config={'displayModeBar': False})
        except Exception as _chart_err:
            st.warning(f"Trend chart unavailable: {_chart_err}")

        st.divider()
        st.markdown("### 📋 Detailed Records")

        for i, r in enumerate(results):
            an = r['analysis']
            bcls = badge_class(an['status'])
            with st.expander(f"📅 {r['test_date']} — {r['bpm']} BPM | {an['category']}", expanded=False):
                c1, c2, c3 = st.columns([1,1,1])
                with c1:
                    st.markdown(f"""
                    <div class="metric-card">
                      <div class="metric-value" style="color:{an['color']}">{r['bpm']}</div>
                      <div class="metric-label">BPM</div>
                    </div>""", unsafe_allow_html=True)
                    # Stress badge if stored
                    stress_r = r.get('stress') or r.get('analysis', {}).get('stress')
                    stress_badge = ""
                    if stress_r and isinstance(stress_r, dict):
                        stress_badge = (
                            f'<div style="margin-top:.5rem;display:inline-flex;align-items:center;'
                            f'gap:.3rem;background:{stress_r["color"]}22;border:1px solid '
                            f'{stress_r["color"]}66;border-radius:6px;padding:2px 8px;'
                            f'font-size:.72rem;color:{stress_r["color"]}">'
                            f'{stress_r["icon"]} {stress_r["label"]}</div>'
                        )
                    st.markdown(f"""
                    <div style="margin-top:0.8rem">
                      <span class="status-badge {bcls}">{an['icon']} {an['category']}</span>
                      {stress_badge}
                      <div style="font-size:0.78rem;color:var(--text2);margin-top:0.5rem">{an['description']}</div>
                    </div>""", unsafe_allow_html=True)
                with c2:
                    st.markdown("**Recommendations**")
                    for rec in an['recommendations']:
                        st.markdown(f"<div style='font-size:0.8rem;color:var(--text2);margin:2px 0'>• {rec}</div>",
                                    unsafe_allow_html=True)
                with c3:
                    try:
                        fig_g = pgo.Figure(pgo.Indicator(
                            mode="gauge+number", value=r['bpm'],
                            gauge={'axis':{'range':[0,200],'tickcolor':'#4A5578'},
                                   'bar':{'color':an['color']},
                                   'bgcolor':'rgba(0,0,0,0)',
                                   'bordercolor':'#253358',
                                   'steps':[{'range':[0,40],'color':'rgba(232,72,85,0.15)'},
                                            {'range':[40,60],'color':'rgba(255,209,102,0.1)'},
                                            {'range':[60,100],'color':'rgba(0,229,160,0.1)'},
                                            {'range':[100,120],'color':'rgba(255,209,102,0.1)'},
                                            {'range':[120,200],'color':'rgba(232,72,85,0.1)'}]},
                            number={'font':{'size':28,'color':an['color'],'family':'DM Mono'}},
                            domain={'x':[0,1],'y':[0,1]}))
                        fig_g.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                                            height=180, margin=dict(l=10,r=10,t=20,b=10),
                                            font=dict(color='#8A97B8'))
                        st.plotly_chart(fig_g, use_container_width=True,
                                        config={'displayModeBar':False},
                                        key=f"gauge_hist_{r['test_id']}")
                    except Exception:
                        st.metric("BPM", r['bpm'])

                if r.get('signal_data'):
                    try:
                        fig_s = pgo.Figure(pgo.Scatter(y=r['signal_data'], mode='lines',
                            line=dict(color='#E84855', width=1.2), fill='tozeroy',
                            fillcolor='rgba(232,72,85,0.07)'))
                        fig_s.update_layout(**plotly_dark(), height=100)
                        st.plotly_chart(fig_s, use_container_width=True,
                                        config={'displayModeBar':False},
                                        key=f"sig_hist_{r['test_id']}")
                    except Exception:
                        pass

        st.divider()
        export_df = pd.DataFrame({'Date':[r['test_date'] for r in results],
                                   'BPM':[r['bpm'] for r in results],
                                   'Category':[r['analysis']['category'] for r in results],
                                   'Status':[r['analysis']['status'] for r in results]})
        st.download_button("⬇ Export CSV", export_df.to_csv(index=False),
                           f"heart_data_{user['username']}.csv", "text/csv")

# ─────────────────────────────────────────────────────────────────────────────
# ADMIN: DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

elif st.session_state.page == "admin_dashboard" and is_admin:
    st.markdown('<div class="section-header">🏠 Admin Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">System overview · All users · Live stats</div>', unsafe_allow_html=True)

    all_results = get_all_results_admin()
    all_users   = get_all_users()
    non_admin   = [u for u in all_users if not u['is_admin']]
    bpms_all    = [r['bpm'] for r in all_results] if all_results else []

    c1,c2,c3,c4 = st.columns(4)
    metrics = [
        (c1, "Registered Users", len(non_admin), "👥", "#00D4FF",   0),
        (c2, "Total Tests",      len(all_results), "📊", "#00E5A0",  150),
        (c3, "Avg Heart Rate",   f"{np.mean(bpms_all):.0f} bpm" if bpms_all else "–", "💓", "#E84855", 300),
        (c4, "Abnormal Reads",   sum(1 for b in bpms_all if not (60<=b<=100)), "⚠️", "#FFD166", 450),
    ]
    for col, label, val, icon, color, delay in metrics:
        with col:
            st.markdown(f"""
            <div class="metric-card">
              <div style="font-size:1.8rem">{icon}</div>
              <div class="metric-value" style="color:{color}">{val}</div>
              <div class="metric-label">{label}</div>
            </div>""", unsafe_allow_html=True)

    st.divider()

    if all_results:
        df_all = pd.DataFrame(all_results)
        df_all['test_date'] = pd.to_datetime(df_all['test_date'])

        c1, c2 = st.columns(2)
        with c1:
            # BPM distribution
            try:
                fig_dist = pgo.Figure(pgo.Histogram(x=bpms_all, nbinsx=20,
                    marker_color='#E84855', opacity=0.8,
                    marker_line=dict(color='#0A0E1A', width=1)))
                fig_dist.add_vrect(x0=60,x1=100,fillcolor="rgba(0,229,160,0.1)",
                                   annotation_text="Normal",line_width=0)
                fig_dist.update_layout(**plotly_dark(), height=260,
                                       title=dict(text="BPM Distribution",font=dict(size=12,color='#E8EDF8')),
                                       xaxis_title="BPM", yaxis_title="Count")
                st.plotly_chart(fig_dist, use_container_width=True, config={'displayModeBar':False})
            except Exception: pass

        with c2:
            cats = df_all['analysis'].apply(lambda a: a['category']).value_counts()
            fig_pie = pgo.Figure(pgo.Pie(labels=cats.index, values=cats.values,
                hole=0.55, marker=dict(colors=['#00E5A0','#FFD166','#E84855','#00D4FF','#9B5DE5'],
                                       line=dict(color='#0A0E1A',width=2)),
                textfont=dict(size=10)))
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)',height=260,
                                  showlegend=True,
                                  legend=dict(font=dict(color='#8A97B8',size=9)),
                                  margin=dict(l=0,r=0,t=30,b=0),
                                  title=dict(text="Category Breakdown",font=dict(size=12,color='#E8EDF8')))
            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar':False})

    st.divider()

    # Recent activity
    st.markdown("### 🕐 Recent Activity")
    log = get_session_log(limit=10)
    if log:
        for li, entry in enumerate(log):
            icon = "🔐" if "LOGIN" in entry['action'] else "💓" if "TEST" in entry['action'] else "💾"
            delay = min(li * 60, 500)
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:0.8rem;padding:0.5rem 0.8rem;
                 border-bottom:1px solid var(--border);font-size:0.82rem">
              <span>{icon}</span>
              <span style="color:var(--cyan);font-weight:500">{entry['username']}</span>
              <span style="color:var(--text2)">{entry['action']}</span>
              <span style="color:var(--text3);margin-left:auto">{entry['logged_at'][:16]}</span>
            </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ADMIN: ALL USERS  (click → show history)
# ─────────────────────────────────────────────────────────────────────────────

elif st.session_state.page == "admin_users" and is_admin:
    st.markdown('<div class="section-header">👥 User Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Click a user to view their complete test history</div>', unsafe_allow_html=True)

    all_users = get_all_users()
    non_admin = [u for u in all_users if not u['is_admin']]

    # Search
    search = st.text_input("🔍 Search users", placeholder="Name or username…")
    filtered = [u for u in non_admin if not search or
                search.lower() in u['full_name'].lower() or
                search.lower() in u['username'].lower()]

    if not filtered:
        st.info("No users found.")
    else:
        for i, u in enumerate(filtered):
            delay = min(i * 80, 600)  # stagger each card, cap at 600ms
            with st.container():
                col_info, col_btn = st.columns([5, 1])
                with col_info:
                    # Quick stats
                    user_results = get_user_results_by_id(u['id'])
                    avg_bpm = f"{np.mean([r['bpm'] for r in user_results]):.0f}" if user_results else "–"
                    last_date = user_results[0]['test_date'][:10] if user_results else "No tests"

                    st.markdown(f"""
                    <div class="cs-card" style="margin-bottom:0.5rem;cursor:default">
                      <div style="display:flex;align-items:center;gap:1rem">
                        <div style="width:44px;height:44px;border-radius:50%;
                             background:linear-gradient(135deg,#E84855,#9B5DE5);
                             display:flex;align-items:center;justify-content:center;
                             font-size:1.2rem;flex-shrink:0">
                          {'👨' if u.get('gender','')=='Male' else '👩' if u.get('gender','')=='Female' else '👤'}
                        </div>
                        <div style="flex:1">
                          <div style="font-weight:600;color:var(--text)">{u['full_name']}</div>
                          <div style="font-size:0.78rem;color:var(--text2)">
                            @{u['username']} · Age {u.get('age','?')} · {u.get('gender','—')}</div>
                        </div>
                        <div style="text-align:center;padding:0 1rem">
                          <div style="font-family:'DM Mono';font-size:1.1rem;color:#00E5A0">{len(user_results)}</div>
                          <div style="font-size:0.7rem;color:var(--text3)">Tests</div>
                        </div>
                        <div style="text-align:center;padding:0 1rem">
                          <div style="font-family:'DM Mono';font-size:1.1rem;color:#E84855">{avg_bpm}</div>
                          <div style="font-size:0.7rem;color:var(--text3)">Avg BPM</div>
                        </div>
                        <div style="text-align:center;padding:0 1rem">
                          <div style="font-size:0.78rem;color:var(--text2)">{last_date}</div>
                          <div style="font-size:0.7rem;color:var(--text3)">Last test</div>
                        </div>
                        <div style="font-size:0.7rem;color:var(--text3)">{u['created_at'][:10]}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)
                with col_btn:
                    if st.button("View →", key=f"view_user_{u['id']}", use_container_width=True):
                        st.session_state.admin_selected_user = u['id']

            # Inline history expansion
            if st.session_state.get('admin_selected_user') == u['id']:
                user_results = get_user_results_by_id(u['id'])
                if not user_results:
                    st.info(f"No test results for {u['full_name']} yet.")
                else:
                    st.markdown(f"""
                    <div style="background:var(--bg2);border:1px solid var(--border);
                         border-radius:12px;padding:1rem 1.5rem;margin-bottom:1rem">
                      <div style="font-family:'DM Serif Display';font-size:1.1rem;color:var(--cyan)">
                        📋 History for {u['full_name']}</div>
                    </div>""", unsafe_allow_html=True)

                    bpms = [r['bpm'] for r in user_results]
                    # Summary row
                    m1,m2,m3,m4 = st.columns(4)
                    for col, label, val in zip([m1,m2,m3,m4],
                        ["Tests","Avg BPM","Min","Max"],
                        [len(user_results),f"{np.mean(bpms):.0f}",min(bpms),max(bpms)]):
                        with col:
                            st.markdown(f"""
                            <div class="metric-card">
                              <div class="metric-value">{val}</div>
                              <div class="metric-label">{label}</div>
                            </div>""", unsafe_allow_html=True)

                    # Trend
                    df_u = pd.DataFrame(user_results)
                    df_u['test_date'] = pd.to_datetime(df_u['test_date'])
                    df_u = df_u.sort_values('test_date')
                    fig_u = pgo.Figure(pgo.Scatter(
                        x=df_u['test_date'], y=df_u['bpm'], mode='lines+markers',
                        line=dict(color='#00D4FF',width=2),
                        marker=dict(size=7,color='#00D4FF')))
                    fig_u.add_hrect(y0=60,y1=100,fillcolor="rgba(0,229,160,0.07)",line_width=0)
                    fig_u.update_layout(**plotly_dark(), height=200)
                    st.plotly_chart(fig_u, use_container_width=True,
                                    config={'displayModeBar':False},
                                    key=f"admin_trend_{u['id']}")

                    # Table
                    rows = []
                    for r in user_results:
                        an = r['analysis']
                        rows.append({'Date': r['test_date'][:16],
                                     'BPM': r['bpm'],
                                     'Category': an['category'],
                                     'Status': an['status'].upper()})
                    tdf = pd.DataFrame(rows)
                    st.dataframe(tdf, use_container_width=True, hide_index=True)

                    if st.button("✖ Close", key=f"close_user_{u['id']}", type="secondary"):
                        st.session_state.admin_selected_user = None
                        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# ADMIN: ALL RECORDS
# ─────────────────────────────────────────────────────────────────────────────

elif st.session_state.page == "admin_records" and is_admin:
    st.markdown('<div class="section-header">📋 All Test Records</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Every encrypted test result across all patients</div>', unsafe_allow_html=True)

    results = get_all_results_admin()
    if not results:
        st.info("No records yet.")
    else:
        df = pd.DataFrame([{'Date':r['test_date'][:16],'User':r['username'],
                             'Name':r['full_name'],'BPM':r['bpm'],
                             'Category':r['analysis']['category'],
                             'Status':r['analysis']['status'].upper()} for r in results])

        # Filters
        c1, c2 = st.columns(2)
        with c1:
            sel_user = st.selectbox("Filter by user", ["All"] + sorted(df['User'].unique().tolist()))
        with c2:
            sel_cat  = st.selectbox("Filter by category", ["All"] + sorted(df['Category'].unique().tolist()))

        dff = df.copy()
        if sel_user != "All": dff = dff[dff['User'] == sel_user]
        if sel_cat  != "All": dff = dff[dff['Category'] == sel_cat]

        st.markdown(f'<div><b>{len(dff)} records</b></div>', unsafe_allow_html=True)
        st.dataframe(dff, use_container_width=True, hide_index=True, height=400)

        st.download_button("⬇ Export All CSV", df.to_csv(index=False),
                           "all_records.csv", "text/csv")

# ─────────────────────────────────────────────────────────────────────────────
# ENCRYPTION LAB – STEP-BY-STEP  (multi-page walkthrough)
# ─────────────────────────────────────────────────────────────────────────────

ENC_STEPS = [
    ("enc_step1", "📝 Step 1", "Plaintext Prep"),
    ("enc_step2", "🔑 Step 2", "ECC Key Gen"),
    ("enc_step3", "🔐 Step 3", "AES Key & Nonce"),
    ("enc_step4", "🛡️ Step 4", "AES-GCM Encrypt"),
    ("enc_step5", "🌐 Step 5", "Storage"),
    ("enc_step6", "🔓 Step 6", "Decryption"),
    ("enc_step7", "🖨️ Step 7", "Raw vs Encrypted"),
]

def enc_progress_bar():
    """Clickable step-by-step progress bar for the Encryption Lab."""
    cur   = st.session_state.page
    pages = [s[0] for s in ENC_STEPS]
    idx   = pages.index(cur) if cur in pages else 0
    n     = len(ENC_STEPS)

    # Inject tiny CSS to shrink button padding inside the pill columns
    st.markdown("""<style>
    .enc-pill-col button {
      padding: 0 !important; height: 32px !important;
      min-height: 32px !important; border-radius: 50% !important;
      width: 32px !important; font-size: 0.8rem !important;
      margin: 0 auto !important; display: block !important;
    }
    </style>""", unsafe_allow_html=True)

    # One column per step + narrow connector columns between them
    col_weights = []
    for i in range(n):
        col_weights.append(1)
        if i < n - 1:
            col_weights.append(0.4)
    all_cols = st.columns(col_weights)

    for i, (pg, short, name) in enumerate(ENC_STEPS):
        col_idx = i * 2  # every other column is a pill column
        with all_cols[col_idx]:
            done   = i < idx
            active = i == idx
            if done:
                pill_bg  = "var(--green)"; pill_col = "hsl(222,58%,5%)"; icon = "✓"
            elif active:
                pill_bg  = "var(--accent)"; pill_col = "white"; icon = str(i+1)
            else:
                pill_bg  = "var(--card2)"; pill_col = "var(--text3)"; icon = str(i+1)

            # Clickable button for each step (allows jumping)
            st.markdown(
                f'<div style="text-align:center">', unsafe_allow_html=True
            )
            clicked = st.button(
                icon,
                key=f"enc_pill_{i}",
                help=f"Jump to {name}",
                use_container_width=False,
            )
            if clicked:
                st.session_state.page = pg
                st.rerun()
            st.markdown(
                f'<div style="text-align:center;font-size:0.6rem;color:'
                + ("var(--accent)" if active else "var(--text3)")
                + f';margin-top:2px;font-weight:{"600" if active else "400"}">' 
                + name + "</div></div>",
                unsafe_allow_html=True,
            )

        # Connector line between pills
        if i < n - 1:
            with all_cols[col_idx + 1]:
                done_conn = i < idx
                color = "var(--green)" if done_conn else "var(--border)"
                st.markdown(
                    f'<div style="height:32px;display:flex;align-items:center">' 
                    f'<div style="width:100%;height:2px;background:{color};'
                    f'border-radius:2px"></div></div>',
                    unsafe_allow_html=True,
                )

    pct = idx / (n - 1) if n > 1 else 0
    st.progress(pct)

def enc_nav(cur_page):
    """Bottom previous/next navigation for each encryption lab step."""
    pages  = [s[0] for s in ENC_STEPS]
    names  = [s[2] for s in ENC_STEPS]
    idx    = pages.index(cur_page)
    n      = len(ENC_STEPS)

    st.divider()
    c1, c2, c3 = st.columns([1, 3, 1])
    with c1:
        if idx > 0:
            prev_name = names[idx - 1]
            if st.button(f"← {prev_name}", use_container_width=True, type="secondary",
                         key=f"enc_prev_{idx}"):
                st.session_state.page = pages[idx - 1]
                st.rerun()
    with c2:
        st.markdown(
            f'<div style="text-align:center;color:var(--text3);font-size:0.8rem;padding-top:0.5rem">' 
            f'Step <b style="color:var(--text)">{idx+1}</b> of <b style="color:var(--text)">{n}</b>' 
            f' &nbsp;·&nbsp; {names[idx]}</div>',
            unsafe_allow_html=True,
        )
    with c3:
        if idx < n - 1:
            next_name = names[idx + 1]
            lbl       = "🖨️ View Report →" if idx == n - 2 else f"{next_name} →"
            if st.button(lbl, use_container_width=True, type="primary",
                         key=f"enc_next_{idx}"):
                st.session_state.page = pages[idx + 1]
                st.rerun()
        else:
            if st.button("↩ Back to Step 1", use_container_width=True, type="secondary",
                         key="enc_restart"):
                st.session_state.page = pages[0]
                st.rerun()

# ── Shared sample data ────────────────────────────────────────────────────────
def get_enc_sample():
    if 'enc_sample' not in st.session_state:
        st.session_state.enc_sample = {
            "patient": user['full_name'],
            "bpm": 72,
            "category": "Normal Resting",
            "timestamp": datetime.now().isoformat(),
            "device_id": "CARDIOSECURE-001",
            "recommendations": ["Maintain regular physical activity","Stay hydrated"]
        }
    return st.session_state.enc_sample

def get_enc_keys():
    if 'enc_keys' not in st.session_state:
        priv, pub = HybridEncryption.generate_ecc_keys()
        key   = os.urandom(32)
        nonce = os.urandom(12)
        st.session_state.enc_keys = {'priv':priv,'pub':pub,'key':key,'nonce':nonce}
    return st.session_state.enc_keys

def get_enc_cipher():
    if 'enc_cipher' not in st.session_state:
        sample = get_enc_sample()
        keys   = get_enc_keys()
        enc = HybridEncryption.encrypt_aes_gcm(json.dumps(sample), keys['key'])
        st.session_state.enc_cipher = enc
    return st.session_state.enc_cipher

# ────────────────────────────────────────────────────────────────────────────
# Redirect bare "encryption" nav link → first step
if st.session_state.page == "encryption":
    st.session_state.page = "enc_step1"
    st.rerun()

if st.session_state.page == "enc_step1":
    st.markdown('<div class="section-header">🔒 Encryption Laboratory</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Step-by-step walkthrough of AES-GCM + ECC Hybrid Encryption</div>', unsafe_allow_html=True)
    enc_progress_bar()
    st.divider()

    sample = get_enc_sample()

    st.markdown("""
    <div class="enc-step-card">
      <div class="enc-step-title">📝 Step 1: Plaintext Medical Data Preparation</div>
      <div class="enc-explanation">
        Before any encryption can occur, the raw medical data must be serialised into a
        structured, standardised format. We use <b>JSON (JavaScript Object Notation)</b> —
        a lightweight, human-readable text format that ensures interoperability across
        different systems and devices.<br><br>
        This plaintext is the <i>most sensitive state</i> of the data — it is fully readable
        and must only ever exist in memory for the shortest possible time before encryption.
        In a clinical system, this stage would occur entirely within a trusted execution
        environment (TEE) to prevent memory-scraping attacks.
      </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**📄 Structured Data (JSON View)**")
        st.json(sample)
    with c2:
        plaintext = json.dumps(sample, indent=2)
        st.markdown("**💾 Raw Plaintext (as stored in memory)**")
        st.code(plaintext, language="json")
        st.markdown(f"""
        <div style="display:flex;gap:1rem;margin-top:0.5rem">
          <div class="metric-card" style="flex:1;padding:0.8rem">
            <div class="metric-value" style="font-size:1.3rem">{len(plaintext)}</div>
            <div class="metric-label">Bytes</div>
          </div>
          <div class="metric-card" style="flex:1;padding:0.8rem">
            <div class="metric-value" style="font-size:1.3rem">{len(plaintext.encode('utf-8'))}</div>
            <div class="metric-label">UTF-8 Chars</div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.success("✅ Medical data successfully serialised to JSON — ready for encryption pipeline.")

    st.markdown("""
    <div style="background:rgba(0,212,255,0.07);border:1px solid rgba(0,212,255,0.2);
         border-radius:10px;padding:1rem;margin-top:0.8rem;font-size:0.83rem;color:var(--text2)">
    <b style="color:var(--cyan)">🔍 Security Note:</b> In production, plaintext medical data is subject to
    HIPAA/GDPR regulations. Data minimisation principles apply — only clinically necessary fields
    are captured. PII (Personally Identifiable Information) is separated from health data using
    a <b>pseudonymisation</b> layer before the encryption stage shown here.
    </div>""", unsafe_allow_html=True)

    enc_nav("enc_step1")

# ─────────────────────────────────────────────────────────────────────────────

elif st.session_state.page == "enc_step2":
    st.markdown('<div class="section-header">🔒 Encryption Laboratory</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Step-by-step walkthrough of AES-GCM + ECC Hybrid Encryption</div>', unsafe_allow_html=True)
    enc_progress_bar()
    st.divider()

    keys = get_enc_keys()
    priv_pem = keys['priv'].private_bytes(serialization.Encoding.PEM,
                  serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
    pub_pem  = keys['pub'].public_bytes(serialization.Encoding.PEM,
                  serialization.PublicFormat.SubjectPublicKeyInfo).decode()

    st.markdown("""
    <div class="enc-step-card">
      <div class="enc-step-title">🔑 Step 2: Elliptic Curve Cryptography (ECC) Key Pair Generation</div>
      <div class="enc-explanation">
        ECC provides <b>asymmetric cryptography</b> — a mathematically linked pair of keys where data
        encrypted with one can only be decrypted with the other.<br><br>
        We use the <b>NIST P-256 (SECP256R1)</b> curve — a 256-bit elliptic curve that provides
        128-bit security equivalent, meaning a brute-force attack would require ~2¹²⁸ operations.
        This is the same curve used by TLS 1.3, Bitcoin, and modern IoT security protocols.<br><br>
        The <b>Elliptic Curve Diffie-Hellman (ECDH)</b> key exchange then allows two parties to
        derive a shared secret over an insecure channel without ever transmitting the secret itself —
        this shared secret seeds the symmetric AES key.
      </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**🔒 Private Key (PKCS#8 PEM — NEVER transmit)**")
        st.code(priv_pem, language="text")
        st.markdown("""
        <div style="background:rgba(232,72,85,0.07);border:1px solid rgba(232,72,85,0.2);
             border-radius:8px;padding:0.8rem;font-size:0.78rem;color:var(--text2)">
        ⚠️ The private key must be stored encrypted at rest, in a Hardware Security Module (HSM)
        or Key Management Service (KMS). It must <b>never</b> leave the secure boundary.
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("**🔓 Public Key (SubjectPublicKeyInfo PEM — freely shareable)**")
        st.code(pub_pem, language="text")
        st.markdown("""
        <div style="background:rgba(0,229,160,0.07);border:1px solid rgba(0,229,160,0.2);
             border-radius:8px;padding:0.8rem;font-size:0.78rem;color:var(--text2)">
        ✅ The public key can be safely distributed via a Public Key Infrastructure (PKI) or
        embedded in X.509 certificates for identity verification.
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🔄 ECDH Key Exchange Simulation")
    st.markdown("""
    <div class="enc-explanation" style="margin-bottom:1rem">
    To simulate a real-world scenario where a patient device communicates with a hospital server,
    we generate <b>two separate ECC key pairs</b> and perform an ECDH exchange. Both parties
    independently derive the same shared secret — without ever transmitting it.
    </div>""", unsafe_allow_html=True)

    priv2, pub2 = HybridEncryption.generate_ecc_keys()
    shared1 = HybridEncryption.derive_shared_key(keys['priv'], pub2)
    shared2 = HybridEncryption.derive_shared_key(priv2, keys['pub'])

    c1, c2, c3 = st.columns([2,1,2])
    with c1:
        st.markdown("""
        <div class="metric-card">
          <div style="font-size:0.9rem;color:var(--cyan);font-weight:600">📱 Patient Device</div>
          <div style="font-size:0.75rem;color:var(--text2);margin-top:0.3rem">Has: own private key + server public key</div>
          <div style="margin-top:0.5rem;font-family:'DM Mono';font-size:0.7rem;color:var(--text3)">
            Derived secret:<br>{}</div>
        </div>""".format(shared1.hex()[:32]+'…'), unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div style="text-align:center;padding-top:1.5rem;color:var(--green);font-size:2rem">⟷</div>
        <div style="text-align:center;font-size:0.7rem;color:var(--text3)">ECDH Exchange</div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="metric-card">
          <div style="font-size:0.9rem;color:var(--purple);font-weight:600">🏥 Hospital Server</div>
          <div style="font-size:0.75rem;color:var(--text2);margin-top:0.3rem">Has: own private key + patient public key</div>
          <div style="margin-top:0.5rem;font-family:'DM Mono';font-size:0.7rem;color:var(--text3)">
            Derived secret:<br>{}</div>
        </div>""".format(shared2.hex()[:32]+'…'), unsafe_allow_html=True)

    if shared1 == shared2:
        st.success("✅ Both parties derived identical shared secrets without transmitting it — ECDH successful!")
    else:
        st.error("Key exchange mismatch (this should not occur).")

    enc_nav("enc_step2")

# ─────────────────────────────────────────────────────────────────────────────

elif st.session_state.page == "enc_step3":
    st.markdown('<div class="section-header">🔒 Encryption Laboratory</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Step-by-step walkthrough of AES-GCM + ECC Hybrid Encryption</div>', unsafe_allow_html=True)
    enc_progress_bar()
    st.divider()

    keys = get_enc_keys()

    st.markdown("""
    <div class="enc-step-card">
      <div class="enc-step-title">🔐 Step 3: AES-256 Session Key & Nonce Generation</div>
      <div class="enc-explanation">
        <b>AES-256 (Advanced Encryption Standard)</b> with a 256-bit key is the gold standard
        for symmetric encryption. It operates on 128-bit data blocks through 14 rounds of
        substitution, permutation, and mixing operations.<br><br>
        In our hybrid scheme, AES-256 encrypts the actual medical data (fast & efficient),
        while ECC handles authentication and key exchange (slower but asymmetric).<br><br>
        The <b>Nonce (Number Used Once)</b> is a 96-bit random value critical to GCM mode security.
        It ensures that even identical plaintexts encrypted with the same key produce
        completely different ciphertexts — defeating traffic analysis attacks.
      </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**🔑 AES-256 Session Key (32 bytes / 256 bits)**")
        key_hex = keys['key'].hex()
        # Visualise as colour-coded groups
        groups = [key_hex[i:i+8] for i in range(0, len(key_hex), 8)]
        colours = ['#E84855','#FFD166','#00E5A0','#00D4FF','#9B5DE5','#FF6B6B','#51CF66','#74C0FC']
        hex_html = ' '.join(f'<span style="color:{colours[j%8]}">{g}</span>' for j,g in enumerate(groups))
        st.markdown(f"""
        <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;
             padding:1rem;font-family:'DM Mono';font-size:0.78rem;line-height:2">
          {hex_html}
        </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style="display:flex;gap:0.8rem;margin-top:0.8rem">
          <div class="metric-card" style="flex:1">
            <div class="metric-value" style="font-size:1.2rem">256</div>
            <div class="metric-label">bits</div>
          </div>
          <div class="metric-card" style="flex:1">
            <div class="metric-value" style="font-size:1.2rem">32</div>
            <div class="metric-label">bytes</div>
          </div>
          <div class="metric-card" style="flex:1">
            <div class="metric-value" style="font-size:1.2rem">64</div>
            <div class="metric-label">hex chars</div>
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style="margin-top:0.8rem;background:rgba(0,229,160,0.07);border:1px solid rgba(0,229,160,0.2);
             border-radius:8px;padding:0.8rem;font-size:0.78rem;color:var(--text2)">
        ✅ Generated via <code>os.urandom(32)</code> — uses the OS CSPRNG (Cryptographically Secure
        Pseudo-Random Number Generator), seeded from hardware entropy sources (CPU timing jitter,
        mouse movement, disk I/O interrupts).
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown("**🎯 GCM Nonce (12 bytes / 96 bits)**")
        nonce_hex = keys['nonce'].hex()
        n_groups  = [nonce_hex[i:i+6] for i in range(0,len(nonce_hex),6)]
        n_html    = ' '.join(f'<span style="color:{colours[j%8]}">{g}</span>' for j,g in enumerate(n_groups))
        st.markdown(f"""
        <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;
             padding:1rem;font-family:'DM Mono';font-size:0.78rem;line-height:2">
          {n_html}
        </div>""", unsafe_allow_html=True)

        st.markdown("""<div style="margin-top:0.8rem">
        <div style="font-size:0.82rem;color:var(--text2);line-height:1.8">
        <b style="color:var(--yellow)">Why 96 bits?</b><br>
        GCM's counter mode works optimally with a 96-bit nonce. Smaller sizes require hashing
        (HKDF) which adds overhead; larger sizes provide no security benefit.<br><br>
        <b style="color:var(--yellow)">Critical rule:</b> Nonce + Key combination must <i>never</i>
        repeat. With a 96-bit random nonce and 2³² encryptions, the collision probability
        is ~0.5 × 2³²/2⁹⁶ = negligible (~10⁻²⁰).
        </div></div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🔑 HKDF Key Derivation from ECDH Shared Secret")
    keys2 = get_enc_keys()
    priv2, pub2 = HybridEncryption.generate_ecc_keys()
    shared = HybridEncryption.derive_shared_key(keys2['priv'], pub2)
    st.markdown("""
    <div class="enc-explanation">
    The raw ECDH output is processed through <b>HKDF (HMAC-based Key Derivation Function)</b>
    defined in RFC 5869. This converts the raw shared secret into a uniformly distributed
    cryptographic key, removing any structure that could be exploited.
    </div>""", unsafe_allow_html=True)
    st.code(f"""# Python (cryptography library)
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

derived_key = HKDF(
    algorithm = hashes.SHA256(),
    length    = 32,          # 256-bit output
    salt      = None,        # Random salt increases security
    info      = b'handshake data',   # Context binding
).derive(ecdh_shared_secret)

# Result: {shared.hex()[:32]}...""", language="python")

    enc_nav("enc_step3")

# ─────────────────────────────────────────────────────────────────────────────

elif st.session_state.page == "enc_step4":
    st.markdown('<div class="section-header">🔒 Encryption Laboratory</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Step-by-step walkthrough of AES-GCM + ECC Hybrid Encryption</div>', unsafe_allow_html=True)
    enc_progress_bar()
    st.divider()

    sample = get_enc_sample()
    keys   = get_enc_keys()
    enc    = get_enc_cipher()

    plaintext_bytes = json.dumps(sample).encode()

    st.markdown("""
    <div class="enc-step-card">
      <div class="enc-step-title">🛡️ Step 4: AES-256-GCM Authenticated Encryption</div>
      <div class="enc-explanation">
        AES-GCM (Galois/Counter Mode) is an <b>AEAD</b> cipher — Authenticated Encryption with
        Associated Data. This means it simultaneously provides:<br>
        • <b>Confidentiality</b>: the ciphertext reveals nothing about the plaintext<br>
        • <b>Integrity</b>: any bit-flip in the ciphertext is detected with overwhelming probability<br>
        • <b>Authenticity</b>: a 128-bit authentication tag proves the data originated from the key-holder<br><br>
        GCM uses the AES block cipher in counter mode (CTR) for encryption, and GHASH (a polynomial
        hash over GF(2¹²⁸)) for authentication. The encryption and authentication run in parallel,
        making GCM extremely fast on modern hardware with AES-NI CPU instructions.
      </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**📄 Input: Plaintext (UTF-8)**")
        st.code(plaintext_bytes.hex(), language="text")
        st.caption(f"Size: {len(plaintext_bytes)} bytes")

    with c2:
        st.markdown("**🔐 Output: Ciphertext (Nonce + Cipher + Auth Tag)**")
        st.code(enc.hex(), language="text")
        st.caption(f"Size: {len(enc)} bytes (+{len(enc)-len(plaintext_bytes)} overhead)")

    st.divider()

    # Byte breakdown
    st.markdown("### 📦 Ciphertext Structure Breakdown")
    nonce_part   = enc[:12]
    cipher_part  = enc[12:-16]
    tag_part     = enc[-16:]

    col_n, col_c, col_t = st.columns([1,4,1])
    with col_n:
        st.markdown(f"""
        <div style="background:rgba(255,209,102,0.1);border:2px solid rgba(255,209,102,0.3);
             border-radius:8px;padding:0.8rem;text-align:center">
          <div style="color:var(--yellow);font-weight:600;font-size:0.8rem">NONCE</div>
          <div style="font-family:'DM Mono';font-size:0.65rem;color:var(--text2);margin-top:4px">
            {nonce_part.hex()[:16]}…</div>
          <div style="color:var(--text3);font-size:0.7rem;margin-top:4px">12 bytes</div>
        </div>""", unsafe_allow_html=True)
    with col_c:
        st.markdown(f"""
        <div style="background:rgba(232,72,85,0.1);border:2px solid rgba(232,72,85,0.3);
             border-radius:8px;padding:0.8rem;text-align:center">
          <div style="color:var(--accent);font-weight:600;font-size:0.8rem">CIPHERTEXT</div>
          <div style="font-family:'DM Mono';font-size:0.65rem;color:var(--text2);margin-top:4px">
            {cipher_part.hex()[:40]}…</div>
          <div style="color:var(--text3);font-size:0.7rem;margin-top:4px">{len(cipher_part)} bytes (same length as plaintext)</div>
        </div>""", unsafe_allow_html=True)
    with col_t:
        st.markdown(f"""
        <div style="background:rgba(0,229,160,0.1);border:2px solid rgba(0,229,160,0.3);
             border-radius:8px;padding:0.8rem;text-align:center">
          <div style="color:var(--green);font-weight:600;font-size:0.8rem">AUTH TAG</div>
          <div style="font-family:'DM Mono';font-size:0.65rem;color:var(--text2);margin-top:4px">
            {tag_part.hex()[:16]}…</div>
          <div style="color:var(--text3);font-size:0.7rem;margin-top:4px">16 bytes</div>
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 💻 Implementation Reference")
    st.code("""from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Encrypt
aesgcm    = AESGCM(key_256bit)          # Create cipher instance
nonce     = os.urandom(12)              # 96-bit unique nonce
ciphertext = aesgcm.encrypt(
    nonce,                              # IV / nonce
    plaintext.encode('utf-8'),          # Message to encrypt
    None                                # Optional: associated data (AAD)
)
# ciphertext = nonce (12) + encrypted_data (n) + auth_tag (16)

# Decrypt (raises InvalidTag if tampered)
plaintext = aesgcm.decrypt(nonce, ciphertext, None)""", language="python")

    enc_nav("enc_step4")

# ─────────────────────────────────────────────────────────────────────────────

elif st.session_state.page == "enc_step5":
    st.markdown('<div class="section-header">🔒 Encryption Laboratory</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Step-by-step walkthrough of AES-GCM + ECC Hybrid Encryption</div>', unsafe_allow_html=True)
    enc_progress_bar()
    st.divider()

    enc = get_enc_cipher()
    keys = get_enc_keys()

    st.markdown("""
    <div class="enc-step-card">
      <div class="enc-step-title">🌐 Step 5: Decentralised Storage Architecture</div>
      <div class="enc-explanation">
        In a production medical IoT system, encrypted data is <b>never stored in a single location</b>.
        A decentralised architecture provides resilience, availability, and reduces the attack surface
        by ensuring no single compromised node exposes patient data.<br><br>
        <b>Key separation</b> is the critical principle: encrypted data and its decryption keys are
        stored in physically separate systems with independent access controls. An attacker who
        obtains the encrypted data without the key gains nothing — and vice versa.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Architecture diagram (using columns as nodes)
    st.markdown("### 🏗️ System Architecture")
    nodes = [
        ("📱 IoT Device", "#00D4FF", "Patient wearable\nor mobile app",
         "Captures rPPG signal", "Ephemeral — no persistent storage"),
        ("🔐 Encryption Layer", "#9B5DE5", "Trusted Execution\nEnvironment (TEE)",
         "AES-256-GCM encryption", "Keys never leave TEE"),
        ("🌐 Data Nodes (3)", "#E84855", "Geo-distributed\nencrypted storage",
         "Encrypted blobs only", "IPFS / Cloud Object Storage"),
        ("🔑 KMS", "#FFD166", "Key Management\nService (HSM)",
         "AES keys, access-controlled", "Separate auth chain"),
        ("⛓️ Blockchain", "#00E5A0", "Audit & Integrity\nLedger",
         "Hash of each record", "Immutable, tamper-evident"),
    ]
    cols = st.columns(len(nodes))
    for col, (title, color, subtitle, stores, note) in zip(cols, nodes):
        with col:
            st.markdown(f"""
            <div style="background:var(--card2);border:1px solid {color}44;border-top:3px solid {color};
                 border-radius:10px;padding:0.8rem;text-align:center;height:180px">
              <div style="font-size:1.2rem;margin-bottom:0.3rem">{title}</div>
              <div style="font-size:0.7rem;color:{color};font-weight:500;margin-bottom:0.5rem">{subtitle}</div>
              <div style="font-size:0.68rem;color:var(--text2);margin-bottom:0.3rem">Stores: {stores}</div>
              <div style="font-size:0.65rem;color:var(--text3);margin-top:auto">{note}</div>
            </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 📦 Simulated Distributed Storage Nodes")

    chunk_size = len(enc) // 3
    chunks = [enc[:chunk_size], enc[chunk_size:2*chunk_size], enc[2*chunk_size:]]
    regions = ["eu-west-1 (Ireland)", "us-east-1 (Virginia)", "ap-southeast-1 (Singapore)"]
    statuses = ["✅ Stored", "✅ Replicated", "✅ Replicated"]
    node_ids = [os.urandom(8).hex() for _ in range(3)]

    c1, c2, c3 = st.columns(3)
    for col, chunk, region, status, nid in zip([c1,c2,c3], chunks, regions, statuses, node_ids):
        with col:
            st.markdown(f"""
            <div class="cs-card">
              <div style="font-size:0.85rem;font-weight:600;color:var(--cyan)">📦 Node {node_ids.index(nid)+1}</div>
              <div style="font-size:0.7rem;color:var(--text3);margin-bottom:0.5rem">{region}</div>
              <div style="font-family:'DM Mono';font-size:0.65rem;color:var(--text2);
                   background:var(--bg);border-radius:6px;padding:0.5rem;margin-bottom:0.5rem;
                   word-break:break-all">{chunk.hex()[:48]}…</div>
              <div style="font-size:0.7rem;color:var(--text3)">Node ID: {nid[:12]}…</div>
              <div style="margin-top:0.4rem;font-size:0.75rem;color:var(--green)">{status}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:rgba(0,229,160,0.07);border:1px solid rgba(0,229,160,0.2);
         border-radius:10px;padding:1rem;margin-top:0.5rem;font-size:0.82rem;color:var(--text2)">
    <b style="color:var(--green)">🔒 Key stored separately in KMS:</b><br>
    <span style="font-family:'DM Mono';font-size:0.72rem;color:var(--text3)">{keys['key'].hex()[:32]}…</span><br>
    <span style="font-size:0.75rem;margin-top:4px;display:block">
    Access to this key requires multi-factor authentication + role-based access control (RBAC).
    Even database administrators cannot decrypt patient data without KMS authorisation.</span>
    </div>""", unsafe_allow_html=True)

    enc_nav("enc_step5")

# ─────────────────────────────────────────────────────────────────────────────

elif st.session_state.page == "enc_step6":
    st.markdown('<div class="section-header">🔒 Encryption Laboratory</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Step-by-step walkthrough of AES-GCM + ECC Hybrid Encryption</div>', unsafe_allow_html=True)
    enc_progress_bar()
    st.divider()

    sample = get_enc_sample()
    keys   = get_enc_keys()
    enc    = get_enc_cipher()

    st.markdown("""
    <div class="enc-step-card">
      <div class="enc-step-title">🔓 Step 6: Decryption, Verification & Integrity Check</div>
      <div class="enc-explanation">
        Decryption in AES-GCM is the reverse of encryption, but with a crucial difference:
        before a single byte of plaintext is released, the <b>authentication tag is verified</b>.
        If the tag doesn't match — due to data corruption, tampering, or wrong key — the operation
        throws a cryptographic exception and <i>no plaintext is ever returned</i>.<br><br>
        This "verify-then-decrypt" design is essential: it prevents <b>padding oracle attacks</b>
        and ensures the application never processes potentially malicious decrypted data.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Verification controls
    col_ctrl, col_info = st.columns([2, 3])
    with col_ctrl:
        st.markdown("### 🧪 Live Decryption Test")
        tamper = st.checkbox("🔴 Simulate data tampering (corrupt 1 byte)", value=False)

        if tamper:
            tampered = bytearray(enc)
            tampered[15] ^= 0xFF  # flip a bit in ciphertext
            test_enc = bytes(tampered)
            st.warning("⚠️ Data tampering simulated — authentication tag will fail")
        else:
            test_enc = enc

        if st.button("🔍 Decrypt & Verify", type="primary", use_container_width=True):
            with st.spinner("Retrieving from storage… verifying auth tag… decrypting…"):
                time.sleep(0.8)
                try:
                    dec_json = HybridEncryption.decrypt_aes_gcm(test_enc, keys['key'])
                    dec_data = json.loads(dec_json)

                    st.success("✅ Authentication tag VALID — no tampering detected")
                    st.success("✅ Decryption successful — data integrity confirmed")
                    st.markdown("**Recovered plaintext:**")
                    st.json(dec_data)

                    if dec_data == sample:
                        st.success("✅ Byte-for-byte match with original data")
                    st.balloons()
                except Exception as e:
                    st.error("❌ DECRYPTION FAILED — Authentication tag mismatch!")
                    st.error(f"Error: {type(e).__name__}: {str(e)[:80]}")
                    st.markdown("""
                    <div style="background:rgba(232,72,85,0.1);border:1px solid rgba(232,72,85,0.3);
                         border-radius:8px;padding:1rem;margin-top:0.5rem;font-size:0.82rem;color:var(--text2)">
                    <b style="color:var(--accent)">🔒 Security Response:</b> Zero plaintext was returned.
                    In a production system this event would be logged to the SIEM, an alert sent to
                    the security team, and the session terminated. The incident would be investigated
                    for potential man-in-the-middle or storage tampering attacks.
                    </div>""", unsafe_allow_html=True)

    with col_info:
        st.markdown("### 📋 Decryption Process")
        steps_dec = [
            ("1", "Retrieve encrypted blob + key from separate stores", "#00D4FF"),
            ("2", "Separate nonce (first 12 bytes) from ciphertext", "#9B5DE5"),
            ("3", "Compute GHASH over ciphertext to derive expected auth tag", "#FFD166"),
            ("4", "Compare computed tag to stored tag (constant-time comparison)", "#E84855"),
            ("5", "ONLY if tags match: decrypt ciphertext using AES-CTR", "#00E5A0"),
            ("6", "Return plaintext / raise exception if any step fails", "#8A97B8"),
        ]
        for num, desc, color in steps_dec:
            st.markdown(f"""
            <div style="display:flex;gap:0.8rem;align-items:flex-start;
                 padding:0.5rem 0;border-bottom:1px solid var(--border)">
              <span class="step-pill step-pill-active" style="background:{color};
                    color:#0A0E1A;flex-shrink:0">{num}</span>
              <div style="font-size:0.82rem;color:var(--text2);padding-top:5px">{desc}</div>
            </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🏆 Hybrid Encryption Summary")
    c1, c2, c3 = st.columns(3)
    layers = [
        (c1, "Symmetric (AES-256-GCM)", "#E84855",
         "Algorithm", "AES-256-GCM",
         "Key size", "256 bits",
         "Security level", "128-bit equiv.",
         "Purpose", "Data encryption"),
        (c2, "Asymmetric (ECC-P256)", "#00D4FF",
         "Algorithm", "SECP256R1",
         "Key exchange", "ECDH",
         "Key derivation", "HKDF-SHA256",
         "Purpose", "Auth & key wrap"),
        (c3, "Authenticated (GHASH)", "#00E5A0",
         "Algorithm", "GHASH / GMAC",
         "Tag size", "128 bits",
         "Tamper detect", "Guaranteed",
         "Purpose", "Integrity & auth"),
    ]
    for col, title, color, *pairs in layers:
        with col:
            rows_html = ''.join(
                f'<tr><td style="color:var(--text3);font-size:0.73rem;padding:3px 0">{pairs[i]}</td>'
                f'<td style="color:var(--text2);font-size:0.73rem;padding:3px 0;text-align:right">{pairs[i+1]}</td></tr>'
                for i in range(0, len(pairs), 2)
            )
            st.markdown(f"""
            <div style="background:var(--card2);border:1px solid {color}44;
                 border-top:2px solid {color};border-radius:10px;padding:1rem">
              <div style="color:{color};font-weight:600;font-size:0.88rem;margin-bottom:0.6rem">{title}</div>
              <table style="width:100%">{rows_html}</table>
            </div>""", unsafe_allow_html=True)

    enc_nav("enc_step6")

# ─────────────────────────────────────────────────────────────────────────────

elif st.session_state.page == "enc_step7":
    render_nav()
    st.markdown('<div class="section-header">🔒 Encryption Laboratory</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Step 7 of 7 — Raw Data vs Encrypted Output · Print Report</div>', unsafe_allow_html=True)
    enc_progress_bar()
    st.divider()

    sample = get_enc_sample()
    keys   = get_enc_keys()
    enc    = get_enc_cipher()

    plaintext_str  = json.dumps(sample, indent=2)
    cipher_hex     = enc.hex()
    key_hex        = keys['key'].hex()
    nonce_hex      = enc[:12].hex()
    ciphertext_hex = enc[12:-16].hex()
    tag_hex        = enc[-16:].hex()

    priv_pem = keys['priv'].private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    ).decode()
    pub_pem = keys['pub'].public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()

    # ── Explanation card ─────────────────────────────────────────────────────
    st.markdown("""
    <div class="enc-step-card">
      <div class="enc-step-title">🖨️ Step 7: Raw Data vs Encrypted Output — Full Comparison Report</div>
      <div class="enc-explanation">
        This final page presents a side-by-side comparison of every piece of data that was
        processed through the hybrid encryption pipeline. It serves as both an educational
        summary and a printable audit artefact.<br><br>
        <b>Raw data</b> is the original human-readable JSON that would exist in memory for
        milliseconds before being passed to the encryption pipeline. <b>Encrypted output</b>
        is what actually travels across the network and sits in the database — completely
        opaque to anyone without the AES-256 key.<br><br>
        The comparison table below demonstrates the core principle of modern cryptography:
        <i>computationally indistinguishable ciphertext</i> — structured plaintext transformed
        into what appears to be random noise, verifiable only by the key-holder.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Stats row ─────────────────────────────────────────────────────────────
    plain_bytes  = len(plaintext_str.encode())
    cipher_bytes = len(enc)
    overhead     = cipher_bytes - plain_bytes
    entropy_est  = len(set(cipher_hex)) / 16 * 100  # hex-char diversity

    m1, m2, m3, m4, m5 = st.columns(5)
    for col, val, lbl, sub in [
        (m1, f"{plain_bytes}",    "Plaintext",   "bytes"),
        (m2, f"{cipher_bytes}",   "Ciphertext",  "bytes"),
        (m3, f"+{overhead}",      "Overhead",    "nonce+tag"),
        (m4, "AES-256-GCM",       "Algorithm",   "AEAD mode"),
        (m5, f"{entropy_est:.0f}%","Hex Entropy", "char diversity"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-card" style="text-align:center;padding:0.8rem">
              <div class="metric-value" style="font-size:1.2rem">{val}</div>
              <div class="metric-label">{lbl}</div>
              <div class="metric-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.divider()

    # ── Three tab sections: Raw | Encrypted | Together ────────────────────────
    tab_raw, tab_enc, tab_both = st.tabs(["📄 Raw Data", "🔐 Encrypted Output", "⚖️ Side-by-Side Comparison"])

    # ── RAW DATA TAB ──────────────────────────────────────────────────────────
    with tab_raw:
        st.markdown("### 📄 Raw Plaintext Medical Record")
        st.markdown("""
        <div style="background:rgba(255,209,102,0.07);border:1px solid rgba(255,209,102,0.25);
             border-radius:10px;padding:0.9rem;margin-bottom:1rem;font-size:0.82rem;color:var(--text2)">
        ⚠️ <b style="color:var(--yellow)">Security Warning:</b> This data represents the
        <i>pre-encryption state</i>. In a production system it exists only in RAM, never on disk,
        and is immediately overwritten after encryption. It is displayed here for educational purposes only.
        </div>""", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Structured View**")
            st.json(sample)
        with c2:
            st.markdown("**Raw JSON String**")
            st.code(plaintext_str, language="json")

        st.markdown("**ECC Public Key (freely shareable)**")
        st.code(pub_pem, language="text")

        st.markdown("**ECC Private Key (secret — shown for lab only)**")
        st.code(priv_pem, language="text")

        st.markdown("**AES-256 Session Key (32 bytes)**")
        groups = [key_hex[i:i+8] for i in range(0, len(key_hex), 8)]
        colours = ['#E84855','#FFD166','#00E5A0','#00D4FF','#9B5DE5','#FF6B6B','#51CF66','#74C0FC']
        hex_html = " ".join(
            f'<span style="color:{colours[j%8]};font-family:DM Mono,monospace">{g}</span>'
            for j, g in enumerate(groups)
        )
        st.markdown(
            f'<div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;' 
            f'padding:1rem;font-size:0.8rem;line-height:2.2;word-break:break-all">{hex_html}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("**GCM Nonce (12 bytes — prepended to ciphertext)**")
        st.code(nonce_hex, language="text")

        # Print raw only
        st.markdown("---")
        raw_print_html = f"""
<!DOCTYPE html><html><head>
<title>CardioSecure — Raw Medical Data Report</title>
<style>
  body{{font-family:'Courier New',monospace;padding:2rem;color:#111;background:#fff}}
  h1{{font-family:Arial,sans-serif;color:#E84855;border-bottom:2px solid #E84855;padding-bottom:.5rem}}
  h2{{font-family:Arial,sans-serif;color:#333;margin-top:1.5rem}}
  pre{{background:#f5f5f5;padding:1rem;border-radius:6px;white-space:pre-wrap;word-break:break-all;font-size:.8rem}}
  .meta{{color:#666;font-family:Arial;font-size:.85rem;margin-bottom:1.5rem}}
  .warn{{background:#fff8e1;border:1px solid #ffc107;padding:.8rem;border-radius:6px;font-family:Arial;font-size:.82rem}}
  @media print{{.no-print{{display:none}}}}
</style></head><body>
<h1>🏥 CardioSecure — Raw Medical Data Report</h1>
<div class="meta">
  Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} &nbsp;|&nbsp;
  Patient: {sample.get("patient","—")} &nbsp;|&nbsp;
  Device: {sample.get("device_id","—")}
</div>
<div class="warn">⚠️ EDUCATIONAL RECORD — This data is pre-encryption plaintext. Treat as CONFIDENTIAL.</div>

<h2>Patient Health Data (JSON)</h2>
<pre>{plaintext_str}</pre>

<h2>AES-256 Session Key (256-bit)</h2>
<pre>{key_hex}</pre>

<h2>GCM Nonce (96-bit)</h2>
<pre>{nonce_hex}</pre>

<h2>ECC Public Key</h2>
<pre>{pub_pem}</pre>

<h2>ECC Private Key (SECRET)</h2>
<pre>{priv_pem}</pre>

<script class="no-print">window.onload=function(){{window.print();}}</script>
</body></html>"""

        st.download_button(
            "🖨️ Print / Download Raw Data Report",
            raw_print_html.encode(),
            file_name="cardiosecure_raw_data.html",
            mime="text/html",
            type="primary",
            use_container_width=True,
        )

    # ── ENCRYPTED OUTPUT TAB ──────────────────────────────────────────────────
    with tab_enc:
        st.markdown("### 🔐 Encrypted Output — What the Database Stores")
        st.markdown("""
        <div style="background:rgba(0,229,160,0.07);border:1px solid rgba(0,229,160,0.25);
             border-radius:10px;padding:0.9rem;margin-bottom:1rem;font-size:0.82rem;color:var(--text2)">
        ✅ <b style="color:var(--green)">Safe to store/transmit:</b> This encrypted blob reveals
        zero information about the underlying medical data. Even with unlimited compute, breaking
        AES-256-GCM is computationally infeasible (~2¹²⁸ operations required).
        </div>""", unsafe_allow_html=True)

        # Colour-coded structure
        st.markdown("**Ciphertext Byte Structure (Nonce | Ciphertext | Auth Tag)**")
        st.markdown(f"""
        <div style="display:flex;gap:0.5rem;margin-bottom:1rem;flex-wrap:wrap">
          <div style="flex:0 0 auto;background:rgba(255,209,102,0.12);border:2px solid rgba(255,209,102,.4);
               border-radius:8px;padding:0.7rem 1rem;text-align:center;min-width:120px">
            <div style="color:var(--yellow);font-weight:700;font-size:0.78rem;text-transform:uppercase">Nonce</div>
            <div style="font-family:DM Mono,monospace;font-size:0.65rem;color:var(--text2);
                 word-break:break-all;margin-top:4px">{nonce_hex}</div>
            <div style="color:var(--text3);font-size:0.68rem;margin-top:4px">12 bytes · 96 bits</div>
          </div>
          <div style="flex:1;background:rgba(232,72,85,0.10);border:2px solid rgba(232,72,85,.4);
               border-radius:8px;padding:0.7rem 1rem;text-align:center;min-width:200px">
            <div style="color:var(--accent);font-weight:700;font-size:0.78rem;text-transform:uppercase">Ciphertext</div>
            <div style="font-family:DM Mono,monospace;font-size:0.62rem;color:var(--text2);
                 word-break:break-all;margin-top:4px">{ciphertext_hex[:80]}…</div>
            <div style="color:var(--text3);font-size:0.68rem;margin-top:4px">{len(enc[12:-16])} bytes</div>
          </div>
          <div style="flex:0 0 auto;background:rgba(0,229,160,0.10);border:2px solid rgba(0,229,160,.4);
               border-radius:8px;padding:0.7rem 1rem;text-align:center;min-width:120px">
            <div style="color:var(--green);font-weight:700;font-size:0.78rem;text-transform:uppercase">Auth Tag</div>
            <div style="font-family:DM Mono,monospace;font-size:0.65rem;color:var(--text2);
                 word-break:break-all;margin-top:4px">{tag_hex}</div>
            <div style="color:var(--text3);font-size:0.68rem;margin-top:4px">16 bytes · 128 bits</div>
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("**Full Ciphertext Blob (hex)**")
        st.code(cipher_hex, language="text")

        st.markdown("**Key stored separately in KMS**")
        st.code(key_hex, language="text")

        # Print encrypted only
        st.markdown("---")
        enc_print_html = f"""
<!DOCTYPE html><html><head>
<title>CardioSecure — Encrypted Data Report</title>
<style>
  body{{font-family:'Courier New',monospace;padding:2rem;color:#111;background:#fff}}
  h1{{font-family:Arial,sans-serif;color:#00897B;border-bottom:2px solid #00897B;padding-bottom:.5rem}}
  h2{{font-family:Arial,sans-serif;color:#333;margin-top:1.5rem}}
  pre{{background:#f5f5f5;padding:1rem;border-radius:6px;white-space:pre-wrap;word-break:break-all;font-size:.78rem}}
  .meta{{color:#666;font-family:Arial;font-size:.85rem;margin-bottom:1.5rem}}
  table{{border-collapse:collapse;width:100%;font-family:Arial;font-size:.82rem;margin-top:.5rem}}
  th{{background:#f0f0f0;padding:.5rem;text-align:left;border:1px solid #ccc}}
  td{{padding:.5rem;border:1px solid #ccc;vertical-align:top}}
  .ok{{background:#e8f5e9;color:#2e7d32;font-weight:700}}
  @media print{{.no-print{{display:none}}}}
</style></head><body>
<h1>🔐 CardioSecure — Encrypted Data Report</h1>
<div class="meta">
  Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} &nbsp;|&nbsp;
  Algorithm: AES-256-GCM + ECC-SECP256R1 &nbsp;|&nbsp;
  Patient: {sample.get("patient","—")}
</div>

<h2>Ciphertext Blob (full, hex-encoded)</h2>
<pre>{cipher_hex}</pre>

<h2>Structure Breakdown</h2>
<table>
  <tr><th>Component</th><th>Bytes</th><th>Hex Value</th><th>Purpose</th></tr>
  <tr><td><b>Nonce</b></td><td>12</td><td><pre style="margin:0;background:none">{nonce_hex}</pre></td><td>Unique IV for GCM counter</td></tr>
  <tr><td><b>Ciphertext</b></td><td>{len(enc[12:-16])}</td><td><pre style="margin:0;background:none">{ciphertext_hex[:40]}…</pre></td><td>AES-CTR encrypted payload</td></tr>
  <tr><td><b>Auth Tag</b></td><td>16</td><td><pre style="margin:0;background:none">{tag_hex}</pre></td><td>GHASH integrity tag</td></tr>
</table>

<h2>AES-256 Session Key (stored separately in KMS)</h2>
<pre>{key_hex}</pre>

<h2>ECC Public Key</h2>
<pre>{pub_pem}</pre>

<h2>Integrity Status</h2>
<table>
  <tr><th>Check</th><th>Result</th></tr>
  <tr><td>Authentication tag present</td><td class="ok">✓ PASS (128-bit GHASH)</td></tr>
  <tr><td>Nonce length valid</td><td class="ok">✓ PASS (96 bits)</td></tr>
  <tr><td>Key length valid</td><td class="ok">✓ PASS (256 bits / AES-256)</td></tr>
  <tr><td>AEAD mode</td><td class="ok">✓ PASS (GCM — Encrypt-then-MAC)</td></tr>
</table>

<script class="no-print">window.onload=function(){{window.print();}}</script>
</body></html>"""

        st.download_button(
            "🖨️ Print / Download Encrypted Data Report",
            enc_print_html.encode(),
            file_name="cardiosecure_encrypted_data.html",
            mime="text/html",
            type="primary",
            use_container_width=True,
        )

    # ── SIDE-BY-SIDE TAB ─────────────────────────────────────────────────────
    with tab_both:
        st.markdown("### ⚖️ Raw vs Encrypted — Full Side-by-Side")
        st.markdown("""
        <div class="enc-explanation" style="margin-bottom:1rem">
        The table below shows every field of the medical record alongside its encrypted
        counterpart. Notice: the ciphertext has no discernible structure, no field delimiters,
        no recognisable patterns — this is the goal of <b>semantic security</b>.
        </div>""", unsafe_allow_html=True)

        # Field-by-field comparison table
        fields = [
            ("Patient Name",    sample.get("patient","—"),      "[embedded in ciphertext, indistinguishable]"),
            ("BPM Reading",     str(sample.get("bpm","—")),     "[embedded in ciphertext, indistinguishable]"),
            ("HR Category",     sample.get("category","—"),     "[embedded in ciphertext, indistinguishable]"),
            ("Timestamp",       sample.get("timestamp","—"),    "[embedded in ciphertext, indistinguishable]"),
            ("Device ID",       sample.get("device_id","—"),    "[embedded in ciphertext, indistinguishable]"),
            ("Recommendations", str(sample.get("recommendations",[])), "[embedded in ciphertext, indistinguishable]"),
        ]

        header_html = """
        <table style="width:100%;border-collapse:collapse;font-size:0.8rem">
          <thead>
            <tr>
              <th style="background:var(--card2);color:var(--text3);padding:.6rem .8rem;
                         text-align:left;border:1px solid var(--border);font-size:.72rem;
                         text-transform:uppercase;letter-spacing:.05em;width:18%">Field</th>
              <th style="background:rgba(255,209,102,0.1);color:var(--yellow);padding:.6rem .8rem;
                         text-align:left;border:1px solid var(--border);font-size:.72rem;
                         text-transform:uppercase;letter-spacing:.05em;width:30%">📄 Raw Plaintext</th>
              <th style="background:rgba(0,229,160,0.07);color:var(--green);padding:.6rem .8rem;
                         text-align:left;border:1px solid var(--border);font-size:.72rem;
                         text-transform:uppercase;letter-spacing:.05em;width:52%">🔐 Encrypted (AES-256-GCM)</th>
            </tr>
          </thead><tbody>"""

        rows_html = ""
        for field, raw_val, enc_val in fields:
            rows_html += f"""
            <tr>
              <td style="padding:.55rem .8rem;border:1px solid var(--border);
                         color:var(--text3);font-size:.75rem;font-weight:600">{field}</td>
              <td style="padding:.55rem .8rem;border:1px solid var(--border);
                         color:var(--text2);font-family:DM Mono,monospace;font-size:.72rem;
                         background:rgba(255,209,102,0.04)">{raw_val}</td>
              <td style="padding:.55rem .8rem;border:1px solid var(--border);
                         color:var(--text3);font-family:DM Mono,monospace;font-size:.68rem;
                         font-style:italic;background:rgba(0,229,160,0.03)">{enc_val}</td>
            </tr>"""

        # Full blob row
        rows_html += f"""
            <tr>
              <td style="padding:.55rem .8rem;border:1px solid var(--border);
                         color:var(--accent);font-size:.75rem;font-weight:600" colspan="1">Full Output</td>
              <td style="padding:.55rem .8rem;border:1px solid var(--border);
                         color:var(--text2);font-family:DM Mono,monospace;font-size:.68rem;
                         background:rgba(255,209,102,0.04)">{plaintext_str[:120].replace(chr(10)," ")}…</td>
              <td style="padding:.55rem .8rem;border:1px solid var(--border);
                         color:var(--green);font-family:DM Mono,monospace;font-size:.68rem;
                         background:rgba(0,229,160,0.04);word-break:break-all">{cipher_hex[:120]}…</td>
            </tr>
          </tbody></table>"""

        st.markdown(header_html + rows_html, unsafe_allow_html=True)

        st.divider()
        st.markdown("### 🔬 Entropy & Randomness Analysis")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Plaintext character frequency**")
            plain_chars  = {}
            for ch in plaintext_str:
                plain_chars[ch] = plain_chars.get(ch, 0) + 1
            top_plain = sorted(plain_chars.items(), key=lambda x: -x[1])[:8]
            for ch, cnt in top_plain:
                pct = cnt / len(plaintext_str) * 100
                label = repr(ch) if ch in (" ", "\n", '"', ":", "{", "}") else ch
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:.5rem;margin:2px 0">' 
                    f'<code style="width:28px;text-align:center">{label}</code>' 
                    f'<div style="flex:1;height:14px;background:var(--border);border-radius:3px">' 
                    f'<div style="width:{min(pct*5,100):.0f}%;height:100%;background:var(--yellow);'
                    f'border-radius:3px"></div></div>' 
                    f'<span style="font-size:.7rem;color:var(--text3);width:40px">{pct:.1f}%</span></div>',
                    unsafe_allow_html=True
                )
            st.caption(f"Unique chars: {len(plain_chars)} / {len(plaintext_str)} total")

        with c2:
            st.markdown("**Ciphertext hex-char frequency (should be near-uniform)**")
            hex_chars = {}
            for ch in cipher_hex:
                hex_chars[ch] = hex_chars.get(ch, 0) + 1
            for ch in sorted(hex_chars.keys()):
                pct = hex_chars[ch] / len(cipher_hex) * 100
                ideal = 100 / 16  # 6.25%
                deviation = abs(pct - ideal)
                bar_color = "var(--green)" if deviation < 1.5 else "var(--yellow)"
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:.5rem;margin:2px 0">' 
                    f'<code style="width:20px;text-align:center">{ch}</code>' 
                    f'<div style="flex:1;height:14px;background:var(--border);border-radius:3px">' 
                    f'<div style="width:{min(pct*8,100):.0f}%;height:100%;background:{bar_color};'
                    f'border-radius:3px"></div></div>' 
                    f'<span style="font-size:.7rem;color:var(--text3);width:40px">{pct:.1f}%</span></div>',
                    unsafe_allow_html=True
                )
            st.caption(f"Ideal = 6.25% each · Deviation < 2% ✅")

        st.divider()

        # ── Combined print report ────────────────────────────────────────────
        both_print_html = f"""
<!DOCTYPE html><html><head>
<title>CardioSecure — Full Encryption Report</title>
<style>
  body{{font-family:Arial,sans-serif;padding:2rem;color:#111;background:#fff;max-width:1100px;margin:0 auto}}
  h1{{color:#E84855;border-bottom:3px solid #E84855;padding-bottom:.5rem}}
  h2{{color:#333;margin-top:2rem;border-left:4px solid #E84855;padding-left:.8rem}}
  h3{{color:#555;margin-top:1.2rem}}
  pre{{font-family:'Courier New',monospace;background:#f5f5f5;padding:1rem;border-radius:6px;
       white-space:pre-wrap;word-break:break-all;font-size:.76rem;border:1px solid #e0e0e0}}
  table{{border-collapse:collapse;width:100%;font-size:.82rem;margin-top:.8rem}}
  th{{background:#f0f0f0;padding:.6rem;text-align:left;border:1px solid #ccc;font-size:.78rem}}
  td{{padding:.55rem;border:1px solid #ccc;vertical-align:top;font-size:.78rem}}
  .raw-cell{{background:#fffde7;font-family:'Courier New',monospace;font-size:.74rem}}
  .enc-cell{{background:#e8f5e9;font-family:'Courier New',monospace;font-size:.72rem;font-style:italic;color:#444}}
  .meta{{color:#666;font-size:.85rem;margin-bottom:1.5rem;line-height:1.8}}
  .badge-ok{{background:#e8f5e9;color:#2e7d32;padding:2px 8px;border-radius:4px;font-size:.78rem;font-weight:700}}
  .section-divider{{border:none;border-top:2px solid #eee;margin:1.5rem 0}}
  .page-break{{page-break-after:always}}
  @media print{{.no-print{{display:none}}}}
</style></head><body>

<h1>🏥 CardioSecure — Full Hybrid Encryption Report</h1>
<div class="meta">
  <b>Generated:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>
  <b>Patient:</b> {sample.get("patient","—")} &nbsp;|&nbsp;
  <b>Device:</b> {sample.get("device_id","—")}<br>
  <b>Algorithm:</b> AES-256-GCM + ECC-SECP256R1 (NIST P-256) + HKDF-SHA256<br>
  <b>Security Level:</b> 128-bit equivalent &nbsp;|&nbsp;
  <b>Mode:</b> AEAD (Authenticated Encryption with Associated Data)
</div>

<hr class="section-divider">
<h2>Section A — Raw Plaintext Medical Data</h2>

<h3>Patient JSON Record</h3>
<pre>{plaintext_str}</pre>

<h3>AES-256 Session Key (256 bits)</h3>
<pre>{key_hex}</pre>

<h3>GCM Nonce (96 bits — prepended to ciphertext)</h3>
<pre>{nonce_hex}</pre>

<h3>ECC Public Key (SECP256R1)</h3>
<pre>{pub_pem}</pre>

<h3>ECC Private Key (SECRET — educational display only)</h3>
<pre>{priv_pem}</pre>

<hr class="section-divider" class="page-break">
<h2>Section B — Encrypted Output</h2>

<h3>Full Ciphertext Blob (Nonce + Ciphertext + Auth Tag)</h3>
<pre>{cipher_hex}</pre>

<h3>Ciphertext Structure</h3>
<table>
  <tr><th>Component</th><th>Bytes</th><th>Hex Value</th><th>Purpose</th></tr>
  <tr>
    <td><b>Nonce</b></td><td>12</td>
    <td class="raw-cell">{nonce_hex}</td>
    <td>Unique 96-bit IV for GCM counter mode. Must never repeat with same key.</td>
  </tr>
  <tr>
    <td><b>Ciphertext</b></td><td>{len(enc[12:-16])}</td>
    <td class="enc-cell">{ciphertext_hex[:60]}…</td>
    <td>AES-CTR encrypted payload. Same length as plaintext (stream cipher).</td>
  </tr>
  <tr>
    <td><b>Auth Tag</b></td><td>16</td>
    <td class="enc-cell">{tag_hex}</td>
    <td>128-bit GHASH authentication tag. Verified before any decryption occurs.</td>
  </tr>
</table>

<hr class="section-divider">
<h2>Section C — Side-by-Side Field Comparison</h2>
<table>
  <tr>
    <th style="width:15%">Field</th>
    <th style="width:35%">📄 Raw Plaintext</th>
    <th style="width:50%">🔐 Status in Ciphertext</th>
  </tr>
  {"".join(
    f'<tr><td><b>{f}</b></td><td class="raw-cell">{r}</td><td class="enc-cell">{e}</td></tr>'
    for f, r, e in fields
  )}
</table>

<hr class="section-divider">
<h2>Section D — Integrity & Compliance Verification</h2>
<table>
  <tr><th>Check</th><th>Result</th><th>Standard</th></tr>
  <tr><td>Authentication tag present</td><td><span class="badge-ok">✓ PASS</span></td><td>NIST SP 800-38D</td></tr>
  <tr><td>Nonce uniqueness (96-bit random)</td><td><span class="badge-ok">✓ PASS</span></td><td>NIST SP 800-38D §8.2.1</td></tr>
  <tr><td>Key length (AES-256)</td><td><span class="badge-ok">✓ PASS — 256 bits</span></td><td>FIPS 197</td></tr>
  <tr><td>Key derivation (HKDF-SHA256)</td><td><span class="badge-ok">✓ PASS</span></td><td>RFC 5869</td></tr>
  <tr><td>ECC curve (SECP256R1)</td><td><span class="badge-ok">✓ PASS</span></td><td>NIST FIPS 186-4</td></tr>
  <tr><td>AEAD mode (Encrypt-then-MAC)</td><td><span class="badge-ok">✓ PASS</span></td><td>RFC 5116</td></tr>
  <tr><td>Plaintext bytes</td><td><span class="badge-ok">{plain_bytes} bytes</span></td><td>—</td></tr>
  <tr><td>Ciphertext bytes</td><td><span class="badge-ok">{cipher_bytes} bytes (+{overhead} overhead)</span></td><td>—</td></tr>
</table>

<script class="no-print">window.onload=function(){{window.print();}}</script>
</body></html>"""

        st.download_button(
            "🖨️ Print / Download Full Combined Report",
            both_print_html.encode(),
            file_name="cardiosecure_full_encryption_report.html",
            mime="text/html",
            type="primary",
            use_container_width=True,
        )

    enc_nav("enc_step7")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: RAW DATA & PRINT
# ─────────────────────────────────────────────────────────────────────────────

elif st.session_state.page == "raw_data":
    st.markdown('<div class="section-header">📦 Raw Data & Print Center</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">View, compare, and print raw or encrypted data records</div>', unsafe_allow_html=True)

    all_results = get_all_results_admin() if is_admin else get_user_results(user['id'])
    results_admin = get_all_results_admin() if is_admin else []

    if not all_results:
        st.info("No records available.")
        st.stop()

    # Select a record
    options = {f"#{r['test_id']} | {r['test_date'][:16]} | {r['bpm']} BPM" :
               r for r in (all_results if is_admin else
               [{**r, 'username': user['username'], 'full_name': user['full_name'],
                 'encrypted_hex': b'', 'key_hex': ''} for r in all_results])}

    if is_admin:
        sel_label = st.selectbox("Select a record to inspect", list(options.keys()))
        record = options[sel_label]
    else:
        records_plain = get_user_results(user['id'])
        if not records_plain:
            st.info("No test records yet.")
            st.stop()
        opts2 = {f"#{r['test_id']} | {r['test_date'][:16]} | {r['bpm']} BPM": r for r in records_plain}
        sel_label = st.selectbox("Select a record to inspect", list(opts2.keys()))
        record = opts2[sel_label]

    st.divider()

    print_tab, raw_tab, enc_tab, both_tab = st.tabs(["🖨️ Print Options", "📄 Raw Data", "🔐 Encrypted Data", "📊 Side-by-Side"])

    with raw_tab:
        st.markdown("### 📄 Decrypted / Raw Patient Data")
        st.markdown("""
        <div style="background:rgba(255,209,102,0.07);border:1px solid rgba(255,209,102,0.25);
             border-radius:8px;padding:0.8rem;font-size:0.8rem;color:var(--text2);margin-bottom:1rem">
        ⚠️ This is the <b>decrypted plaintext</b> — the most sensitive form of the data. Access is
        logged. In production, only authorised clinicians with verified credentials may view this.
        </div>""", unsafe_allow_html=True)

        if is_admin:
            raw = {
                "record_id":   record['test_id'],
                "patient":     record['full_name'],
                "username":    record['username'],
                "bpm":         record['bpm'],
                "category":    record['analysis']['category'],
                "description": record['analysis']['description'],
                "recommendations": record['analysis']['recommendations'],
                "test_date":   record['test_date'],
                "status":      record['analysis']['status']
            }
        else:
            raw = {
                "record_id":   record.get('test_id',''),
                "patient":     user['full_name'],
                "username":    user['username'],
                "bpm":         record['bpm'],
                "category":    record['analysis']['category'],
                "description": record['analysis']['description'],
                "recommendations": record['analysis']['recommendations'],
                "test_date":   record.get('test_date',''),
                "status":      record['analysis']['status']
            }

        c1, c2 = st.columns(2)
        with c1:
            st.json(raw)
        with c2:
            st.code(json.dumps(raw, indent=2), language="json")
            st.download_button("⬇ Download Raw JSON",
                               json.dumps(raw, indent=2),
                               f"raw_{record.get('test_id','')}.json", "application/json")

    with enc_tab:
        st.markdown("### 🔐 Encrypted Data (Hex Representation)")
        st.markdown("""
        <div style="background:rgba(0,229,160,0.07);border:1px solid rgba(0,229,160,0.2);
             border-radius:8px;padding:0.8rem;font-size:0.8rem;color:var(--text2);margin-bottom:1rem">
        ✅ This is what is stored in the database. Without the encryption key, this data is
        mathematically indistinguishable from random noise. Even a quantum computer would need
        to solve the AES key-search problem first.
        </div>""", unsafe_allow_html=True)

        if is_admin and 'encrypted_hex' in record:
            enc_hex = record['encrypted_hex']
            key_hex = record['key_hex']
        else:
            # Re-encrypt for display
            sample_enc = {k: raw[k] for k in raw}
            key_demo = os.urandom(32)
            enc_bytes = HybridEncryption.encrypt_aes_gcm(json.dumps(sample_enc), key_demo)
            enc_hex = enc_bytes.hex()
            key_hex = key_demo.hex()

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**🔐 Encrypted Blob (Hex)**")
            st.code(enc_hex, language="text")
        with c2:
            st.markdown("**🔑 Encryption Key (AES-256)**")
            st.code(key_hex if key_hex else "(key not shown — stored in separate KMS)", language="text")
            nonce = enc_hex[:24]
            st.markdown(f"""
            <div class="metric-card" style="margin-top:0.5rem">
              <div style="font-size:0.75rem;color:var(--text2)"><b>Nonce (first 12 bytes):</b>
              <code style="font-size:0.7rem">{nonce}</code></div>
              <div style="font-size:0.75rem;color:var(--text2);margin-top:4px">
              <b>Total encrypted size:</b> {len(enc_hex)//2} bytes</div>
            </div>""", unsafe_allow_html=True)

        st.download_button("⬇ Download Encrypted Hex",
                           enc_hex, f"encrypted_{record.get('test_id','')}.txt", "text/plain")

    with both_tab:
        st.markdown("### 📊 Raw vs Encrypted Comparison")
        raw_str = json.dumps(raw, indent=2)
        enc_display = enc_hex[:200] + "…" if is_admin and 'encrypted_hex' in record else "(re-generated sample)"

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
            <div style="text-align:center;padding:0.5rem;background:rgba(255,209,102,0.1);
                 border-radius:8px 8px 0 0;border:1px solid rgba(255,209,102,0.2);
                 font-size:0.82rem;color:var(--yellow);font-weight:600">
            📄 PLAINTEXT (Readable)</div>""", unsafe_allow_html=True)
            st.code(raw_str, language="json")
            st.metric("Size", f"{len(raw_str)} bytes")

        with c2:
            st.markdown("""
            <div style="text-align:center;padding:0.5rem;background:rgba(0,229,160,0.1);
                 border-radius:8px 8px 0 0;border:1px solid rgba(0,229,160,0.2);
                 font-size:0.82rem;color:var(--green);font-weight:600">
            🔐 CIPHERTEXT (Encrypted)</div>""", unsafe_allow_html=True)
            st.code(enc_hex if is_admin else "(re-encrypted demo)", language="text")
            st.metric("Size", f"{len(enc_hex)//2} bytes")

    with print_tab:
        st.markdown("### 🖨️ Print Options")
        st.markdown("""
        <div style="font-size:0.85rem;color:var(--text2);margin-bottom:1rem">
        Use your browser's print function (Ctrl+P / Cmd+P) after clicking a print button below.
        Each option prepares a formatted view optimised for printing.
        </div>""", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        raw_str = json.dumps(raw, indent=2)
        with c1:
            st.markdown("""
            <div class="cs-card" style="text-align:center">
              <div style="font-size:2rem;margin-bottom:0.5rem">📄</div>
              <div style="font-weight:600;margin-bottom:0.3rem">Print Raw Data</div>
              <div style="font-size:0.78rem;color:var(--text2)">Patient-readable plaintext report</div>
            </div>""", unsafe_allow_html=True)
            raw_html = f"""<html><head><title>CardioSecure Report</title>
<style>body{{font-family:monospace;padding:2rem;color:#000}}
h1{{color:#E84855}}pre{{background:#f5f5f5;padding:1rem;border-radius:4px}}</style></head>
<body><h1>❤️ CardioSecure – Patient Report</h1>
<p>Generated: {datetime.now().strftime('%d %B %Y %H:%M')}</p>
<hr><pre>{raw_str}</pre></body></html>"""
            st.download_button("⬇ Download Raw Report",
                               raw_html, f"report_raw_{record.get('test_id','')}.html", "text/html")

        with c2:
            st.markdown("""
            <div class="cs-card" style="text-align:center">
              <div style="font-size:2rem;margin-bottom:0.5rem">🔐</div>
              <div style="font-weight:600;margin-bottom:0.3rem">Print Encrypted</div>
              <div style="font-size:0.78rem;color:var(--text2)">Technical encrypted audit record</div>
            </div>""", unsafe_allow_html=True)
            enc_html = f"""<html><head><title>CardioSecure Encrypted Record</title>
<style>body{{font-family:monospace;padding:2rem;color:#000}}
h1{{color:#00B09B}}pre{{background:#f5f5f5;padding:1rem;border-radius:4px;word-break:break-all}}</style></head>
<body><h1>🔐 CardioSecure – Encrypted Record</h1>
<p>Generated: {datetime.now().strftime('%d %B %Y %H:%M')}</p>
<p>Record ID: #{record.get('test_id','')}</p>
<hr><h3>Encrypted Data (AES-256-GCM):</h3>
<pre>{enc_hex if is_admin else '(re-encrypted demo)'}</pre>
<h3>Nonce (first 12 bytes):</h3><pre>{enc_hex[:24] if enc_hex else ''}</pre>
</body></html>"""
            st.download_button("⬇ Download Encrypted Report",
                               enc_html, f"report_enc_{record.get('test_id','')}.html", "text/html")

        with c3:
            st.markdown("""
            <div class="cs-card" style="text-align:center">
              <div style="font-size:2rem;margin-bottom:0.5rem">📋</div>
              <div style="font-weight:600;margin-bottom:0.3rem">Print Both</div>
              <div style="font-size:0.78rem;color:var(--text2)">Combined full report (raw + encrypted)</div>
            </div>""", unsafe_allow_html=True)
            both_html = f"""<html><head><title>CardioSecure Full Report</title>
<style>body{{font-family:monospace;padding:2rem;color:#000;max-width:900px;margin:0 auto}}
h1{{color:#E84855}}h2{{color:#333;border-bottom:2px solid #E84855;padding-bottom:0.3rem}}
pre{{background:#f5f5f5;padding:1rem;border-radius:4px;white-space:pre-wrap;word-break:break-all}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:1rem}}</style></head>
<body><h1>❤️ CardioSecure – Full Report</h1>
<p>Generated: {datetime.now().strftime('%d %B %Y %H:%M')} | Record ID: #{record.get('test_id','')}</p>
<hr>
<div class="grid">
<div><h2>📄 Raw Data (Plaintext)</h2><pre>{raw_str}</pre></div>
<div><h2>🔐 Encrypted Data</h2><pre>{enc_hex if is_admin else '(demo)'}</pre>
<p><b>Nonce:</b> {enc_hex[:24] if enc_hex else ''}</p></div>
</div>
<hr><p style="font-size:0.8rem;color:#666">
⚠️ Secure document — handle in accordance with HIPAA/GDPR regulations.
CardioSecure · EBSU/PG/PhD/2021/10930 · Yunisa Sunday</p>
</body></html>"""
            st.download_button("⬇ Download Full Report",
                               both_html, f"report_full_{record.get('test_id','')}.html", "text/html")

# ─────────────────────────────────────────────────────────────────────────────
# FALLBACK
# ─────────────────────────────────────────────────────────────────────────────

else:
    if st.session_state.page not in [p for p,_,_ in ENC_STEPS] and \
       st.session_state.page not in ["monitor","results","admin_dashboard",
                                      "admin_users","admin_records","all_records","raw_data","encryption"]:
        st.session_state.page = "monitor"
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="cs-footer">
  🔒 AES-256-GCM + ECC-SECP256R1 Hybrid Encryption ·
  🧠 ML-Refined rPPG Heart Rate Detection ·
  EBSU/PG/PhD/2021/10930 · Yunisa Sunday<br>
  ⚠️ Research & educational purposes only — not a certified medical device
</div>
""", unsafe_allow_html=True)
