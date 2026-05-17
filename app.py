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
page_title="MedChainSecure: A Secure IoMT Heart Rate System with Hybrid Encryption & Blockchain",
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
.cs-nav{{background:{nav_bg};border-bottom:1px solid {nav_bdr};padding:.8rem 2rem;width:100vw;margin-left:calc(-50vw + 50%);box-sizing:border-box;
display:flex;align-items:center;justify-content:space-between;
margin-bottom:1.5rem;box-shadow:{nav_shd};position:sticky;top:0;z-index:100;
animation:slideDown .45s cubic-bezier(.23,1,.32,1) both;}}

/* FIX: Remove white overlay on left side */
[data-testid="stAppViewContainer"] {{
background: {bg} !important;
}}

section[data-testid="stMain"] {{
padding: 0 !important;
background: transparent !important;
}}

.main .block-container, [data-testid="stAppViewBlockContainer"],
[data-testid="stMainBlockContainer"] {{
padding: 0 !important;
max-width: 100% !important;
width: 100% !important;
background: transparent !important;
}}

/* Fix for content padding - don't force padding on all elements */
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {{
padding-left: 0 !important;
padding-right: 0 !important;
}}

/* Only apply padding to specific containers */
.stTabs, .stExpander, .cs-card {{
padding-left: 1.5rem;
padding-right: 1.5rem;
}}

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
.block-container{{padding:0 !important;max-width:100% !important}}
.main .block-container{{padding:0 !important}}
[data-testid="stAppViewContainer"]>section>div{{padding:0 !important}}
/* Full-width page styling */
.page-full{{width:100%;box-sizing:border-box}}
.page-hero-bg{{
margin:-1rem -2rem 2rem;padding:3.5rem 2rem 2.5rem;
background:
  radial-gradient(ellipse at 8% 20%,hsla(355,78%,55%,.09) 0%,transparent 50%),
  radial-gradient(ellipse at 92% 80%,hsla(195,100%,50%,.06) 0%,transparent 50%),
  radial-gradient(ellipse at 50% 100%,hsla(222,40%,8%,1) 0%,transparent 70%);
border-bottom:1px solid var(--border);text-align:center
}}
.metric-card{{
background:var(--card);border:1px solid var(--border);border-radius:14px;
padding:1.3rem 1rem;text-align:center;height:100%;
transition:transform .2s,box-shadow .2s;
}}
.metric-card:hover{{transform:translateY(-4px);box-shadow:0 12px 32px rgba(0,0,0,.3)}}
.metric-value{{font-family:'DM Serif Display',serif;font-size:2.2rem;line-height:1;
font-weight:400;color:var(--accent);margin:.3rem 0 .2rem}}
.metric-label{{font-size:.78rem;font-weight:600;color:var(--text)}}
.metric-sub{{font-size:.68rem;color:var(--text3);margin-top:.2rem}}

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
                 "X-Sig": sig, "User-Agent": "MedChainSecure/2.0"},
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
        ("monitor",       "❤️ Monitor"),
        ("results",       "📊 My Results"),
        ("encryption",    "🔒 Encryption Lab"),
        ("decentral",     "🌐 Decentralisation"),
        ("decryption",    "🔓 Decryption"),
        ("raw_data",      "📦 Data"),
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
                  color:var(--text);line-height:1">MedChainSecure</div>
      <div style="font-size:.58rem;color:var(--text3);letter-spacing:.1em;
                  text-transform:uppercase;margin-top:1px">IoMT Security Platform</div>
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
    st.markdown('<div class="nav-btn-row" style="padding:0 1.5rem">', unsafe_allow_html=True)
    # Build one column per nav item + 1 for sign-out
    n_cols = len(nav_items) + 1
    cols = st.columns(n_cols)
    for i, (pid, label) in enumerate(nav_items):
        with cols[i]:
            active = (st.session_state.page == pid or
                      (pid == "encryption" and st.session_state.page.startswith("enc_")) or
                      (pid == "decentral"  and st.session_state.page == "decentral") or
                      (pid == "decryption" and st.session_state.page == "decryption"))
            if active:
                # Active: styled text, not a button
                st.markdown(
                    f'<div style="text-align:center;padding:4px 8px;font-size:.83rem;'
                    f'font-weight:600;color:var(--accent);background:hsla(355,78%,55%,.12);'
                    f'border-radius:8px">{label}</div>',
                    unsafe_allow_html=True
                )
            else:
                # FIX: Use unique key with timestamp
                if st.button(label, key=unique_key(f"nav__{pid}_{i}"), use_container_width=True):
                    go(pid)
    # Sign Out in last column
    with cols[-1]:
        if u:
            if st.button("Sign Out", key=unique_key("nav_signout"), use_container_width=True):
                logout()
    st.markdown('</div>', unsafe_allow_html=True)
else:
    # Unauthenticated: sign-in / home buttons
    if st.session_state.page == "landing":
        _, cb, _ = st.columns([5, 1, 0.3])
        with cb:
            if st.button("Sign In →", key="nav_signin_main", type="primary"):
                go("login")
    elif st.session_state.page == "login":
        _, cb, _ = st.columns([5, 1.2, 0.3])
        with cb:
            if st.button("← Home", key="nav_home_main"):
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
  <p class="hero-sub">EBSU/PG/PhD/2021/10930 · Yunisa Sunday</p>
  <h1 class="hero-title">MedChainSecure</h1>
  <p class="hero-desc">
    Hybrid Encryption &amp; Blockchain Framework for Secure IoMT Data Management
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
    🔗 AES-256-GCM + ECC-SECP256R1 + Blockchain Ledger
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
        Hybrid Encryption + Blockchain</h3>
      <p style="font-size:.83rem;color:var(--text2);line-height:1.6">
        AES-256-GCM + ECC-SECP256R1 + Blockchain Ledger for IoMT data integrity and privacy.</p>
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
        AES-256-GCM encrypted records, ECDH key exchange, Blockchain audit ledger, decentralised backup.</p>
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
        MedChainSecure</div>
      <div style="color:var(--text3);font-size:.72rem;letter-spacing:.18em;
                  text-transform:uppercase;margin-top:.4rem">
        EBSU/PG/PhD/2021/10930 · Yunisa Sunday</div>
      <div style="color:var(--text2);font-family:'DM Mono',monospace;font-size:.67rem;margin-top:.6rem">
        EBSU/PG/PhD/2021/10930 &middot; Yunisa Sunday</div>
      <div style="display:inline-flex;align-items:center;gap:.4rem;margin-top:.7rem;
                  padding:3px 13px;border:1px solid hsla(195,100%,50%,.25);border-radius:20px;
                  background:hsla(195,100%,50%,.06);font-size:.67rem;color:var(--cyan);
                  letter-spacing:.06em">
        🔗 AES-256-GCM + ECC-SECP256R1 + Blockchain
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
<div class="cs-footer">🔗 MedChainSecure · AES-256-GCM + ECC-SECP256R1 + Blockchain Ledger ·
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
  <span style="font-size:2rem">🔗</span>
  <div style="font-family:'DM Serif Display',serif;font-size:1rem;color:#E8EDF8;margin-top:4px">
    MedChainSecure</div>
</div>
""", unsafe_allow_html=True)
st.divider()

user_pages = [
    ("❤️ Monitor",              "monitor"),
    ("📊 My Results",            "results"),
    ("🔒 Encryption Lab",        "enc_step1"),
    ("🌐 Decentralisation",      "decentralisation"),
    ("🔓 Decryption",            "decryption"),
    ("📦 Data",                  "raw_data"),
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
    active = (st.session_state.page == pg or
              (pg == "enc_step1" and st.session_state.page.startswith("enc_")))
    if st.button(label, use_container_width=True,
                 type="primary" if active else "secondary", key=unique_key(f"sidebar_{pg}")):
        st.session_state.page = pg
        st.rerun()

st.divider()
if st.button("🚪 Sign Out", use_container_width=True, type="secondary", key=unique_key("sidebar_signout")):
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
# PAGE: HEART MONITOR (simplified for brevity - keep your existing implementation)
# ─────────────────────────────────────────────────────────────────────────────

# Due to length limitations, I'm showing the key fix for the encryption lab step pills
# You'll need to replace the enc_progress_bar function with this version:

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
        # FIX: Use unique key with page name
        clicked = st.button(
            icon,
            key=unique_key(f"enc_pill_{pg}_{i}"),
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

# Define ENC_STEPS if not already defined (add this before enc_progress_bar)
ENC_STEPS = [
("enc_step1", "📝 Step 1", "Plaintext Prep"),
("enc_step2", "🔑 Step 2", "ECC Key Gen"),
("enc_step3", "🔐 Step 3", "AES Key & Nonce"),
("enc_step4", "🛡️ Step 4", "AES-GCM Encrypt"),
("enc_step5", "🌐 Step 5", "Storage"),
("enc_step6", "🔓 Step 6", "Decryption"),
("enc_step7", "🖨️ Step 7", "Raw vs Encrypted"),
]

# The rest of your existing code continues here...
# (Keep all your existing page implementations for monitor, results, admin, etc.)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="cs-footer">
🔗 MedChainSecure · AES-256-GCM + ECC-SECP256R1 + Blockchain Ledger ·
Hybrid Encryption &amp; Blockchain Framework for Secure IoMT Data Management ·
EBSU/PG/PhD/2021/10930 · Yunisa Sunday<br>
⚠️ Research &amp; educational purposes only — not a certified medical device
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PWA / OFFLINE SUPPORT
# Registers a service worker so the app can cache pages and work offline.
# ─────────────────────────────────────────────────────────────────────────────
components.html("""
<script>
(function(){
if(!('serviceWorker' in navigator)) return;
var sw = [
"const C='medchain-v2';",
"self.addEventListener('install',e=>e.waitUntil(caches.open(C).then(c=>c.addAll(['/']))));",
"self.addEventListener('fetch',e=>e.respondWith(",
"  fetch(e.request).catch(()=>caches.match(e.request))",
"));"
].join('');
var blob = new Blob([sw], {type:'application/javascript'});
navigator.serviceWorker.register(URL.createObjectURL(blob)).catch(function(){});

// Web App Manifest for "Add to Home Screen"
var m = JSON.stringify({
name:'MedChainSecure',
short_name:'MedChain',
description:'Hybrid Encryption & Blockchain Framework for Secure IoMT Data Management',
start_url:'/',
display:'standalone',
background_color:'#0A0E1A',
theme_color:'#E84855',
icons:[{
  src:"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E❤️%3C/text%3E%3C/svg%3E",
  sizes:'512x512', type:'image/svg+xml'
}]
});
var ml = document.createElement('link');
ml.rel='manifest';
ml.href=URL.createObjectURL(new Blob([m],{type:'application/json'}));
document.head.appendChild(ml);

// Meta tags for standalone iOS
var mt = document.createElement('meta');
mt.name='apple-mobile-web-app-capable'; mt.content='yes';
document.head.appendChild(mt);
})();
</script>
""", height=0)
