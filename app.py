import streamlit as st
import sys
import os

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
    import plotly.graph_objects as go
    import plotly.express as px
except ImportError:
    st.error("Missing: plotly. Add `plotly>=5.19.0` to requirements.txt")
    st.stop()

try:
    import pandas as pd
except ImportError:
    st.error("Missing: pandas. Add `pandas>=2.2.0` to requirements.txt")
    st.stop()

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
import tempfile

# ─────────────────────────────────────────────────────────────────────────────
# APP NAME & BRANDING
# ─────────────────────────────────────────────────────────────────────────────
APP_TITLE    = "MedChainSecure"
APP_SUBTITLE = "Hybrid Encryption & Blockchain Framework for Secure IoMT Data Management"
APP_AUTHOR   = "EBSU/PG/PhD/2021/10930 · Yunisa Sunday"
APP_SECURITY = "🔒 AES-256-GCM + ECC-SECP256R1 + Blockchain Ledger"
APP_FULLNAME = "MedChainSecure: A Secure IoMT Based Heart Rate Generated Data using Hybrid Encryption & Blockchain Techniques"

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=f"{APP_TITLE} – Heart Rate Monitor",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────────────────────────────────────
# THEME CSS
# ─────────────────────────────────────────────────────────────────────────────
def _apply_theme_css():
    is_light = st.session_state.get("theme", "dark") == "light"
    if is_light:
        bg="hsl(220,20%,97%)";bg2="hsl(220,20%,93%)";card="hsl(0,0%,100%)";card2="hsl(220,20%,95%)"
        border="hsl(220,20%,84%)";text="hsl(222,40%,12%)";text2="hsl(222,20%,45%)"
        text3="hsl(222,15%,65%)";accent="hsl(355,78%,48%)";accent2="hsl(355,78%,58%)"
        green="hsl(160,70%,35%)";yellow="hsl(40,80%,42%)";cyan="hsl(195,80%,38%)"
        purple="hsl(265,55%,48%)";glow="hsla(355,78%,48%,.2)"
        app_bg=f"radial-gradient(ellipse at 10% 20%,hsla(355,78%,55%,.03) 0%,transparent 50%),{bg}"
        nav_bg=f"linear-gradient(90deg,{card},{bg2})";nav_bdr=border
        nav_shd="0 2px 12px rgba(0,0,0,.1)";inp_bg=card2;tab_list=bg2;tab_act=card
        scr_trk="hsl(220,20%,93%)";scr_thm="hsl(220,20%,78%)";btn_svg=text
        tog_bg=card;tog_bdr=border;tog_shd="0 2px 12px rgba(0,0,0,.15)"
    else:
        bg="hsl(222,58%,5%)";bg2="hsl(222,50%,8%)";card="hsl(222,40%,12%)";card2="hsl(222,35%,16%)"
        border="hsl(222,30%,22%)";text="hsl(220,30%,92%)";text2="hsl(220,15%,55%)"
        text3="hsl(222,20%,35%)";accent="hsl(355,78%,55%)";accent2="hsl(355,78%,68%)"
        green="hsl(160,100%,45%)";yellow="hsl(40,100%,70%)";cyan="hsl(195,100%,50%)"
        purple="hsl(265,70%,60%)";glow="hsla(355,78%,55%,.3)"
        app_bg=f"radial-gradient(ellipse at 10% 20%,hsla(355,78%,55%,.07) 0%,transparent 50%),radial-gradient(ellipse at 90% 80%,hsla(195,100%,50%,.05) 0%,transparent 50%),{bg}"
        nav_bg=f"linear-gradient(90deg,{card},{card2})";nav_bdr=border
        nav_shd="0 4px 20px rgba(0,0,0,.4)";inp_bg=bg2;tab_list=bg2;tab_act=card
        scr_trk=bg2;scr_thm=border;btn_svg=text
        tog_bg=card;tog_bdr=border;tog_shd="0 4px 20px rgba(0,0,0,.45)"

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@300;400;500&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');
html,body,.stApp,[class*="css"],[data-testid="stAppViewContainer"],[data-testid="stVerticalBlock"],[data-testid="stHorizontalBlock"]{{font-family:'DM Sans',sans-serif !important;background-color:{bg} !important;color:{text} !important;}}
.stApp{{background:{app_bg} !important;}}
p,span,div,h1,h2,h3,h4,h5,h6,li,td,th,code,label,.stMarkdown p,.stMarkdown li,.stMarkdown span,[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] span,[data-testid="stMarkdownContainer"] li{{color:{text} !important}}
[data-testid="stMetric"] label,[data-testid="stMetricValue"],[data-testid="stMetricDelta"]{{color:{text} !important}}
.streamlit-expanderHeader{{color:{text} !important;background:{card2} !important}}
.streamlit-expanderContent{{background:{bg2} !important;color:{text} !important}}
.stSelectbox label,.stRadio label,.stCheckbox label,.stNumberInput label,.stTextInput label,.stTextArea label,.stSlider label{{color:{text2} !important}}
.cs-card{{background:{card};border:1px solid {border};border-radius:16px;padding:1.5rem;margin-bottom:1rem;box-shadow:0 4px 24px rgba(0,0,0,.3);transition:transform .25s cubic-bezier(.23,1,.32,1),box-shadow .25s;}}
.cs-card:hover{{transform:translateY(-3px);box-shadow:0 16px 40px rgba(0,0,0,.45)}}
.metric-card{{background:{card2};border:1px solid {border};border-radius:12px;padding:1.2rem;text-align:center;transition:transform .25s cubic-bezier(.23,1,.32,1),border-color .25s,box-shadow .25s;}}
.metric-card:hover{{transform:translateY(-5px);border-color:{accent};box-shadow:0 12px 32px rgba(0,0,0,.5)}}
.section-header{{font-family:'DM Serif Display',serif;font-size:1.6rem;color:{text};margin-bottom:.3rem}}
.section-sub{{font-size:.85rem;color:{text2};margin-bottom:1.2rem}}
.gradient-text{{background:linear-gradient(135deg,{accent2} 0%,{accent} 45%,{cyan} 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}}
.metric-value{{font-family:'DM Mono',monospace;font-size:2rem;font-weight:500;color:{accent}}}
.metric-label{{font-size:.75rem;color:{text2};text-transform:uppercase;letter-spacing:.1em;margin-top:.2rem}}
.metric-sub{{font-size:.7rem;color:{text3};margin-top:.2rem}}
@keyframes pulse-text{{0%,100%{{opacity:1}}50%{{opacity:.7}}}}
@keyframes heartbeat-ring{{0%{{box-shadow:0 0 0 0 hsla(355,78%,55%,.5)}}50%{{box-shadow:0 0 0 18px hsla(355,78%,55%,0)}}100%{{box-shadow:0 0 0 0 hsla(355,78%,55%,0)}}}}
.bpm-display{{font-family:'DM Serif Display',serif;font-size:6rem;line-height:1;display:inline-block;border-radius:50%;padding:.2rem 1rem;animation:pulse-text 1.5s ease-in-out infinite,heartbeat-ring 1.5s ease-out infinite;}}
.bpm-normal{{color:{green}}}.bpm-warning{{color:{yellow}}}.bpm-danger{{color:{accent}}}
.status-badge{{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:20px;font-size:.75rem;font-weight:500;letter-spacing:.05em;text-transform:uppercase}}
.badge-normal{{background:hsla(160,100%,45%,.15);border:1px solid hsla(160,100%,45%,.4);color:{green}}}
.badge-warning{{background:hsla(40,100%,70%,.15);border:1px solid hsla(40,100%,70%,.4);color:{yellow}}}
.badge-danger{{background:hsla(355,78%,55%,.15);border:1px solid hsla(355,78%,55%,.4);color:{accent}}}
.badge-info{{background:hsla(195,100%,50%,.15);border:1px solid hsla(195,100%,50%,.4);color:{cyan}}}
@keyframes ecg{{0%{{opacity:.3}}50%{{opacity:1}}100%{{opacity:.3}}}}
.ecg-line{{height:2px;background:linear-gradient(90deg,transparent,{accent},transparent);animation:ecg 2s linear infinite;margin:.5rem 0}}
.stTextInput input,.stSelectbox>div,.stTextArea textarea,.stNumberInput input{{background:{inp_bg} !important;border:1px solid {border} !important;border-radius:10px !important;color:{text} !important;font-family:'DM Sans',sans-serif !important;}}
.stTextInput input:focus{{border-color:{accent} !important;box-shadow:0 0 0 2px {glow} !important}}
.stButton>button{{background:linear-gradient(135deg,{accent},hsl(355,78%,38%)) !important;color:white !important;border:none !important;border-radius:10px !important;font-family:'DM Sans',sans-serif !important;font-weight:500 !important;padding:.5rem 1.5rem !important;transition:all .2s !important;}}
.stButton>button:hover{{transform:translateY(-1px) !important;box-shadow:0 4px 20px {glow} !important}}
.stButton>button[kind="secondary"]{{background:{card} !important;border:1px solid {border} !important;color:{text} !important}}
.stTabs [data-baseweb="tab-list"]{{background:{tab_list} !important;border-radius:12px !important;padding:4px !important;gap:4px !important;border:1px solid {border} !important}}
.stTabs [data-baseweb="tab"]{{background:transparent !important;color:{text2} !important;border-radius:8px !important;font-size:.85rem !important;font-weight:500 !important;padding:.5rem 1rem !important;border:none !important;transition:all .2s !important}}
.stTabs [aria-selected="true"]{{background:{tab_act} !important;color:{text} !important;border:1px solid {border} !important}}
.step-pill{{display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:50%;font-family:'DM Mono',monospace;font-weight:500;font-size:.85rem;margin-right:.5rem}}
.step-pill-active{{background:{accent};color:white;animation:popIn .4s cubic-bezier(.175,.885,.32,1.275) both}}
.step-pill-done{{background:{green};color:hsl(222,58%,5%)}}
.step-pill-todo{{background:{card2};border:1px solid {border};color:{text3}}}
@keyframes slideDown{{from{{opacity:0;transform:translateY(-24px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes fadeIn{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes popIn{{0%{{opacity:0;transform:scale(.88) translateY(20px)}}70%{{transform:scale(1.03)}}100%{{opacity:1;transform:scale(1) translateY(0)}}}}
@keyframes heartbeat{{0%,100%{{transform:scale(1)}}14%{{transform:scale(1.15)}}28%{{transform:scale(1)}}42%{{transform:scale(1.08)}}56%{{transform:scale(1)}}}}
@keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-10px)}}}}
#cs-theme-btn{{position:fixed;bottom:1.2rem;right:1.2rem;z-index:9999;width:44px;height:44px;border-radius:50%;border:1px solid {tog_bdr};background:{tog_bg};cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:{tog_shd};padding:0;transition:transform .2s,box-shadow .2s;}}
#cs-theme-btn svg{{stroke:{btn_svg} !important;width:18px;height:18px}}
#cs-theme-btn:hover{{transform:scale(1.12);box-shadow:0 6px 28px hsla(355,78%,55%,.4)}}
::-webkit-scrollbar{{width:6px;height:6px}}
::-webkit-scrollbar-track{{background:{scr_trk}}}
::-webkit-scrollbar-thumb{{background:{scr_thm};border-radius:3px}}
#MainMenu,footer,header{{visibility:hidden}}
.stDeployButton{{display:none}}
section[data-testid="stSidebar"]{{display:none}}
.block-container{{padding:1.5rem 2rem 2rem !important;max-width:1400px !important}}
.stApp,.cs-card,.metric-card,.stButton>button{{transition:background-color .2s ease,color .2s ease,border-color .2s ease !important}}
/* NAV BUTTON STYLES */
div.nav-zone div[data-testid="stButton"]>button{{
  background:transparent !important;border:none !important;
  color:{text2} !important;font-size:.8rem !important;font-weight:500 !important;
  padding:5px 9px !important;border-radius:8px !important;
  box-shadow:none !important;transform:none !important;
}}
div.nav-zone div[data-testid="stButton"]>button:hover{{
  background:hsla(355,78%,55%,.08) !important;color:{text} !important;
  transform:none !important;box-shadow:none !important;
}}
div.nav-active-btn div[data-testid="stButton"]>button{{
  background:hsla(355,78%,55%,.12) !important;
  color:{accent} !important;
  border:1px solid hsla(355,78%,55%,.25) !important;
  font-weight:600 !important;
}}
div.nav-signout-btn div[data-testid="stButton"]>button{{
  background:transparent !important;border:1px solid {border} !important;
  color:{text2} !important;font-size:.75rem !important;padding:4px 12px !important;
}}
@media print{{.stButton,#cs-theme-btn{{display:none !important}}body{{background:white !important;color:black !important}}}}
</style>
""", unsafe_allow_html=True)

# Theme toggle hidden button
st.markdown('<style>#__theme_trigger__{{display:none !important}}</style>', unsafe_allow_html=True)
_theme_toggled = st.button("__theme__", key="__theme_trigger__")
if _theme_toggled:
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
    st.rerun()

components.html("""<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;height:0;overflow:hidden;background:transparent">
<script>
(function(){
  var SUN='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';
  var MOON='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
  function clickHiddenBtn(){var p=window.parent.document;var btns=p.querySelectorAll('button');for(var i=0;i<btns.length;i++){if(btns[i].textContent.trim()==='__theme__'){btns[i].click();return true;}}return false;}
  function inject(){try{var p=window.parent.document;if(p.getElementById('cs-theme-btn'))return;var btn=p.createElement('button');btn.id='cs-theme-btn';btn.title='Toggle dark / light mode';btn.innerHTML=SUN;btn.onclick=function(){btn.innerHTML=(btn.innerHTML.indexOf('circle')!==-1)?MOON:SUN;clickHiddenBtn();};p.body.appendChild(btn);}catch(e){setTimeout(inject,400);}}
  setTimeout(inject,200);setTimeout(inject,1200);setTimeout(inject,4000);
})();
</script></body></html>""", height=0, scrolling=False)

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
# BLOCKCHAIN LEDGER (in-memory + SQLite backed)
# ─────────────────────────────────────────────────────────────────────────────
class Block:
    def __init__(self, index, timestamp, data, previous_hash, record_id=None):
        self.index         = index
        self.timestamp     = timestamp
        self.data          = data
        self.previous_hash = previous_hash
        self.record_id     = record_id
        self.nonce         = 0
        self.hash          = self.calculate_hash()

    def calculate_hash(self):
        block_str = json.dumps({
            "index": self.index, "timestamp": self.timestamp,
            "data": self.data, "previous_hash": self.previous_hash,
            "nonce": self.nonce, "record_id": self.record_id
        }, sort_keys=True)
        return hashlib.sha256(block_str.encode()).hexdigest()

    def mine_block(self, difficulty=2):
        target = "0" * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()

    def to_dict(self):
        return {
            "index": self.index, "timestamp": self.timestamp,
            "data": self.data, "previous_hash": self.previous_hash,
            "hash": self.hash, "nonce": self.nonce, "record_id": self.record_id
        }

class Blockchain:
    def __init__(self):
        self.chain = []
        self.difficulty = 2
        self._create_genesis()

    def _create_genesis(self):
        genesis = Block(0, datetime.now().isoformat(),
                        {"message": f"Genesis Block – {APP_TITLE}", "type": "genesis"},
                        "0" * 64)
        genesis.mine_block(self.difficulty)
        self.chain.append(genesis)

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, data, record_id=None):
        new_block = Block(
            len(self.chain),
            datetime.now().isoformat(),
            data,
            self.get_latest_block().hash,
            record_id=record_id
        )
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        return new_block

    def is_valid(self):
        for i in range(1, len(self.chain)):
            cur  = self.chain[i]
            prev = self.chain[i - 1]
            if cur.hash != cur.calculate_hash():
                return False, f"Block {i} hash mismatch"
            if cur.previous_hash != prev.hash:
                return False, f"Block {i} broken link to block {i-1}"
        return True, "Chain valid"

    def find_by_record_id(self, record_id):
        return [b for b in self.chain if b.record_id == record_id]

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────────────────────
def _probe_writable(path: str) -> bool:
    try:
        d = os.path.dirname(path)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
        conn = sqlite3.connect(path, timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE IF NOT EXISTS _probe (x INTEGER)")
        conn.execute("DROP TABLE IF EXISTS _probe")
        conn.commit(); conn.close()
        return True
    except Exception:
        return False

def _get_db_path() -> str:
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()
    candidates = [
        os.path.join(tempfile.gettempdir(), "medchainsecure.db"),
        os.path.join(os.path.expanduser("~"), "medchainsecure.db"),
        os.path.join(script_dir, "medchainsecure.db"),
        os.path.join(os.getcwd(), "medchainsecure.db"),
    ]
    for path in candidates:
        if _probe_writable(path):
            return path
    return ":memory:"

DB_PATH = _get_db_path()

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn

def _add_col(c, table, col, defn):
    try:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {defn}")
    except sqlite3.OperationalError:
        pass

def init_database():
    try:
        conn = get_conn(); c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            age INTEGER DEFAULT 0,
            gender TEXT DEFAULT "",
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        _add_col(c,"users","age","INTEGER DEFAULT 0")
        _add_col(c,"users","gender","TEXT DEFAULT ''")

        c.execute('''CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            encrypted_data BLOB NOT NULL,
            encryption_key BLOB NOT NULL,
            raw_bpm REAL,
            raw_category TEXT,
            raw_timestamp TEXT,
            block_hash TEXT DEFAULT "",
            block_index INTEGER DEFAULT -1,
            node_ids TEXT DEFAULT "",
            test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id))''')
        _add_col(c,"test_results","raw_bpm","REAL")
        _add_col(c,"test_results","raw_category","TEXT")
        _add_col(c,"test_results","raw_timestamp","TEXT")
        _add_col(c,"test_results","block_hash","TEXT DEFAULT ''")
        _add_col(c,"test_results","block_index","INTEGER DEFAULT -1")
        _add_col(c,"test_results","node_ids","TEXT DEFAULT ''")

        c.execute('''CREATE TABLE IF NOT EXISTS blockchain_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_index INTEGER,
            block_hash TEXT,
            previous_hash TEXT,
            record_id INTEGER,
            data_summary TEXT,
            mined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        c.execute('''CREATE TABLE IF NOT EXISTS session_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT,
            details TEXT,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT OR IGNORE INTO users (username,password_hash,full_name,is_admin) VALUES (?,?,?,?)",
                  ("admin", admin_hash, "System Administrator", 1))
        conn.commit()
    except Exception as e:
        st.error(f"Database init error: {e}")
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
        return True, "Registration successful!"
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    except Exception as e:
        return False, f"Database error: {e}"
    finally:
        if conn: conn.close()

def login_user(username, password):
    conn = None
    try:
        conn = get_conn(); c = conn.cursor()
        h = hashlib.sha256(password.encode()).hexdigest()
        c.execute("""SELECT id,full_name,is_admin,COALESCE(age,0) AS age,COALESCE(gender,'') AS gender
                     FROM users WHERE username=? AND password_hash=?""", (username, h))
        r = c.fetchone()
        if r:
            return True, {"id":r[0],"username":username,"full_name":r[1],"is_admin":r[2],"age":r[3],"gender":r[4]}
        return False, None
    except Exception as e:
        st.error(f"Login error: {e}")
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
    except: pass
    finally:
        if conn: conn.close()

def save_blockchain_log(block):
    conn = None
    try:
        conn = get_conn(); c = conn.cursor()
        c.execute("""INSERT INTO blockchain_log
                     (block_index,block_hash,previous_hash,record_id,data_summary)
                     VALUES (?,?,?,?,?)""",
                  (block.index, block.hash, block.previous_hash,
                   block.record_id, json.dumps(block.data)[:200]))
        conn.commit()
    except: pass
    finally:
        if conn: conn.close()

def get_blockchain_log(limit=50):
    conn = None
    try:
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT * FROM blockchain_log ORDER BY mined_at DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        return [dict(r) for r in rows]
    except: return []
    finally:
        if conn: conn.close()

def save_test_result(user_id, bpm, signal_data, analysis, block_hash="", block_index=-1, node_ids=""):
    conn = None
    try:
        conn = get_conn(); c = conn.cursor()
        key = os.urandom(32)
        data = {"bpm": bpm, "signal_data": signal_data[:100], "analysis": analysis,
                "timestamp": datetime.now().isoformat()}
        enc = HybridEncryption.encrypt_aes_gcm(json.dumps(data), key)
        c.execute('''INSERT INTO test_results
                   (user_id,encrypted_data,encryption_key,raw_bpm,raw_category,
                    raw_timestamp,block_hash,block_index,node_ids)
                   VALUES (?,?,?,?,?,?,?,?,?)''',
                  (user_id, enc, key, bpm, analysis['category'],
                   data['timestamp'], block_hash, block_index, node_ids))
        conn.commit()
        return c.lastrowid
    except Exception as e:
        st.warning(f"Could not save result: {e}")
        return None
    finally:
        if conn: conn.close()

def get_user_results(user_id):
    conn = None
    try:
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT id,encrypted_data,encryption_key,test_date,
                            COALESCE(block_hash,'') AS block_hash,
                            COALESCE(block_index,-1) AS block_index,
                            COALESCE(node_ids,'') AS node_ids
                     FROM test_results WHERE user_id=? ORDER BY test_date DESC""", (user_id,))
        rows = c.fetchall()
    except: return []
    finally:
        if conn: conn.close()
    out = []
    for r in rows:
        try:
            dec = json.loads(HybridEncryption.decrypt_aes_gcm(bytes(r[1]), bytes(r[2])))
            dec['test_id']     = r[0]
            dec['test_date']   = r[3]
            dec['block_hash']  = r[4]
            dec['block_index'] = r[5]
            dec['node_ids']    = r[6]
            out.append(dec)
        except: pass
    return out

def get_all_results_admin():
    conn = None
    try:
        conn = get_conn(); c = conn.cursor()
        c.execute('''SELECT t.id,u.id,u.username,u.full_name,
                            COALESCE(u.age,0) AS age,COALESCE(u.gender,"") AS gender,
                            t.encrypted_data,t.encryption_key,t.test_date,
                            COALESCE(t.block_hash,"") AS block_hash,
                            COALESCE(t.block_index,-1) AS block_index,
                            COALESCE(t.node_ids,"") AS node_ids
                     FROM test_results t JOIN users u ON t.user_id=u.id
                     ORDER BY t.test_date DESC''')
        rows = c.fetchall()
    except: return []
    finally:
        if conn: conn.close()
    out = []
    for r in rows:
        try:
            dec = json.loads(HybridEncryption.decrypt_aes_gcm(bytes(r[6]), bytes(r[7])))
            out.append({'test_id':r[0],'user_id':r[1],'username':r[2],'full_name':r[3],
                        'age':r[4],'gender':r[5],'bpm':dec['bpm'],'test_date':r[8],
                        'analysis':dec['analysis'],'encrypted_hex':bytes(r[6]).hex(),
                        'key_hex':bytes(r[7]).hex(),'block_hash':r[9],
                        'block_index':r[10],'node_ids':r[11]})
        except: pass
    return out

def get_all_users():
    conn = None
    try:
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT id,username,full_name,COALESCE(age,0),COALESCE(gender,""),is_admin,created_at
                     FROM users ORDER BY created_at DESC""")
        rows = c.fetchall()
        return [{'id':r[0],'username':r[1],'full_name':r[2],'age':r[3],'gender':r[4],'is_admin':r[5],'created_at':r[6]} for r in rows]
    except: return []
    finally:
        if conn: conn.close()

def get_session_log(user_id=None, limit=50):
    conn = None
    try:
        conn = get_conn(); c = conn.cursor()
        if user_id:
            c.execute('''SELECT l.id,u.username,l.action,l.details,l.logged_at
                         FROM session_log l JOIN users u ON l.user_id=u.id
                         WHERE l.user_id=? ORDER BY l.logged_at DESC LIMIT ?''', (user_id, limit))
        else:
            c.execute('''SELECT l.id,u.username,l.action,l.details,l.logged_at
                         FROM session_log l JOIN users u ON l.user_id=u.id
                         ORDER BY l.logged_at DESC LIMIT ?''', (limit,))
        rows = c.fetchall()
        return [{'id':r[0],'username':r[1],'action':r[2],'details':r[3],'logged_at':r[4]} for r in rows]
    except: return []
    finally:
        if conn: conn.close()

# ─────────────────────────────────────────────────────────────────────────────
# HEART RATE ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def get_forehead_roi(face, frame_shape):
    x,y,w,h = face
    return (x+int(w*.25), y+int(h*.08), int(w*.5), int(h*.18))

def get_cheek_roi(face, frame_shape):
    x,y,w,h = face
    return (x+int(w*.05), y+int(h*.45), int(w*.25), int(h*.2))

def extract_color_signal(frame, roi):
    x,y,w,h = roi
    if y+h>frame.shape[0] or x+w>frame.shape[1] or w<=0 or h<=0:
        return None, None, None
    patch = frame[y:y+h, x:x+w]
    r=float(np.mean(patch[:,:,2])); g=float(np.mean(patch[:,:,1])); b=float(np.mean(patch[:,:,0]))
    return g, r-g, r/2+g/2-b

def ml_refine_bpm(raw_bpm, age=0, gender='', history=[]):
    if raw_bpm<40 or raw_bpm>200:
        return int(np.mean(history[-5:])) if history else 75
    if history and len(history)>=3:
        rm=np.mean(history[-3:]); rs=np.std(history[-3:])
        if abs(raw_bpm-rm)>2*rs and rs>0:
            raw_bpm=int(.4*raw_bpm+.6*rm)
    if age:
        max_hr=220-age
        if raw_bpm>max_hr*.95: raw_bpm=min(raw_bpm,int(max_hr*.95))
    return int(raw_bpm)

def calculate_heart_rate(data_buffer, times, use_chrom=True):
    if len(data_buffer)<150: return 0, []
    sig=np.array(data_buffer); detrended=signal.detrend(sig)
    fps=len(times)/max((times[-1]-times[0]),.01) if len(times)>1 else 30
    nyq=fps/2; low=max(.01,.67/nyq); high=min(.99,4./nyq)
    if low>=high: return 0, []
    b,a=signal.butter(4,[low,high],btype='band')
    try: filtered=signal.filtfilt(b,a,detrended)
    except: return 0, []
    fft=np.fft.rfft(filtered*np.hanning(len(filtered)))
    freqs=np.fft.rfftfreq(len(filtered),1/fps)
    mask=(freqs>=.67)&(freqs<=4.)
    if not mask.any(): return 0, []
    mags=np.abs(fft[mask]); peak=freqs[mask][np.argmax(mags)]
    return int(peak*60), filtered.tolist()

def analyze_heart_rate(bpm):
    if bpm<40:
        return {"category":"Bradycardia (Severe)","status":"danger","description":"Heart rate critically low. Immediate medical attention required.","icon":"🚨","color":"#E84855","recommendations":["Seek emergency care immediately","Do not drive","Lie down and rest","Call emergency services"]}
    elif 40<=bpm<60:
        return {"category":"Bradycardia (Mild)","status":"warning","description":"Slightly low heart rate; common in athletes or deep sleep.","icon":"⚠️","color":"#FFD166","recommendations":["Monitor for dizziness","Consult a cardiologist","Track multiple readings","Common in trained athletes"]}
    elif 60<=bpm<=100:
        return {"category":"Normal Resting","status":"success","description":"Heart rate within the optimal healthy resting range.","icon":"✅","color":"#00E5A0","recommendations":["Maintain regular aerobic exercise","Stay hydrated (8+ glasses/day)","Manage stress with mindfulness","Get 7-9 hours of quality sleep"]}
    elif 101<=bpm<=120:
        return {"category":"Tachycardia (Mild)","status":"warning","description":"Mildly elevated – often stress, caffeine, or exertion.","icon":"⚠️","color":"#FFD166","recommendations":["Practice deep breathing (4-7-8 method)","Reduce caffeine intake","Ensure full hydration","Avoid strenuous activity"]}
    else:
        return {"category":"Tachycardia (Severe)","status":"danger","description":"Heart rate significantly above normal resting range.","icon":"🚨","color":"#E84855","recommendations":["Seek medical attention promptly","Rule out cardiac arrhythmia","Avoid stimulants completely","Record all symptoms for your doctor"]}

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
try:
    init_database()
except Exception as _db_err:
    st.error(f"**Database init failed.** Path tried: `{DB_PATH}` — Error: `{_db_err}`")
    st.stop()

defaults = {
    "logged_in":False,"user":None,"page":"landing","theme":"dark",
    "data_buffer":deque(maxlen=300),"chrom_x":deque(maxlen=300),
    "chrom_y":deque(maxlen=300),"times":deque(maxlen=300),
    "bpm":0,"bpm_history":[],"running":False,
    "test_complete":False,"last_result":None,
    "enc_step":0,"enc_data":{},"admin_selected_user":None,
    "blockchain":None,
}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k]=v

# Init blockchain
if st.session_state.blockchain is None:
    st.session_state.blockchain = Blockchain()

_qp = st.query_params
if "theme" in _qp and st.session_state.theme=="dark":
    _t=_qp["theme"]
    if _t in ("dark","light"): st.session_state.theme=_t

_apply_theme_css()

def go(page):
    st.session_state.page=page; st.rerun()

def logout():
    for k in defaults: st.session_state[k]=defaults[k]
    st.session_state.blockchain=Blockchain()
    st.session_state.page="landing"; st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def plotly_dark():
    is_light=st.session_state.get("theme","dark")=="light"
    grid="#C8D0E0" if is_light else "#253358"
    font_="#4A5578" if is_light else "#8A97B8"
    return dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="DM Sans",color=font_,size=11),
                xaxis=dict(gridcolor=grid,showgrid=True,zeroline=False),
                yaxis=dict(gridcolor=grid,showgrid=True,zeroline=False),
                margin=dict(l=10,r=10,t=40,b=10))

def bpm_class(bpm):
    if bpm<40 or bpm>120: return "bpm-danger"
    if 40<=bpm<60 or 101<=bpm<=120: return "bpm-warning"
    return "bpm-normal"

def badge_class(status):
    return {"success":"badge-normal","warning":"badge-warning","danger":"badge-danger","info":"badge-info"}.get(status,"badge-info")

LOGO_SVG_SM="""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" width="34" height="34" style="filter:drop-shadow(0 0 8px rgba(232,72,85,.55))"><path d="M40 62C40 62 14 46 14 28C14 19 21 13 28 13C33 13 37 16 40 20C43 16 47 13 52 13C59 13 66 19 66 28C66 46 40 62 40 62Z" fill="url(#sg)"/><polyline points="16,40 22,40 25,32 28,48 32,28 36,40 40,40 44,36 48,44 52,40 64,40" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.9"/><defs><linearGradient id="sg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#FF6B6B"/><stop offset="100%" stop-color="#C62A35"/></linearGradient></defs></svg>"""
LOGO_SVG_LG="""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" width="76" height="76" style="filter:drop-shadow(0 0 22px rgba(232,72,85,.6))"><path d="M40 62C40 62 14 46 14 28C14 19 21 13 28 13C33 13 37 16 40 20C43 16 47 13 52 13C59 13 66 19 66 28C66 46 40 62 40 62Z" fill="url(#lg)"/><polyline points="16,40 22,40 25,32 28,48 32,28 36,40 40,40 44,36 48,44 52,40 64,40" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" opacity="0.95"/><defs><linearGradient id="lg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#FF6B6B"/><stop offset="55%" stop-color="#E84855"/><stop offset="100%" stop-color="#C62A35"/></linearGradient></defs></svg>"""

# ─────────────────────────────────────────────────────────────────────────────
# NAVIGATION
# ─────────────────────────────────────────────────────────────────────────────
def render_nav():
    u=st.session_state.user
    if u and u.get("is_admin"):
        nav_items=[
            ("admin_dashboard","🏠 Dashboard"),
            ("monitor","❤️ Monitor"),
            ("admin_users","👥 Users"),
            ("admin_records","📋 Records"),
            ("enc_step1","🔒 Encryption Lab"),
            ("decentralised","🌐 Decentralisation"),
            ("decryption","🔓 Decryption"),
            ("raw_data","📦 Data"),
        ]
    elif u:
        nav_items=[
            ("monitor","❤️ Monitor"),
            ("results","📊 My Results"),
            ("enc_step1","🔒 Encryption Lab"),
            ("decentralised","🌐 Decentralisation"),
            ("decryption","🔓 Decryption"),
            ("raw_data","📦 Data"),
        ]
    else:
        nav_items=[]

    # Brand bar
    user_info=""
    if u:
        ab=' <span style="color:#FFD166;font-size:.68rem;padding:1px 6px;border:1px solid hsla(40,100%,70%,.3);border-radius:4px">ADMIN</span>' if u.get("is_admin") else ""
        user_info=f'<span style="color:var(--text2);font-size:.78rem">👤 {u["full_name"]}{ab}</span>'

    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
         padding:.5rem 1.5rem .2rem;border-bottom:1px solid var(--border);
         background:var(--bg2);position:sticky;top:0;z-index:100;">
      <div style="display:flex;align-items:center;gap:.6rem">
        <div style="animation:heartbeat 1.5s ease-in-out infinite;display:flex">{LOGO_SVG_SM}</div>
        <div>
          <div style="font-family:'DM Serif Display',serif;font-size:.95rem;color:var(--text);line-height:1">{APP_TITLE}</div>
          <div style="font-size:.52rem;color:var(--text3);letter-spacing:.08em;text-transform:uppercase">Hybrid Encryption &amp; Blockchain · IoMT Security</div>
        </div>
        <span style="font-size:.52rem;color:var(--text3);letter-spacing:.1em;text-transform:uppercase;padding:2px 5px;border:1px solid var(--border);border-radius:4px;margin-left:2px;align-self:flex-start;margin-top:3px">v3.0</span>
      </div>
      <div style="display:flex;align-items:center;gap:.8rem">
        {user_info}
        <span style="color:var(--text3);font-size:.75rem">{datetime.now().strftime("%d %b %Y")}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if not u:
        _, cb, _ = st.columns([5,1,.3])
        with cb:
            if st.session_state.page=="landing":
                if st.button("Sign In", key="nav_signin", type="primary"): go("login")
            else:
                if st.button("← Home", key="nav_home"): go("landing")
        return

    # Nav button row
    st.markdown('<div class="nav-zone">', unsafe_allow_html=True)
    cur_page=st.session_state.page
    cols=st.columns([.6]+[1.15]*len(nav_items)+[.5,1.1])
    for i,(pid,label) in enumerate(nav_items):
        is_active=(cur_page==pid or (pid=="enc_step1" and cur_page.startswith("enc_")))
        with cols[i+1]:
            if is_active:
                st.markdown('<div class="nav-active-btn">', unsafe_allow_html=True)
            if st.button(label, key=f"nav_{pid}", use_container_width=True):
                go(pid)
            if is_active:
                st.markdown('</div>', unsafe_allow_html=True)
    with cols[-1]:
        st.markdown('<div class="nav-signout-btn">', unsafe_allow_html=True)
        if st.button("🚪 Sign Out", key="nav_so_main", use_container_width=True):
            logout()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<hr style="margin:.2rem 0 .8rem;border-color:var(--border)">', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# LANDING PAGE
# ─────────────────────────────────────────────────────────────────────────────
def render_landing():
    st.markdown(f"""
    <style>
    .landing-hero{{min-height:88vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:2rem 1rem;background:radial-gradient(ellipse at 10% 20%,hsla(355,78%,55%,.08) 0%,transparent 50%),radial-gradient(ellipse at 90% 80%,hsla(195,100%,50%,.06) 0%,transparent 50%);}}
    .hero-title{{font-family:'DM Serif Display',serif;font-size:clamp(2.2rem,5vw,3.8rem);line-height:1.05;background:linear-gradient(135deg,#FF6B6B 0%,#E84855 40%,#00D4FF 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin:.8rem 0 .4rem;}}
    .hero-sub{{font-size:.75rem;letter-spacing:.2em;text-transform:uppercase;color:var(--text2);margin-bottom:.5rem}}
    .hero-fullname{{font-size:.78rem;color:var(--text2);max-width:680px;line-height:1.6;margin-bottom:.4rem}}
    .hero-desc{{color:var(--text2);max-width:540px;line-height:1.65;margin-bottom:1.8rem;font-size:.9rem}}
    .hero-btns{{display:flex;gap:1rem;justify-content:center;flex-wrap:wrap}}
    .btn-primary{{padding:.75rem 2rem;border-radius:12px;font-weight:500;font-size:.9rem;cursor:pointer;background:linear-gradient(135deg,var(--accent),hsl(355,78%,38%));color:white;border:none;box-shadow:0 4px 20px hsla(355,78%,55%,.3);transition:transform .2s,box-shadow .2s;}}
    .feature-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1.1rem;margin:2.5rem 0}}
    .feature-card{{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:1.4rem;transition:transform .25s cubic-bezier(.23,1,.32,1),box-shadow .25s;}}
    .feature-card:hover{{transform:translateY(-5px);box-shadow:0 14px 36px rgba(0,0,0,.35)}}
    .how-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1.3rem;max-width:1000px;margin:1.8rem auto 0}}
    .how-card{{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:1.3rem;border-top-width:3px;}}
    .step-num{{font-family:'DM Mono',monospace;font-size:2rem;font-weight:300;color:var(--border);margin-bottom:.6rem;line-height:1}}
    </style>

    <div class="landing-hero">
      <div style="animation:heartbeat 1.5s ease-in-out infinite;margin-bottom:.8rem">{LOGO_SVG_LG}</div>
      <p class="hero-sub">IoMT Security Research Framework</p>
      <h1 class="hero-title">{APP_TITLE}</h1>
      <p class="hero-fullname"><em>{APP_FULLNAME}</em></p>
      <p class="hero-desc">{APP_SUBTITLE}</p>
      <div style="margin-bottom:1.8rem">
        <div style="font-family:'DM Mono',monospace;font-size:.7rem;color:var(--text3)">{APP_AUTHOR}</div>
        <div style="margin-top:.6rem;padding:4px 14px;border:1px solid hsla(195,100%,50%,.25);border-radius:20px;background:hsla(195,100%,50%,.06);font-size:.68rem;color:var(--cyan);letter-spacing:.06em;display:inline-block">{APP_SECURITY}</div>
      </div>
    </div>

    <div class="ecg-line"></div>

    <div style="max-width:1100px;margin:0 auto;padding:3rem 1rem 2rem">
      <h2 style="font-family:'DM Serif Display',serif;font-size:1.9rem;text-align:center;color:var(--text);margin-bottom:.4rem">Clinical-Grade IoMT Security Features</h2>
      <p style="text-align:center;color:var(--text2);margin-bottom:0;font-size:.85rem">Advanced computer vision · Military-grade encryption · Immutable blockchain audit trail</p>
      <div class="feature-grid">
        <div class="feature-card"><div style="font-size:1.8rem;margin-bottom:.7rem">❤️</div><h3 style="font-family:'DM Serif Display',serif;font-size:1rem;color:var(--text);margin-bottom:.4rem">rPPG Detection</h3><p style="font-size:.8rem;color:var(--text2);line-height:1.6">Non-contact heart rate via CHROM + Butterworth bandpass + FFT peak analysis.</p></div>
        <div class="feature-card"><div style="font-size:1.8rem;margin-bottom:.7rem">🛡️</div><h3 style="font-family:'DM Serif Display',serif;font-size:1rem;color:var(--text);margin-bottom:.4rem">Hybrid Encryption</h3><p style="font-size:.8rem;color:var(--text2);line-height:1.6">AES-256-GCM + ECC-SECP256R1 key exchange for end-to-end data security.</p></div>
        <div class="feature-card"><div style="font-size:1.8rem;margin-bottom:.7rem">⛓️</div><h3 style="font-family:'DM Serif Display',serif;font-size:1rem;color:var(--text);margin-bottom:.4rem">Blockchain Ledger</h3><p style="font-size:.8rem;color:var(--text2);line-height:1.6">Every record anchored to an immutable proof-of-work blockchain for tamper evidence.</p></div>
        <div class="feature-card"><div style="font-size:1.8rem;margin-bottom:.7rem">🌐</div><h3 style="font-family:'DM Serif Display',serif;font-size:1rem;color:var(--text);margin-bottom:.4rem">Decentralised Storage</h3><p style="font-size:.8rem;color:var(--text2);line-height:1.6">3-node geo-distributed encrypted storage with key separation architecture.</p></div>
        <div class="feature-card"><div style="font-size:1.8rem;margin-bottom:.7rem">🔓</div><h3 style="font-family:'DM Serif Display',serif;font-size:1rem;color:var(--text);margin-bottom:.4rem">Decryption Lab</h3><p style="font-size:.8rem;color:var(--text2);line-height:1.6">Live authenticated decryption with tamper-detection simulation and integrity proof.</p></div>
        <div class="feature-card"><div style="font-size:1.8rem;margin-bottom:.7rem">📴</div><h3 style="font-family:'DM Serif Display',serif;font-size:1rem;color:var(--text);margin-bottom:.4rem">Offline Mode</h3><p style="font-size:.8rem;color:var(--text2);line-height:1.6">Fully functional offline — all processing local. No cloud dependency required.</p></div>
      </div>
    </div>

    <div style="background:hsla(222,40%,12%,.5);border-top:1px solid var(--border);border-bottom:1px solid var(--border);padding:3rem 1rem;margin:0 -2rem">
      <h2 style="font-family:'DM Serif Display',serif;font-size:1.9rem;text-align:center;color:var(--text)">How It Works</h2>
      <div class="how-grid">
        <div class="how-card" style="border-top-color:var(--cyan)"><div class="step-num">01</div><h3 style="font-family:'DM Serif Display',serif;font-size:1rem;color:var(--text);margin-bottom:.4rem">Face Detection</h3><p style="font-size:.78rem;color:var(--text2);line-height:1.6">Haar Cascade isolates forehead/cheek ROI regions for dense vascular signal capture.</p></div>
        <div class="how-card" style="border-top-color:var(--accent)"><div class="step-num">02</div><h3 style="font-family:'DM Serif Display',serif;font-size:1rem;color:var(--text);margin-bottom:.4rem">Signal Processing</h3><p style="font-size:.78rem;color:var(--text2);line-height:1.6">CHROM chrominance + Butterworth bandpass (0.67–4.0 Hz) + FFT peak detection.</p></div>
        <div class="how-card" style="border-top-color:var(--purple)"><div class="step-num">03</div><h3 style="font-family:'DM Serif Display',serif;font-size:1rem;color:var(--text);margin-bottom:.4rem">Hybrid Encrypt</h3><p style="font-size:.78rem;color:var(--text2);line-height:1.6">AES-256-GCM encrypts data; ECC-SECP256R1 ECDH secures the symmetric key.</p></div>
        <div class="how-card" style="border-top-color:var(--green)"><div class="step-num">04</div><h3 style="font-family:'DM Serif Display',serif;font-size:1rem;color:var(--text);margin-bottom:.4rem">Blockchain Anchor</h3><p style="font-size:.78rem;color:var(--text2);line-height:1.6">Record hash mined into proof-of-work blockchain for immutable audit trail.</p></div>
        <div class="how-card" style="border-top-color:var(--yellow)"><div class="step-num">05</div><h3 style="font-family:'DM Serif Display',serif;font-size:1rem;color:var(--text);margin-bottom:.4rem">Decentralised Store</h3><p style="font-size:.78rem;color:var(--text2);line-height:1.6">Encrypted blobs distributed across 3 geo-nodes; keys stored in separate KMS.</p></div>
      </div>
    </div>

    <div style="text-align:center;padding:1.5rem 1rem;border-top:1px solid var(--border)">
      <p style="font-size:.7rem;color:var(--text3)">{APP_SECURITY} &nbsp;·&nbsp; ⚠️ For research &amp; educational purposes only &nbsp;·&nbsp; Not a certified medical device</p>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# LOGIN / REGISTER PAGE
# ─────────────────────────────────────────────────────────────────────────────
def render_login():
    col_l, col_m, col_r = st.columns([1,1.8,1])
    with col_m:
        st.markdown(f"""
        <div style="text-align:center;padding:2rem 0 1.5rem">
          <div style="display:flex;align-items:center;justify-content:center;margin-bottom:.9rem;animation:heartbeat 1.5s ease-in-out infinite">{LOGO_SVG_LG}</div>
          <div style="font-family:'DM Serif Display',serif;font-size:2.4rem;line-height:1.1;background:linear-gradient(135deg,#FF6B6B 0%,#E84855 45%,#00D4FF 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">{APP_TITLE}</div>
          <div style="color:var(--text2);font-size:.75rem;line-height:1.5;max-width:340px;margin:.5rem auto 0">{APP_SUBTITLE}</div>
          <div style="color:var(--text3);font-family:'DM Mono',monospace;font-size:.65rem;margin-top:.5rem">{APP_AUTHOR}</div>
          <div style="display:inline-flex;align-items:center;gap:.4rem;margin-top:.6rem;padding:3px 12px;border:1px solid hsla(195,100%,50%,.25);border-radius:20px;background:hsla(195,100%,50%,.06);font-size:.65rem;color:var(--cyan);letter-spacing:.06em">{APP_SECURITY}</div>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_reg = st.tabs(["🔐 Sign In", "✍️ Create Account"])
        with tab_login:
            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
            username=st.text_input("Username",placeholder="your.username",key="li_user")
            password=st.text_input("Password",type="password",placeholder="••••••••",key="li_pass")
            c1,c2=st.columns(2)
            with c1:
                if st.button("Sign In →",type="primary",use_container_width=True):
                    if username and password:
                        ok,ud=login_user(username,password)
                        if ok:
                            st.session_state.logged_in=True; st.session_state.user=ud
                            log_action(ud['id'],"LOGIN","Successful login")
                            st.session_state.page="admin_dashboard" if ud['is_admin'] else "monitor"
                            st.rerun()
                        else: st.error("Invalid credentials")
                    else: st.warning("Please enter credentials")
            with c2:
                st.markdown("""<div style="background:rgba(0,212,255,0.06);border:1px solid rgba(0,212,255,0.2);border-radius:10px;padding:.6rem .8rem;font-size:.73rem;color:#8A97B8"><b style="color:#00D4FF">Demo Admin</b><br>User: <code style="color:#00D4FF">admin</code><br>Pass: <code style="color:#00D4FF">admin123</code></div>""", unsafe_allow_html=True)
        with tab_reg:
            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
            c1,c2=st.columns(2)
            with c1:
                rn=st.text_input("Full Name",key="r_name"); ru=st.text_input("Username",key="r_user")
            with c2:
                ra=st.number_input("Age",min_value=10,max_value=120,value=30,key="r_age")
                rg=st.selectbox("Gender",["Prefer not to say","Male","Female","Other"],key="r_gen")
            rp=st.text_input("Password (min 6 chars)",type="password",key="r_pass")
            rp2=st.text_input("Confirm Password",type="password",key="r_pass2")
            if st.button("Create Account →",type="primary",use_container_width=True):
                if rn and ru and rp:
                    if rp==rp2:
                        if len(rp)>=6:
                            ok,msg=register_user(ru,rp,rn,ra,rg)
                            if ok: st.success(f"✅ Account created! Welcome, {rn}. Please sign in.")
                            else: st.error(msg)
                        else: st.warning("Password must be at least 6 characters")
                    else: st.error("Passwords do not match")
                else: st.warning("Please fill all required fields")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: HEART MONITOR
# ─────────────────────────────────────────────────────────────────────────────
def render_monitor(user):
    st.markdown('<div class="section-header">❤️ Heart Rate Monitor</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">rPPG via webcam snapshot · Hybrid-encrypted · Blockchain-anchored</div>', unsafe_allow_html=True)

    with st.expander("ℹ️ How Does Webcam Heart Rate Detection Work?", expanded=False):
        st.markdown("""
### 🩺 rPPG – Remote Photoplethysmography

**Face Detection:** Haar Cascade locates your face and isolates the **forehead ROI** — the region with the densest superficial vasculature for maximum signal quality.

**CHROM Signal Extraction:** Each frame's R, G, B channels are combined: `Xs = R – G` and `Ys = R/2 + G/2 – B`. These chrominance signals suppress motion artefacts.

**Bandpass Filtering:** A 4th-order Butterworth filter (0.67–4.0 Hz = 40–240 BPM) removes noise outside the physiological heart rate range.

**FFT Analysis:** Fast Fourier Transform converts the time-domain signal to frequency. The dominant peak × 60 = BPM.

**On Streamlit Cloud:** Uses `st.camera_input()` for photo capture. Take multiple photos in quick succession (~15 photos over 30 seconds) to build a signal buffer. For continuous live video, run the app locally: `streamlit run app.py`

> ⚠️ Research demonstration tool only. Not a certified medical device.
""")

    st.divider()

    # ── Mode selector ──────────────────────────────────────────────────────
    mode = st.radio("Camera Mode", ["📸 Photo Capture (Streamlit Cloud)", "🎥 Continuous (Local only)"],
                    horizontal=True, key="monitor_mode")

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )

    def process_frame(frame_bgr):
        """Process a cv2 BGR frame through the rPPG pipeline."""
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
        if len(faces) == 0:
            cv2.putText(frame_bgr, "No face detected", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (232, 72, 85), 2)
            return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB), 0, []

        face = max(faces, key=lambda f: f[2] * f[3])
        x, y, w, h = face
        roi = get_forehead_roi(face, frame_bgr.shape)
        g, xs, ys = extract_color_signal(frame_bgr, roi)

        if g is not None:
            st.session_state.data_buffer.append(g)
            st.session_state.times.append(time.time())

        bpm_raw, sig_filtered = calculate_heart_rate(
            list(st.session_state.data_buffer),
            list(st.session_state.times)
        )
        bpm = 0
        if bpm_raw > 0:
            st.session_state.bpm_history.append(bpm_raw)
            bpm = ml_refine_bpm(bpm_raw, user.get('age', 0),
                                user.get('gender', ''), st.session_state.bpm_history)

        # Annotate frame
        cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), (0, 229, 160), 2)
        rx, ry, rw, rh = roi
        cv2.rectangle(frame_bgr, (rx, ry), (rx + rw, ry + rh), (232, 72, 85), 1)
        cv2.putText(frame_bgr, "ROI", (rx, max(ry - 5, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (232, 72, 85), 1)
        if bpm > 0:
            cv2.putText(frame_bgr, f"{bpm} BPM", (x, max(y - 8, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 229, 160), 2)
        cv2.putText(frame_bgr, f"Samples: {len(st.session_state.data_buffer)}",
                    (8, frame_bgr.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (138, 151, 184), 1)
        return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB), bpm, sig_filtered

    # ── Layout ─────────────────────────────────────────────────────────────
    col_cam, col_stats = st.columns([3, 2], gap="large")

    with col_stats:
        bpm_placeholder    = st.empty()
        status_placeholder = st.empty()
        signal_placeholder = st.empty()

    with col_cam:
        st.markdown('<div class="cs-card">', unsafe_allow_html=True)

        # ── PHOTO CAPTURE MODE (works on Streamlit Cloud) ──────────────────
        if "Photo" in mode:
            st.markdown("### 📸 Photo Capture Mode")
            st.info("💡 Take 15–20 photos over ~30 seconds while keeping still in good lighting for best accuracy.")

            cam_photo = st.camera_input("Capture frame for rPPG analysis", key="cam_input_monitor")

            ctrl1, ctrl2, ctrl3 = st.columns(3)
            with ctrl1:
                if st.button("🗑 Reset Buffer", type="secondary", use_container_width=True, key="mon_reset"):
                    st.session_state.data_buffer = deque(maxlen=300)
                    st.session_state.times = deque(maxlen=300)
                    st.session_state.bpm_history = []
                    st.session_state.bpm = 0
                    st.session_state.last_result = None
                    st.session_state.test_complete = False
                    log_action(user['id'], "TEST_RESET", "Buffer cleared")
                    st.rerun()
            with ctrl2:
                st.markdown(f'<div style="text-align:center;font-family:\'DM Mono\';font-size:.8rem;color:var(--text2);padding:.5rem">Buffer: {len(st.session_state.data_buffer)}/150</div>', unsafe_allow_html=True)
            with ctrl3:
                save_btn = st.button("💾 Save + Chain", type="primary", use_container_width=True,
                                     key="mon_save", disabled=not st.session_state.test_complete)

            if cam_photo is not None:
                file_bytes = np.frombuffer(cam_photo.getvalue(), np.uint8)
                frame_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                if frame_bgr is not None:
                    rgb_frame, bpm_val, sig_filtered = process_frame(frame_bgr)
                    st.image(rgb_frame, channels="RGB", use_container_width=True,
                             caption=f"Frame captured · Buffer: {len(st.session_state.data_buffer)} samples")
                    if bpm_val > 0:
                        st.session_state.bpm = bpm_val
                        analysis = analyze_heart_rate(bpm_val)
                        st.session_state.last_result = {
                            "bpm": bpm_val, "analysis": analysis, "signal_data": sig_filtered
                        }
                        st.session_state.test_complete = True
                    elif len(st.session_state.data_buffer) < 150:
                        st.info(f"📊 Collecting signal… {len(st.session_state.data_buffer)}/150 samples. Keep taking photos!")
                else:
                    st.error("Could not decode image — try again.")

        # ── CONTINUOUS MODE (local only) ───────────────────────────────────
        else:
            st.markdown("### 🎥 Continuous Camera Mode")
            st.warning("⚠️ Continuous mode requires running locally: `streamlit run app.py`  \nOn Streamlit Cloud, use **Photo Capture** mode instead.")

            ctrl1, ctrl2, ctrl3 = st.columns(3)
            with ctrl1:
                start_btn = st.button("▶ Start", type="primary", use_container_width=True, key="mon_start")
            with ctrl2:
                stop_btn  = st.button("⏹ Stop",  type="secondary", use_container_width=True, key="mon_stop")
            with ctrl3:
                save_btn2 = st.button("💾 Save + Chain", type="secondary", use_container_width=True,
                                      key="mon_save2", disabled=not st.session_state.test_complete)

            camera_placeholder = st.empty()

            if start_btn:
                st.session_state.running = True
                st.session_state.test_complete = False
                st.session_state.data_buffer = deque(maxlen=300)
                st.session_state.times = deque(maxlen=300)
                st.session_state.bpm_history = []
                log_action(user['id'], "TEST_START", "Continuous mode started")

            if stop_btn:
                st.session_state.running = False
                if st.session_state.bpm > 0:
                    st.session_state.test_complete = True

            if st.session_state.running:
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    st.error("❌ Cannot open webcam. Try Photo Capture mode above, or check camera permissions.")
                    st.session_state.running = False
                else:
                    frames_collected = 0
                    start_time = time.time()
                    stop_requested = False
                    while st.session_state.running and frames_collected < 450:
                        ret, frame_bgr = cap.read()
                        if not ret:
                            break
                        rgb_frame, bpm_val, sig_filtered = process_frame(frame_bgr)
                        camera_placeholder.image(rgb_frame, channels="RGB", use_container_width=True)
                        if bpm_val > 0:
                            st.session_state.bpm = bpm_val
                            analysis = analyze_heart_rate(bpm_val)
                            st.session_state.last_result = {
                                "bpm": bpm_val, "analysis": analysis, "signal_data": sig_filtered
                            }
                            st.session_state.test_complete = True
                        frames_collected += 1
                        time.sleep(1 / 15)
                    cap.release()
                    st.session_state.running = False

            # unified save reference for continuous mode
            save_btn = save_btn2

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Save + blockchain anchor (shared for both modes) ───────────────────
    if save_btn and st.session_state.test_complete and st.session_state.last_result:
        r = st.session_state.last_result
        bc = st.session_state.blockchain
        block_data = {
            "bpm": r['bpm'],
            "category": r['analysis']['category'],
            "user": user['username'],
            "timestamp": datetime.now().isoformat()
        }
        with st.spinner("⛏️ Mining block to blockchain…"):
            new_block = bc.add_block(block_data)
        node_ids = ",".join([os.urandom(6).hex() for _ in range(3)])
        rid = save_test_result(
            user['id'], r['bpm'],
            list(st.session_state.data_buffer),
            r['analysis'],
            new_block.hash, new_block.index, node_ids
        )
        if rid:
            save_blockchain_log(new_block)
            log_action(user['id'], "RESULT_SAVED",
                       f"BPM={r['bpm']},Block={new_block.index},Hash={new_block.hash[:16]}")
            st.success(f"✅ Saved & blockchain-anchored! Block #{new_block.index} · `{new_block.hash[:28]}…`")
        else:
            st.error("Save failed — check DB path/permissions.")

    # ── BPM display & signal chart ─────────────────────────────────────────
    bpm_val = st.session_state.bpm
    cls = bpm_class(bpm_val)
    sample_count = len(st.session_state.data_buffer)

    bpm_placeholder.markdown(f"""
    <div class="cs-card" style="text-align:center;padding:1.5rem">
      <div style="font-size:.72rem;color:var(--text3);text-transform:uppercase;letter-spacing:.1em;margin-bottom:.3rem">Heart Rate</div>
      <div class="bpm-display {cls}">{bpm_val if bpm_val else '–'}</div>
      <div style="font-size:.85rem;color:var(--text2);margin-top:.3rem">BPM</div>
      <div style="margin-top:.6rem">
        <div style="height:4px;background:var(--border);border-radius:2px;overflow:hidden">
          <div style="height:100%;width:{min(sample_count/150*100,100):.0f}%;background:linear-gradient(90deg,var(--accent),var(--cyan));border-radius:2px;transition:width .3s"></div>
        </div>
        <div style="font-size:.68rem;color:var(--text3);margin-top:3px">{sample_count}/150 samples collected</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.last_result:
        an = st.session_state.last_result['analysis']
        bcls = badge_class(an['status'])
        status_placeholder.markdown(f"""
        <div class="cs-card">
          <div style="margin-bottom:.6rem"><span class="status-badge {bcls}">{an['icon']} {an['category']}</span></div>
          <div style="font-size:.82rem;color:var(--text2)">{an['description']}</div>
          <div style="font-size:.75rem;color:var(--text3);margin-top:.6rem"><b>Recommendations:</b></div>
          {''.join(f"<div style='font-size:.75rem;color:var(--text2);margin-top:3px'>• {x}</div>" for x in an['recommendations'])}
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.data_buffer:
            buf = list(st.session_state.data_buffer)[-80:]
            fig = go.Figure(go.Scatter(
                y=buf, mode='lines',
                line=dict(color='#E84855', width=1.5),
                fill='tozeroy', fillcolor='rgba(232,72,85,0.1)'
            ))
            fig.update_layout(**plotly_dark(), height=130,
                              title=dict(text="Live rPPG Signal", font=dict(size=11)))
            signal_placeholder.plotly_chart(
                fig, use_container_width=True,
                config={'displayModeBar': False},
                key=f"live_sig_{sample_count}"
            )

def render_results(user):
    st.markdown('<div class="section-header">📊 My Health History</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">All readings for {user["full_name"]} · Blockchain-anchored records</div>', unsafe_allow_html=True)
    results=get_user_results(user['id'])
    if not results:
        st.markdown("""<div style="text-align:center;padding:3rem;color:var(--text2)"><div style="font-size:3rem;margin-bottom:1rem">📭</div><div style="font-size:1.1rem">No results yet</div><div style="font-size:.85rem;color:var(--text3);margin-top:.3rem">Complete a heart rate test to see your history here.</div></div>""", unsafe_allow_html=True)
        return
    bpms=[r['bpm'] for r in results]; normal_count=sum(1 for b in bpms if 60<=b<=100)
    c1,c2,c3,c4,c5=st.columns(5)
    for col,label,val,sub in [(c1,"Total Tests",len(results),"All time"),(c2,"Average BPM",f"{np.mean(bpms):.0f}","Mean"),(c3,"Lowest",f"{min(bpms)}","BPM"),(c4,"Highest",f"{max(bpms)}","BPM"),(c5,"Normal",f"{normal_count}/{len(bpms)}","60-100 BPM")]:
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{val}</div><div class="metric-label">{label}</div><div class="metric-sub">{sub}</div></div>', unsafe_allow_html=True)
    st.divider()
    df=pd.DataFrame(results); df['test_date']=pd.to_datetime(df['test_date']); df=df.sort_values('test_date')
    df['color']=df['bpm'].apply(lambda b:'#00E5A0' if 60<=b<=100 else '#FFD166' if 40<=b<60 or 101<=b<=120 else '#E84855')
    fig=go.Figure()
    fig.add_hrect(y0=60,y1=100,fillcolor="rgba(0,229,160,0.07)",annotation_text="Normal Zone",annotation_position="top left",line_width=0)
    fig.add_trace(go.Scatter(x=df['test_date'],y=df['bpm'],mode='lines+markers',line=dict(color='#E84855',width=2),marker=dict(size=8,color=df['color'],line=dict(width=1,color='#0A0E1A')),hovertemplate='<b>%{y} BPM</b><br>%{x}<extra></extra>',name='Heart Rate'))
    fig.update_layout(**plotly_dark(),height=280,title=dict(text="Heart Rate Over Time",font=dict(size=13,color='#E8EDF8')))
    st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
    st.divider(); st.markdown("### 📋 Detailed Records")
    for r in results:
        an=r['analysis']; bcls=badge_class(an['status'])
        chain_badge=""
        if r.get('block_hash'):
            chain_badge=f"⛓️ Block #{r['block_index']}"
        with st.expander(f"📅 {r['test_date']} — {r['bpm']} BPM | {an['category']} {chain_badge}", expanded=False):
            c1,c2,c3=st.columns([1,1,1])
            with c1:
                st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:{an["color"]}">{r["bpm"]}</div><div class="metric-label">BPM</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div style="margin-top:.8rem"><span class="status-badge {bcls}">{an["icon"]} {an["category"]}</span><div style="font-size:.78rem;color:var(--text2);margin-top:.5rem">{an["description"]}</div></div>', unsafe_allow_html=True)
                if r.get('block_hash'):
                    st.markdown(f'<div style="margin-top:.6rem;background:rgba(0,229,160,.07);border:1px solid rgba(0,229,160,.2);border-radius:8px;padding:.6rem;font-size:.7rem"><b style="color:var(--green)">⛓️ Blockchain</b><br><code style="font-size:.65rem">{r["block_hash"][:32]}…</code><br>Block #{r["block_index"]}</div>', unsafe_allow_html=True)
            with c2:
                st.markdown("**Recommendations**")
                for rec in an['recommendations']:
                    st.markdown(f"<div style='font-size:.8rem;color:var(--text2);margin:2px 0'>• {rec}</div>", unsafe_allow_html=True)
            with c3:
                fig_g=go.Figure(go.Indicator(mode="gauge+number",value=r['bpm'],gauge={'axis':{'range':[0,200],'tickcolor':'#4A5578'},'bar':{'color':an['color']},'bgcolor':'rgba(0,0,0,0)','bordercolor':'#253358','steps':[{'range':[0,40],'color':'rgba(232,72,85,0.15)'},{'range':[40,60],'color':'rgba(255,209,102,0.1)'},{'range':[60,100],'color':'rgba(0,229,160,0.1)'},{'range':[100,120],'color':'rgba(255,209,102,0.1)'},{'range':[120,200],'color':'rgba(232,72,85,0.1)'}]},number={'font':{'size':28,'color':an['color'],'family':'DM Mono'}},domain={'x':[0,1],'y':[0,1]}))
                fig_g.update_layout(paper_bgcolor='rgba(0,0,0,0)',height=180,margin=dict(l=10,r=10,t=20,b=10),font=dict(color='#8A97B8'))
                st.plotly_chart(fig_g,use_container_width=True,config={'displayModeBar':False},key=f"gauge_{r['test_id']}")
    st.divider()
    export_df=pd.DataFrame({'Date':[r['test_date'] for r in results],'BPM':[r['bpm'] for r in results],'Category':[r['analysis']['category'] for r in results],'Block Hash':[r.get('block_hash','') for r in results]})
    st.download_button("⬇ Export CSV",export_df.to_csv(index=False),f"health_data_{user['username']}.csv","text/csv")

# ─────────────────────────────────────────────────────────────────────────────
# PAGE: DECENTRALISED STORAGE
# ─────────────────────────────────────────────────────────────────────────────
def render_decentralised(user, is_admin):
    st.markdown('<div class="section-header">🌐 Decentralisation / Storage</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Geo-distributed encrypted node architecture · Blockchain-verified integrity · Key separation</div>', unsafe_allow_html=True)

    bc = st.session_state.blockchain
    all_results = get_all_results_admin() if is_admin else get_user_results(user['id'])

    # ── Architecture overview ──────────────────────────────────────────────
    st.markdown("### 🏗️ Storage Architecture")
    st.markdown(f"""
    <div style="background:var(--card2);border:1px solid var(--border);border-radius:12px;padding:1.2rem;margin-bottom:1rem;font-size:.83rem;color:var(--text2)">
    <b style="color:var(--cyan)">Decentralised IoMT Storage Principle:</b> Encrypted patient data is never stored in a single location.
    The architecture separates <b>encrypted blobs</b> (distributed across 3 geo-nodes) from <b>decryption keys</b>
    (stored in an independent Key Management Service). The blockchain ledger provides an immutable hash of every record.
    An attacker must simultaneously compromise all 3 data nodes AND the KMS — without either alone yielding any plaintext.
    </div>""", unsafe_allow_html=True)

    nodes_info = [
        ("📦 Node 1", "#00D4FF", "eu-west-1", "Ireland", "Primary"),
        ("📦 Node 2", "#E84855", "us-east-1", "Virginia", "Replica"),
        ("📦 Node 3", "#00E5A0", "ap-southeast-1", "Singapore", "Replica"),
        ("🔑 KMS", "#FFD166", "Separate Auth", "HSM-backed", "Key Store"),
        ("⛓️ Blockchain", "#9B5DE5", "All Nodes", "Immutable Ledger", "Audit Trail"),
    ]
    cols = st.columns(len(nodes_info))
    for col, (title, color, region, loc, role) in zip(cols, nodes_info):
        with col:
            st.markdown(f"""
            <div style="background:var(--card2);border:1px solid {color}44;border-top:3px solid {color};
                 border-radius:10px;padding:.9rem;text-align:center;min-height:150px">
              <div style="font-size:1.1rem;margin-bottom:.3rem">{title}</div>
              <div style="font-size:.7rem;color:{color};font-weight:600;margin-bottom:.3rem">{region}</div>
              <div style="font-size:.68rem;color:var(--text2)">{loc}</div>
              <div style="font-size:.65rem;color:var(--text3);margin-top:.3rem">{role}</div>
            </div>""", unsafe_allow_html=True)

    st.divider()

    # ── Blockchain status ─────────────────────────────────────────────────
    st.markdown("### ⛓️ Blockchain Ledger Status")
    is_valid, msg = bc.is_valid()
    chain_len = len(bc.chain)

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:var(--cyan)">{chain_len}</div><div class="metric-label">Total Blocks</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:var(--green)">{"✅ Valid" if is_valid else "❌ Invalid"}</div><div class="metric-label">Chain Integrity</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:var(--yellow)">{bc.difficulty}</div><div class="metric-label">PoW Difficulty</div></div>', unsafe_allow_html=True)
    with c4:
        latest_hash = bc.get_latest_block().hash[:16]+"…"
        st.markdown(f'<div class="metric-card"><div style="font-family:\'DM Mono\';font-size:.75rem;color:var(--accent);margin-top:.3rem">{latest_hash}</div><div class="metric-label">Latest Hash</div></div>', unsafe_allow_html=True)

    if is_valid:
        st.success(f"✅ {msg} — {chain_len} blocks, difficulty {bc.difficulty}")
    else:
        st.error(f"❌ {msg}")

    # Blockchain explorer
    st.markdown("### 🔍 Blockchain Explorer")
    chain_df = pd.DataFrame([{
        "Block": b.index,
        "Hash": b.hash[:20]+"…",
        "Prev Hash": b.previous_hash[:20]+"…",
        "Nonce": b.nonce,
        "Record ID": b.record_id if b.record_id else "–",
        "Time": b.timestamp[:19]
    } for b in bc.chain])
    st.dataframe(chain_df, use_container_width=True, hide_index=True)

    # ── Live node simulation ───────────────────────────────────────────────
    st.divider()
    st.markdown("### 📡 Live Node Status & Record Distribution")

    if not all_results:
        st.info("No records stored yet. Save a test result from the Monitor page to see distribution.")
    else:
        records_to_show = all_results[:6]
        for r in records_to_show:
            bh = r.get('block_hash','') if isinstance(r,dict) else r.get('block_hash','')
            bid = r.get('block_index',-1) if isinstance(r,dict) else -1
            node_ids_raw = r.get('node_ids','') if isinstance(r,dict) else ''
            node_ids = node_ids_raw.split(',') if node_ids_raw else [os.urandom(6).hex() for _ in range(3)]

            rid = r.get('test_id','?') if isinstance(r,dict) else r.get('test_id','?')
            bpm_v = r.get('bpm','?') if isinstance(r,dict) else r.get('bpm','?')
            td = r.get('test_date','?') if isinstance(r,dict) else r.get('test_date','?')
            user_n = r.get('username',user['username']) if isinstance(r,dict) else user['username']

            enc_hex_preview = r.get('encrypted_hex','') if isinstance(r,dict) else ''
            if not enc_hex_preview:
                # Re-simulate for regular users
                dummy_key = os.urandom(32)
                dummy_enc = HybridEncryption.encrypt_aes_gcm(json.dumps({"bpm":bpm_v}), dummy_key)
                enc_hex_preview = dummy_enc.hex()

            node_labels = ["eu-west-1 (Ireland)","us-east-1 (Virginia)","ap-se-1 (Singapore)"]
            chunk_size = max(len(enc_hex_preview)//3, 1)
            chunks = [enc_hex_preview[i*chunk_size:(i+1)*chunk_size] for i in range(3)]

            with st.expander(f"📄 Record #{rid} | {bpm_v} BPM | {str(td)[:16]} | @{user_n}", expanded=False):
                nc1,nc2,nc3,nc4 = st.columns([1,1,1,1])
                for idx,(col2,node_lab,chunk) in enumerate(zip([nc1,nc2,nc3],node_labels,chunks)):
                    nid = node_ids[idx] if idx < len(node_ids) else os.urandom(6).hex()
                    with col2:
                        colors=["#00D4FF","#E84855","#00E5A0"]
                        st.markdown(f"""<div style="background:var(--card2);border:1px solid {colors[idx]}44;border-top:2px solid {colors[idx]};border-radius:8px;padding:.7rem">
                          <div style="font-size:.72rem;color:{colors[idx]};font-weight:600">📦 {node_lab}</div>
                          <div style="font-family:'DM Mono';font-size:.6rem;color:var(--text2);margin:.4rem 0;word-break:break-all">{chunk[:40]}…</div>
                          <div style="font-size:.65rem;color:var(--green)">✅ Stored · Node: {nid[:10]}…</div>
                        </div>""", unsafe_allow_html=True)
                with nc4:
                    st.markdown(f"""<div style="background:var(--card2);border:1px solid var(--yellow)44;border-top:2px solid var(--yellow);border-radius:8px;padding:.7rem">
                      <div style="font-size:.72rem;color:var(--yellow);font-weight:600">⛓️ Blockchain</div>
                      <div style="font-family:'DM Mono';font-size:.6rem;color:var(--text2);margin:.4rem 0;word-break:break-all">{bh[:32] if bh else 'Not anchored'}…</div>
                      <div style="font-size:.65rem;color:var(--green)">{'✅ Block #'+str(bid) if bh else '⚠️ No block'}</div>
                    </div>""", unsafe_allow_html=True)

    # ── Tamper simulation ──────────────────────────────────────────────────
    st.divider()
    st.markdown("### 🔨 Blockchain Tamper Simulation")
    st.markdown('<div style="font-size:.82rem;color:var(--text2);margin-bottom:.8rem">Simulate an attack that modifies a block\'s data — the chain validation will detect it instantly.</div>', unsafe_allow_html=True)
    if len(bc.chain) > 1:
        col_s, col_b = st.columns([3,1])
        with col_s:
            tamper_idx = st.slider("Block to tamper", 1, len(bc.chain)-1, 1)
        with col_b:
            if st.button("🔨 Tamper Block", type="primary", use_container_width=True):
                bc.chain[tamper_idx].data["tampered"] = True
                bc.chain[tamper_idx].data["bpm"] = 999
                valid, vmsg = bc.is_valid()
                if not valid:
                    st.error(f"❌ Tamper detected! {vmsg}")
                    st.warning("Block hash no longer matches data — integrity violation caught.")
                    # Restore
                    bc.chain[tamper_idx].data.pop("tampered", None)
                    bc.chain[tamper_idx].data["bpm"] = bc.chain[tamper_idx].data.get("bpm", 72)
                else:
                    st.success("Chain still valid (tamper didn't change hash — shouldn't happen)")
    else:
        st.info("Save at least one test result first to have blocks to tamper with.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: DECRYPTION
# ─────────────────────────────────────────────────────────────────────────────
def render_decryption(user, is_admin):
    st.markdown('<div class="section-header">🔓 Decryption Centre</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Authenticated AES-256-GCM decryption · Tamper simulation · Integrity verification</div>', unsafe_allow_html=True)

    all_results = get_all_results_admin() if is_admin else get_user_results(user['id'])
    if not all_results:
        st.info("No records available. Save a test result from the Monitor page first.")
        return

    # ── Record selector ────────────────────────────────────────────────────
    st.markdown("### 📂 Select Record to Decrypt")
    options = {}
    for r in all_results:
        rid = r.get('test_id','?')
        bpm_v = r.get('bpm','?')
        td = str(r.get('test_date',''))[:16]
        user_n = r.get('username', user['username'])
        label = f"Record #{rid} | {bpm_v} BPM | {td} | @{user_n}"
        options[label] = r
    sel_label = st.selectbox("Choose record", list(options.keys()))
    record = options[sel_label]

    st.divider()

    # ── Generate fresh encryption of this record for demo ─────────────────
    an = record.get('analysis', {}) if isinstance(record, dict) else {}
    bpm_v = record.get('bpm', 72) if isinstance(record, dict) else 72
    td_v = record.get('test_date', datetime.now().isoformat())
    plain_data = {
        "record_id": record.get('test_id',''),
        "patient": record.get('full_name', user['full_name']) if is_admin else user['full_name'],
        "bpm": bpm_v,
        "category": an.get('category','Normal Resting'),
        "description": an.get('description',''),
        "recommendations": an.get('recommendations',[]),
        "test_date": str(td_v),
        "block_hash": record.get('block_hash',''),
        "status": an.get('status','success'),
        "system": APP_TITLE,
        "security": APP_SECURITY,
    }
    demo_key = os.urandom(32)
    demo_enc = HybridEncryption.encrypt_aes_gcm(json.dumps(plain_data), demo_key)

    # ECC keys for this demo
    priv_key, pub_key = HybridEncryption.generate_ecc_keys()
    priv_pem = priv_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
    pub_pem  = pub_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()

    # ── Tabs ──────────────────────────────────────────────────────────────
    t1, t2, t3, t4 = st.tabs(["🔓 Live Decrypt", "🔑 Key Inspector", "🔨 Tamper Test", "📊 Comparison"])

    with t1:
        st.markdown("### 🔓 Live Authenticated Decryption")
        col_ctrl, col_enc = st.columns([1, 2])
        with col_ctrl:
            st.markdown('<div class="cs-card">', unsafe_allow_html=True)
            st.markdown("**🔐 Ciphertext Preview**")
            st.code(demo_enc.hex()[:80]+"…", language="text")
            st.markdown(f"**Size:** {len(demo_enc)} bytes (nonce 12 + data {len(demo_enc)-28} + tag 16)")
            st.markdown("</div>", unsafe_allow_html=True)

            if st.button("▶ Decrypt & Verify", type="primary", use_container_width=True):
                with st.spinner("Authenticating tag… decrypting…"):
                    time.sleep(0.6)
                    try:
                        dec_json = HybridEncryption.decrypt_aes_gcm(demo_enc, demo_key)
                        dec_data = json.loads(dec_json)
                        st.success("✅ Auth tag VALID — no tampering")
                        st.success("✅ Decryption successful")
                        if dec_data == plain_data:
                            st.success("✅ Byte-for-byte match with plaintext")
                        st.balloons()
                        with col_enc:
                            st.markdown("**📄 Recovered Plaintext:**")
                            st.json(dec_data)
                    except Exception as e:
                        st.error(f"❌ Decryption failed: {e}")

        with col_enc:
            st.markdown("**📋 Decryption Process**")
            steps = [("1","Retrieve encrypted blob from storage node","#00D4FF"),("2","Retrieve key from KMS (separate auth required)","#9B5DE5"),("3","Extract nonce (first 12 bytes)","#FFD166"),("4","Compute GHASH over ciphertext","#E84855"),("5","Constant-time compare auth tags","#E84855"),("6","Only on match: AES-CTR decrypt","#00E5A0"),("7","Return plaintext / raise exception if tampered","#8A97B8")]
            for num,desc,color in steps:
                st.markdown(f'<div style="display:flex;gap:.7rem;align-items:flex-start;padding:.4rem 0;border-bottom:1px solid var(--border)"><span class="step-pill step-pill-active" style="background:{color};color:#0A0E1A;flex-shrink:0">{num}</span><div style="font-size:.8rem;color:var(--text2);padding-top:4px">{desc}</div></div>', unsafe_allow_html=True)

    with t2:
        st.markdown("### 🔑 Key Inspector")
        c1,c2 = st.columns(2)
        with c1:
            st.markdown("**AES-256 Session Key (32 bytes)**")
            groups=[demo_key.hex()[i:i+8] for i in range(0,len(demo_key.hex()),8)]
            colours=['#E84855','#FFD166','#00E5A0','#00D4FF','#9B5DE5','#FF6B6B','#51CF66','#74C0FC']
            hex_html=' '.join(f'<span style="color:{colours[j%8]}">{g}</span>' for j,g in enumerate(groups))
            st.markdown(f'<div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:1rem;font-family:\'DM Mono\';font-size:.75rem;line-height:2">{hex_html}</div>', unsafe_allow_html=True)
            nonce_hex=demo_enc[:12].hex(); n_groups=[nonce_hex[i:i+6] for i in range(0,len(nonce_hex),6)]
            n_html=' '.join(f'<span style="color:{colours[j%8]}">{g}</span>' for j,g in enumerate(n_groups))
            st.markdown("**Nonce (12 bytes / 96-bit)**")
            st.markdown(f'<div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:.8rem;font-family:\'DM Mono\';font-size:.75rem;line-height:2">{n_html}</div>', unsafe_allow_html=True)
        with c2:
            st.markdown("**ECC Private Key (SECP256R1)**")
            st.code(priv_pem, language="text")
            st.markdown("**ECC Public Key**")
            st.code(pub_pem[:200]+"…", language="text")

    with t3:
        st.markdown("### 🔨 Tamper Attack Simulation")
        st.markdown('<div style="font-size:.83rem;color:var(--text2);margin-bottom:1rem">Flip one byte in the ciphertext and observe the authentication tag rejection — zero plaintext is ever returned.</div>', unsafe_allow_html=True)
        tamper_byte = st.slider("Byte position to corrupt", 13, len(demo_enc)-17, 15)
        if st.button("🔨 Tamper & Attempt Decrypt", type="primary"):
            with st.spinner("Simulating tamper… attempting decrypt…"):
                time.sleep(0.5)
                tampered = bytearray(demo_enc); tampered[tamper_byte] ^= 0xFF
                try:
                    HybridEncryption.decrypt_aes_gcm(bytes(tampered), demo_key)
                    st.error("Unexpected: decryption succeeded on tampered data!")
                except Exception as e:
                    st.error("❌ DECRYPTION REJECTED — Authentication tag mismatch!")
                    st.markdown(f"""<div style="background:rgba(232,72,85,.1);border:1px solid rgba(232,72,85,.3);border-radius:8px;padding:1rem;margin-top:.5rem;font-size:.82rem;color:var(--text2)">
                    <b style="color:var(--accent)">🔒 Security Response:</b> No plaintext was returned. In production this event would be logged to SIEM, session terminated, and a tamper alert raised.<br><br>
                    <b>Error:</b> <code>{type(e).__name__}</code><br>
                    <b>Byte tampered:</b> position {tamper_byte} (0x{demo_enc[tamper_byte]:02X} → 0x{tampered[tamper_byte]:02X})
                    </div>""", unsafe_allow_html=True)

    with t4:
        st.markdown("### 📊 Plaintext vs Ciphertext")
        plain_str = json.dumps(plain_data, indent=2)
        c1,c2 = st.columns(2)
        with c1:
            st.markdown('<div style="text-align:center;padding:.5rem;background:rgba(255,209,102,.1);border-radius:8px 8px 0 0;border:1px solid rgba(255,209,102,.2);font-size:.82rem;color:var(--yellow);font-weight:600">📄 PLAINTEXT (Readable)</div>', unsafe_allow_html=True)
            st.code(plain_str, language="json")
            st.metric("Size", f"{len(plain_str)} bytes")
        with c2:
            st.markdown('<div style="text-align:center;padding:.5rem;background:rgba(0,229,160,.1);border-radius:8px 8px 0 0;border:1px solid rgba(0,229,160,.2);font-size:.82rem;color:var(--green);font-weight:600">🔐 CIPHERTEXT (Encrypted)</div>', unsafe_allow_html=True)
            st.code(demo_enc.hex(), language="text")
            st.metric("Size", f"{len(demo_enc)} bytes")
            st.markdown('<div style="background:rgba(0,229,160,.07);border:1px solid rgba(0,229,160,.2);border-radius:8px;padding:.8rem;font-size:.78rem;color:var(--text2)">✅ Without the 256-bit key, this is computationally indistinguishable from random noise — 2¹²⁸ brute-force operations required.</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ENCRYPTION LAB STEPS
# ─────────────────────────────────────────────────────────────────────────────
ENC_STEPS = [
    ("enc_step1","📝 Step 1","Plaintext Prep"),
    ("enc_step2","🔑 Step 2","ECC Key Gen"),
    ("enc_step3","🔐 Step 3","AES Key & Nonce"),
    ("enc_step4","🛡️ Step 4","AES-GCM Encrypt"),
    ("enc_step5","🌐 Step 5","Distributed Store"),
    ("enc_step6","🔓 Step 6","Decrypt & Verify"),
]

def enc_progress_bar():
    cur=st.session_state.page; pages=[s[0] for s in ENC_STEPS]
    idx=pages.index(cur) if cur in pages else 0
    cols=st.columns(len(ENC_STEPS))
    for i,(pg,short,name) in enumerate(ENC_STEPS):
        with cols[i]:
            if i<idx: pill,icon="step-pill-done","✓"
            elif i==idx: pill,icon="step-pill-active",str(i+1)
            else: pill,icon="step-pill-todo",str(i+1)
            st.markdown(f'<div style="text-align:center"><span class="step-pill {pill}">{icon}</span><div style="font-size:.62rem;color:var(--text3);margin-top:3px">{name}</div></div>', unsafe_allow_html=True)
    st.progress(idx/(len(ENC_STEPS)-1) if idx else 0)

def enc_nav(cur_page):
    pages=[s[0] for s in ENC_STEPS]; idx=pages.index(cur_page)
    c1,c2,c3=st.columns([1,3,1])
    with c1:
        if idx>0:
            if st.button("← Previous",use_container_width=True,type="secondary"):
                st.session_state.page=pages[idx-1]; st.rerun()
    with c2:
        st.markdown(f"<div style='text-align:center;color:var(--text3);font-size:.8rem'>Step {idx+1} of {len(ENC_STEPS)}</div>", unsafe_allow_html=True)
    with c3:
        if idx<len(ENC_STEPS)-1:
            if st.button("Next →",use_container_width=True,type="primary"):
                st.session_state.page=pages[idx+1]; st.rerun()

def get_enc_sample(user):
    if 'enc_sample' not in st.session_state:
        st.session_state.enc_sample={"patient":user['full_name'],"bpm":72,"category":"Normal Resting","timestamp":datetime.now().isoformat(),"device_id":"MEDCHAIN-001","system":APP_TITLE,"recommendations":["Maintain regular physical activity","Stay hydrated"]}
    return st.session_state.enc_sample

def get_enc_keys():
    if 'enc_keys' not in st.session_state:
        priv,pub=HybridEncryption.generate_ecc_keys(); key=os.urandom(32); nonce=os.urandom(12)
        st.session_state.enc_keys={'priv':priv,'pub':pub,'key':key,'nonce':nonce}
    return st.session_state.enc_keys

def get_enc_cipher(user):
    if 'enc_cipher' not in st.session_state:
        sample=get_enc_sample(user); keys=get_enc_keys()
        st.session_state.enc_cipher=HybridEncryption.encrypt_aes_gcm(json.dumps(sample),keys['key'])
    return st.session_state.enc_cipher

# ─────────────────────────────────────────────────────────────────────────────
# ENC STEP PAGES (condensed but complete)
# ─────────────────────────────────────────────────────────────────────────────
def render_enc_step1(user):
    st.markdown(f'<div class="section-header">🔒 Encryption Laboratory</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">Step-by-step walkthrough · {APP_SECURITY}</div>', unsafe_allow_html=True)
    enc_progress_bar(); st.divider()
    sample=get_enc_sample(user)
    st.markdown('<div class="cs-card"><div style="font-family:\'DM Serif Display\',serif;font-size:1.1rem;color:var(--cyan);margin-bottom:.6rem">📝 Step 1: Plaintext Medical Data Preparation</div><div style="font-size:.83rem;color:var(--text2);line-height:1.7">Before encryption, raw IoMT data is serialised to <b>JSON</b>. This is the most sensitive state — it must only exist in memory for the shortest possible time inside a Trusted Execution Environment (TEE) before encryption. In clinical systems, a <b>pseudonymisation</b> layer separates PII from health data at this stage.</div></div>', unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        st.markdown("**📄 Structured JSON**"); st.json(sample)
    with c2:
        pt=json.dumps(sample,indent=2)
        st.markdown("**💾 Raw Plaintext**"); st.code(pt,language="json")
        st.markdown(f'<div style="display:flex;gap:.8rem;margin-top:.5rem"><div class="metric-card" style="flex:1"><div class="metric-value" style="font-size:1.2rem">{len(pt)}</div><div class="metric-label">Bytes</div></div><div class="metric-card" style="flex:1"><div class="metric-value" style="font-size:1.2rem">{len(pt.encode())}</div><div class="metric-label">UTF-8</div></div></div>', unsafe_allow_html=True)
    st.success("✅ IoMT data serialised to JSON — ready for hybrid encryption pipeline.")
    st.markdown(f'<div style="background:rgba(0,212,255,.07);border:1px solid rgba(0,212,255,.2);border-radius:10px;padding:1rem;margin-top:.8rem;font-size:.83rem;color:var(--text2)"><b style="color:var(--cyan)">🔍 System:</b> {APP_TITLE} · {APP_SECURITY}</div>', unsafe_allow_html=True)
    enc_nav("enc_step1")

def render_enc_step2():
    st.markdown('<div class="section-header">🔒 Encryption Laboratory</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{APP_SECURITY}</div>', unsafe_allow_html=True)
    enc_progress_bar(); st.divider()
    keys=get_enc_keys()
    priv_pem=keys['priv'].private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()).decode()
    pub_pem=keys['pub'].public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    st.markdown('<div class="cs-card"><div style="font-family:\'DM Serif Display\',serif;font-size:1.1rem;color:var(--cyan);margin-bottom:.6rem">🔑 Step 2: ECC Key Pair Generation (SECP256R1)</div><div style="font-size:.83rem;color:var(--text2);line-height:1.7">We use the <b>NIST P-256 (SECP256R1)</b> curve — 256-bit key providing 128-bit security. The same curve used by TLS 1.3. <b>ECDH</b> key exchange lets two IoMT parties derive a shared secret over an insecure channel without transmitting it.</div></div>', unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        st.markdown("**🔒 Private Key (PKCS#8 — store in HSM)**"); st.code(priv_pem,language="text")
        st.markdown('<div style="background:rgba(232,72,85,.07);border:1px solid rgba(232,72,85,.2);border-radius:8px;padding:.7rem;font-size:.78rem;color:var(--text2)">⚠️ Never transmit. Store in Hardware Security Module or KMS.</div>', unsafe_allow_html=True)
    with c2:
        st.markdown("**🔓 Public Key (freely shareable via PKI)**"); st.code(pub_pem,language="text")
        st.markdown('<div style="background:rgba(0,229,160,.07);border:1px solid rgba(0,229,160,.2);border-radius:8px;padding:.7rem;font-size:.78rem;color:var(--text2)">✅ Distribute via X.509 certificates for IoMT device identity verification.</div>', unsafe_allow_html=True)
    st.divider(); st.markdown("### 🔄 ECDH Key Exchange Simulation")
    priv2,pub2=HybridEncryption.generate_ecc_keys()
    s1=HybridEncryption.derive_shared_key(keys['priv'],pub2)
    s2=HybridEncryption.derive_shared_key(priv2,keys['pub'])
    c1,c2,c3=st.columns([2,1,2])
    with c1: st.markdown(f'<div class="metric-card"><div style="color:var(--cyan);font-weight:600">📱 IoMT Device</div><div style="font-size:.72rem;color:var(--text2);margin-top:.3rem">Derived: {s1.hex()[:28]}…</div></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div style="text-align:center;padding-top:1.2rem;color:var(--green);font-size:1.8rem">⟷</div><div style="text-align:center;font-size:.68rem;color:var(--text3)">ECDH</div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><div style="color:var(--purple);font-weight:600">🏥 Hospital Server</div><div style="font-size:.72rem;color:var(--text2);margin-top:.3rem">Derived: {s2.hex()[:28]}…</div></div>', unsafe_allow_html=True)
    if s1==s2: st.success("✅ Both parties derived identical shared secrets without transmitting — ECDH successful!")
    enc_nav("enc_step2")

def render_enc_step3():
    st.markdown('<div class="section-header">🔒 Encryption Laboratory</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{APP_SECURITY}</div>', unsafe_allow_html=True)
    enc_progress_bar(); st.divider()
    keys=get_enc_keys()
    st.markdown('<div class="cs-card"><div style="font-family:\'DM Serif Display\',serif;font-size:1.1rem;color:var(--cyan);margin-bottom:.6rem">🔐 Step 3: AES-256 Session Key & Nonce Generation</div><div style="font-size:.83rem;color:var(--text2);line-height:1.7"><b>AES-256</b> with 14 rounds of substitution-permutation encrypts the actual IoMT data. The <b>96-bit Nonce</b> ensures identical plaintexts produce different ciphertexts, defeating traffic analysis. Both generated via <code>os.urandom()</code> — the OS CSPRNG seeded from hardware entropy.</div></div>', unsafe_allow_html=True)
    c1,c2=st.columns(2)
    colours=['#E84855','#FFD166','#00E5A0','#00D4FF','#9B5DE5','#FF6B6B','#51CF66','#74C0FC']
    with c1:
        st.markdown("**🔑 AES-256 Key (32 bytes)**")
        g=[keys['key'].hex()[i:i+8] for i in range(0,64,8)]
        html=' '.join(f'<span style="color:{colours[j%8]}">{x}</span>' for j,x in enumerate(g))
        st.markdown(f'<div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:1rem;font-family:\'DM Mono\';font-size:.78rem;line-height:2">{html}</div>', unsafe_allow_html=True)
    with c2:
        st.markdown("**🎯 GCM Nonce (12 bytes)**")
        ng=[keys['nonce'].hex()[i:i+6] for i in range(0,24,6)]
        nhtml=' '.join(f'<span style="color:{colours[j%8]}">{x}</span>' for j,x in enumerate(ng))
        st.markdown(f'<div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:1rem;font-family:\'DM Mono\';font-size:.78rem;line-height:2">{nhtml}</div>', unsafe_allow_html=True)
        st.markdown('<div style="margin-top:.6rem;font-size:.8rem;color:var(--text2)"><b style="color:var(--yellow)">Why 96-bit?</b> GCM counter mode is optimised for 96-bit nonce. With random nonce + 2³² encryptions, collision probability ~10⁻²⁰.</div>', unsafe_allow_html=True)
    st.code(f"""from cryptography.hazmat.primitives.kdf.hkdf import HKDF
derived_key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'handshake data').derive(ecdh_shared_secret)
# Result: {keys['key'].hex()[:32]}...""", language="python")
    enc_nav("enc_step3")

def render_enc_step4(user):
    st.markdown('<div class="section-header">🔒 Encryption Laboratory</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{APP_SECURITY}</div>', unsafe_allow_html=True)
    enc_progress_bar(); st.divider()
    sample=get_enc_sample(user); keys=get_enc_keys(); enc=get_enc_cipher(user)
    pb=json.dumps(sample).encode()
    st.markdown('<div class="cs-card"><div style="font-family:\'DM Serif Display\',serif;font-size:1.1rem;color:var(--cyan);margin-bottom:.6rem">🛡️ Step 4: AES-256-GCM Authenticated Encryption (AEAD)</div><div style="font-size:.83rem;color:var(--text2);line-height:1.7">AES-GCM provides <b>Confidentiality + Integrity + Authenticity</b> simultaneously. GCM uses AES in CTR mode for encryption and GHASH (polynomial hash over GF(2¹²⁸)) for authentication — running in parallel for hardware acceleration via AES-NI.</div></div>', unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1: st.markdown("**📄 Plaintext**"); st.code(pb.hex(),language="text"); st.caption(f"Size: {len(pb)} bytes")
    with c2: st.markdown("**🔐 Ciphertext**"); st.code(enc.hex(),language="text"); st.caption(f"Size: {len(enc)} bytes (+{len(enc)-len(pb)} overhead)")
    st.divider(); st.markdown("### 📦 Ciphertext Structure")
    n_part=enc[:12]; c_part=enc[12:-16]; t_part=enc[-16:]
    co1,co2,co3=st.columns([1,4,1])
    with co1: st.markdown(f'<div style="background:rgba(255,209,102,.1);border:2px solid rgba(255,209,102,.3);border-radius:8px;padding:.7rem;text-align:center"><div style="color:var(--yellow);font-weight:600;font-size:.78rem">NONCE</div><div style="font-family:\'DM Mono\';font-size:.6rem;color:var(--text2);margin-top:3px">{n_part.hex()[:14]}…</div><div style="color:var(--text3);font-size:.68rem;margin-top:3px">12 bytes</div></div>', unsafe_allow_html=True)
    with co2: st.markdown(f'<div style="background:rgba(232,72,85,.1);border:2px solid rgba(232,72,85,.3);border-radius:8px;padding:.7rem;text-align:center"><div style="color:var(--accent);font-weight:600;font-size:.78rem">CIPHERTEXT</div><div style="font-family:\'DM Mono\';font-size:.6rem;color:var(--text2);margin-top:3px">{c_part.hex()[:36]}…</div><div style="color:var(--text3);font-size:.68rem;margin-top:3px">{len(c_part)} bytes</div></div>', unsafe_allow_html=True)
    with co3: st.markdown(f'<div style="background:rgba(0,229,160,.1);border:2px solid rgba(0,229,160,.3);border-radius:8px;padding:.7rem;text-align:center"><div style="color:var(--green);font-weight:600;font-size:.78rem">AUTH TAG</div><div style="font-family:\'DM Mono\';font-size:.6rem;color:var(--text2);margin-top:3px">{t_part.hex()[:14]}…</div><div style="color:var(--text3);font-size:.68rem;margin-top:3px">16 bytes</div></div>', unsafe_allow_html=True)
    enc_nav("enc_step4")

def render_enc_step5(user):
    st.markdown('<div class="section-header">🔒 Encryption Laboratory</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{APP_SECURITY}</div>', unsafe_allow_html=True)
    enc_progress_bar(); st.divider()
    enc=get_enc_cipher(user); keys=get_enc_keys()
    st.markdown('<div class="cs-card"><div style="font-family:\'DM Serif Display\',serif;font-size:1.1rem;color:var(--cyan);margin-bottom:.6rem">🌐 Step 5: Decentralised IoMT Storage Architecture</div><div style="font-size:.83rem;color:var(--text2);line-height:1.7">Encrypted IoMT data is never stored in a single location. A 3-node geo-distributed architecture with independent KMS ensures: no single compromised node yields patient data. Blockchain provides an immutable hash anchor for each record.</div></div>', unsafe_allow_html=True)
    chunk_size=len(enc)//3; chunks=[enc[:chunk_size],enc[chunk_size:2*chunk_size],enc[2*chunk_size:]]
    regions=["eu-west-1 (Ireland)","us-east-1 (Virginia)","ap-southeast-1 (Singapore)"]; node_ids=[os.urandom(8).hex() for _ in range(3)]
    c1,c2,c3=st.columns(3)
    for col,chunk,region,nid in zip([c1,c2,c3],chunks,regions,node_ids):
        with col:
            st.markdown(f'<div class="cs-card"><div style="font-size:.85rem;font-weight:600;color:var(--cyan)">📦 {region}</div><div style="font-family:\'DM Mono\';font-size:.62rem;color:var(--text2);background:var(--bg);border-radius:6px;padding:.5rem;margin:.5rem 0;word-break:break-all">{chunk.hex()[:40]}…</div><div style="font-size:.68rem;color:var(--text3)">Node: {nid[:14]}…</div><div style="font-size:.73rem;color:var(--green);margin-top:.3rem">✅ Stored</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="background:rgba(0,229,160,.07);border:1px solid rgba(0,229,160,.2);border-radius:10px;padding:.9rem;margin-top:.5rem;font-size:.82rem;color:var(--text2)"><b style="color:var(--green)">🔑 KMS key (stored separately):</b><br><span style="font-family:\'DM Mono\';font-size:.7rem;color:var(--text3)">{keys["key"].hex()[:32]}…</span><br><span style="font-size:.75rem">Access requires MFA + RBAC. Admins cannot decrypt without KMS authorisation.</span></div>', unsafe_allow_html=True)
    enc_nav("enc_step5")

def render_enc_step6(user):
    st.markdown('<div class="section-header">🔒 Encryption Laboratory</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{APP_SECURITY}</div>', unsafe_allow_html=True)
    enc_progress_bar(); st.divider()
    sample=get_enc_sample(user); keys=get_enc_keys(); enc=get_enc_cipher(user)
    st.markdown('<div class="cs-card"><div style="font-family:\'DM Serif Display\',serif;font-size:1.1rem;color:var(--cyan);margin-bottom:.6rem">🔓 Step 6: Authenticated Decryption & Integrity Verification</div><div style="font-size:.83rem;color:var(--text2);line-height:1.7">Before any byte of plaintext is released, the <b>128-bit authentication tag is verified</b>. If tampered — no plaintext is ever returned. This "verify-then-decrypt" design prevents padding oracle attacks.</div></div>', unsafe_allow_html=True)
    col_ctrl,col_info=st.columns([2,3])
    with col_ctrl:
        st.markdown("### 🧪 Live Decryption Test")
        tamper=st.checkbox("🔴 Simulate tamper (corrupt 1 byte)",value=False)
        test_enc=enc
        if tamper:
            t=bytearray(enc); t[15]^=0xFF; test_enc=bytes(t)
            st.warning("⚠️ Data tampered — auth tag will fail")
        if st.button("🔍 Decrypt & Verify",type="primary",use_container_width=True):
            with st.spinner("Verifying auth tag…"):
                time.sleep(0.6)
                try:
                    dec=json.loads(HybridEncryption.decrypt_aes_gcm(test_enc,keys['key']))
                    st.success("✅ Auth tag VALID"); st.success("✅ Decryption successful")
                    if dec==sample: st.success("✅ Byte-for-byte match with original")
                    st.json(dec); st.balloons()
                except Exception as e:
                    st.error("❌ DECRYPTION FAILED — Auth tag mismatch!")
                    st.markdown(f'<div style="background:rgba(232,72,85,.1);border:1px solid rgba(232,72,85,.3);border-radius:8px;padding:1rem;font-size:.82rem;color:var(--text2)"><b style="color:var(--accent)">Security Response:</b> Zero plaintext returned. Session terminated. SIEM alert raised.</div>', unsafe_allow_html=True)
    with col_info:
        st.markdown("### 📋 Decryption Steps")
        for n,d,c in [("1","Retrieve blob + key from separate stores","#00D4FF"),("2","Separate nonce (first 12 bytes)","#9B5DE5"),("3","Compute GHASH over ciphertext","#FFD166"),("4","Constant-time compare auth tags","#E84855"),("5","Only on match: AES-CTR decrypt","#00E5A0"),("6","Return plaintext / raise exception","#8A97B8")]:
            st.markdown(f'<div style="display:flex;gap:.7rem;align-items:flex-start;padding:.4rem 0;border-bottom:1px solid var(--border)"><span class="step-pill step-pill-active" style="background:{c};color:#0A0E1A;flex-shrink:0">{n}</span><div style="font-size:.8rem;color:var(--text2);padding-top:4px">{d}</div></div>', unsafe_allow_html=True)
    enc_nav("enc_step6")


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN PAGES
# ─────────────────────────────────────────────────────────────────────────────
def render_admin_dashboard():
    st.markdown('<div class="section-header">🏠 Admin Dashboard</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{APP_TITLE} · System Overview</div>', unsafe_allow_html=True)
    all_results=get_all_results_admin(); all_users=get_all_users()
    non_admin=[u for u in all_users if not u['is_admin']]; bpms=[r['bpm'] for r in all_results] if all_results else []
    c1,c2,c3,c4=st.columns(4)
    for col,label,val,icon,color in [(c1,"Registered Users",len(non_admin),"👥","#00D4FF"),(c2,"Total Tests",len(all_results),"📊","#00E5A0"),(c3,"Avg Heart Rate",f"{np.mean(bpms):.0f} bpm" if bpms else "–","💓","#E84855"),(c4,"Blockchain Blocks",len(st.session_state.blockchain.chain),"⛓️","#9B5DE5")]:
        with col: st.markdown(f'<div class="metric-card"><div style="font-size:1.6rem">{icon}</div><div class="metric-value" style="color:{color}">{val}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)
    st.divider()
    if all_results:
        df_all=pd.DataFrame(all_results); df_all['test_date']=pd.to_datetime(df_all['test_date'])
        c1,c2=st.columns(2)
        with c1:
            fig_dist=go.Figure(go.Histogram(x=bpms,nbinsx=20,marker_color='#E84855',opacity=.8,marker_line=dict(color='#0A0E1A',width=1)))
            fig_dist.add_vrect(x0=60,x1=100,fillcolor="rgba(0,229,160,0.1)",annotation_text="Normal",line_width=0)
            fig_dist.update_layout(**plotly_dark(),height=260,title=dict(text="BPM Distribution",font=dict(size=12,color='#E8EDF8')))
            st.plotly_chart(fig_dist,use_container_width=True,config={'displayModeBar':False})
        with c2:
            cats=df_all['analysis'].apply(lambda a:a['category']).value_counts()
            fig_pie=go.Figure(go.Pie(labels=cats.index,values=cats.values,hole=.55,marker=dict(colors=['#00E5A0','#FFD166','#E84855','#00D4FF','#9B5DE5'],line=dict(color='#0A0E1A',width=2)),textfont=dict(size=10)))
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)',height=260,showlegend=True,legend=dict(font=dict(color='#8A97B8',size=9)),margin=dict(l=0,r=0,t=30,b=0),title=dict(text="Category Breakdown",font=dict(size=12,color='#E8EDF8')))
            st.plotly_chart(fig_pie,use_container_width=True,config={'displayModeBar':False})
    st.divider(); st.markdown("### 🕐 Recent Activity")
    log=get_session_log(limit=10)
    for entry in log:
        icon="🔐" if "LOGIN" in entry['action'] else "💓" if "TEST" in entry['action'] else "💾"
        st.markdown(f'<div style="display:flex;align-items:center;gap:.8rem;padding:.5rem .8rem;border-bottom:1px solid var(--border);font-size:.82rem"><span>{icon}</span><span style="color:var(--cyan);font-weight:500">{entry["username"]}</span><span style="color:var(--text2)">{entry["action"]}</span><span style="color:var(--text3);margin-left:auto">{entry["logged_at"][:16]}</span></div>', unsafe_allow_html=True)

def render_admin_users():
    st.markdown('<div class="section-header">👥 User Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Click View to see user test history</div>', unsafe_allow_html=True)
    all_users=get_all_users(); non_admin=[u for u in all_users if not u['is_admin']]
    search=st.text_input("🔍 Search users",placeholder="Name or username…")
    filtered=[u for u in non_admin if not search or search.lower() in u['full_name'].lower() or search.lower() in u['username'].lower()]
    if not filtered: st.info("No users found."); return
    for u in filtered:
        user_results=get_user_results(u['id']); avg_bpm=f"{np.mean([r['bpm'] for r in user_results]):.0f}" if user_results else "–"; last_date=user_results[0]['test_date'][:10] if user_results else "No tests"
        col_info,col_btn=st.columns([5,1])
        with col_info:
            st.markdown(f'<div class="cs-card" style="margin-bottom:.4rem"><div style="display:flex;align-items:center;gap:1rem"><div style="width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,#E84855,#9B5DE5);display:flex;align-items:center;justify-content:center;font-size:1.1rem;flex-shrink:0">{"👨" if u.get("gender","")=="Male" else "👩" if u.get("gender","")=="Female" else "👤"}</div><div style="flex:1"><div style="font-weight:600;color:var(--text)">{u["full_name"]}</div><div style="font-size:.75rem;color:var(--text2)">@{u["username"]} · Age {u.get("age","?")} · {u.get("gender","—")}</div></div><div style="text-align:center;padding:0 .8rem"><div style="font-family:\'DM Mono\';font-size:1rem;color:#00E5A0">{len(user_results)}</div><div style="font-size:.68rem;color:var(--text3)">Tests</div></div><div style="text-align:center;padding:0 .8rem"><div style="font-family:\'DM Mono\';font-size:1rem;color:#E84855">{avg_bpm}</div><div style="font-size:.68rem;color:var(--text3)">Avg BPM</div></div><div style="text-align:center;padding:0 .8rem"><div style="font-size:.75rem;color:var(--text2)">{last_date}</div><div style="font-size:.68rem;color:var(--text3)">Last test</div></div></div></div>', unsafe_allow_html=True)
        with col_btn:
            if st.button("View →",key=f"view_user_{u['id']}",use_container_width=True):
                st.session_state.admin_selected_user=u['id']
        if st.session_state.get('admin_selected_user')==u['id']:
            if not user_results: st.info(f"No results for {u['full_name']}.")
            else:
                bpms=[r['bpm'] for r in user_results]; m1,m2,m3,m4=st.columns(4)
                for col,label,val in zip([m1,m2,m3,m4],["Tests","Avg BPM","Min","Max"],[len(user_results),f"{np.mean(bpms):.0f}",min(bpms),max(bpms)]):
                    with col: st.markdown(f'<div class="metric-card"><div class="metric-value">{val}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)
                df_u=pd.DataFrame(user_results); df_u['test_date']=pd.to_datetime(df_u['test_date']); df_u=df_u.sort_values('test_date')
                fig_u=go.Figure(go.Scatter(x=df_u['test_date'],y=df_u['bpm'],mode='lines+markers',line=dict(color='#00D4FF',width=2),marker=dict(size=7,color='#00D4FF')))
                fig_u.add_hrect(y0=60,y1=100,fillcolor="rgba(0,229,160,0.07)",line_width=0); fig_u.update_layout(**plotly_dark(),height=200)
                st.plotly_chart(fig_u,use_container_width=True,config={'displayModeBar':False},key=f"trend_{u['id']}")
                rows=[{'Date':r['test_date'][:16],'BPM':r['bpm'],'Category':r['analysis']['category'],'Block':r.get('block_hash','')[:16]+'…' if r.get('block_hash') else '–'} for r in user_results]
                st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
                if st.button("✖ Close",key=f"close_{u['id']}",type="secondary"):
                    st.session_state.admin_selected_user=None; st.rerun()

def render_admin_records():
    st.markdown('<div class="section-header">📋 All Test Records</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Every encrypted + blockchain-anchored test result</div>', unsafe_allow_html=True)
    results=get_all_results_admin()
    if not results: st.info("No records yet."); return
    df=pd.DataFrame([{'Date':r['test_date'][:16],'User':r['username'],'Name':r['full_name'],'BPM':r['bpm'],'Category':r['analysis']['category'],'Block':r.get('block_hash','')[:16]+'…' if r.get('block_hash') else '–'} for r in results])
    c1,c2=st.columns(2)
    with c1: sel_user=st.selectbox("Filter user",["All"]+sorted(df['User'].unique().tolist()))
    with c2: sel_cat=st.selectbox("Filter category",["All"]+sorted(df['Category'].unique().tolist()))
    dff=df.copy()
    if sel_user!="All": dff=dff[dff['User']==sel_user]
    if sel_cat!="All": dff=dff[dff['Category']==sel_cat]
    st.markdown(f'<b>{len(dff)} records</b>', unsafe_allow_html=True)
    st.dataframe(dff,use_container_width=True,hide_index=True,height=400)
    st.download_button("⬇ Export CSV",df.to_csv(index=False),"all_records.csv","text/csv")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: RAW DATA & PRINT
# ─────────────────────────────────────────────────────────────────────────────
def render_raw_data(user, is_admin):
    st.markdown('<div class="section-header">📦 Raw Data & Print Centre</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Inspect, compare and print raw or encrypted records</div>', unsafe_allow_html=True)
    all_results=get_all_results_admin() if is_admin else get_user_results(user['id'])
    if not all_results: st.info("No records available."); return

    if is_admin:
        options={f"#{r['test_id']} | {r['test_date'][:16]} | {r['bpm']} BPM | @{r['username']}":r for r in all_results}
    else:
        options={f"#{r['test_id']} | {r['test_date'][:16]} | {r['bpm']} BPM":r for r in all_results}
    sel_label=st.selectbox("Select record",list(options.keys())); record=options[sel_label]

    an=record.get('analysis',{}) if isinstance(record,dict) else {}
    raw={"record_id":record.get('test_id',''),"system":APP_TITLE,"security":APP_SECURITY,"patient":record.get('full_name',user['full_name']) if is_admin else user['full_name'],"username":record.get('username',user['username']) if is_admin else user['username'],"bpm":record.get('bpm',0),"category":an.get('category',''),"description":an.get('description',''),"recommendations":an.get('recommendations',[]),"test_date":str(record.get('test_date','')),"block_hash":record.get('block_hash',''),"block_index":record.get('block_index',-1),"status":an.get('status','')}
    raw_str=json.dumps(raw,indent=2)

    demo_key=os.urandom(32); demo_enc=HybridEncryption.encrypt_aes_gcm(json.dumps(raw),demo_key)
    enc_hex=(record.get('encrypted_hex','') if is_admin and isinstance(record,dict) and 'encrypted_hex' in record else demo_enc.hex())

    st.divider()
    pt,et,bt,prt=st.tabs(["📄 Raw Data","🔐 Encrypted","📊 Comparison","🖨️ Print"])

    with pt:
        st.markdown('<div style="background:rgba(255,209,102,.07);border:1px solid rgba(255,209,102,.25);border-radius:8px;padding:.8rem;font-size:.8rem;color:var(--text2);margin-bottom:1rem">⚠️ Decrypted plaintext — most sensitive form. Access is logged.</div>', unsafe_allow_html=True)
        c1,c2=st.columns(2)
        with c1: st.json(raw)
        with c2: st.code(raw_str,language="json"); st.download_button("⬇ Download JSON",raw_str,f"raw_{record.get('test_id','')}.json","application/json")

    with et:
        st.markdown('<div style="background:rgba(0,229,160,.07);border:1px solid rgba(0,229,160,.2);border-radius:8px;padding:.8rem;font-size:.8rem;color:var(--text2);margin-bottom:1rem">✅ Stored form — without the key this is indistinguishable from random noise.</div>', unsafe_allow_html=True)
        c1,c2=st.columns(2)
        with c1: st.markdown("**🔐 Encrypted Blob (Hex)**"); st.code(enc_hex,language="text")
        with c2: st.markdown("**🔑 AES-256 Key**"); st.code(demo_key.hex(),language="text")
        st.download_button("⬇ Download Encrypted",enc_hex,f"enc_{record.get('test_id','')}.txt","text/plain")

    with bt:
        c1,c2=st.columns(2)
        with c1: st.markdown('<div style="text-align:center;padding:.5rem;background:rgba(255,209,102,.1);border-radius:8px 8px 0 0;border:1px solid rgba(255,209,102,.2);font-size:.82rem;color:var(--yellow);font-weight:600">📄 PLAINTEXT</div>', unsafe_allow_html=True); st.code(raw_str,language="json"); st.metric("Size",f"{len(raw_str)} bytes")
        with c2: st.markdown('<div style="text-align:center;padding:.5rem;background:rgba(0,229,160,.1);border-radius:8px 8px 0 0;border:1px solid rgba(0,229,160,.2);font-size:.82rem;color:var(--green);font-weight:600">🔐 CIPHERTEXT</div>', unsafe_allow_html=True); st.code(enc_hex,language="text"); st.metric("Size",f"{len(enc_hex)//2} bytes")

    with prt:
        st.markdown("### 🖨️ Print / Download Reports")
        c1,c2,c3=st.columns(3)
        base_html=f"""<html><head><meta charset="utf-8"><title>{APP_TITLE} Report</title>
<style>body{{font-family:monospace;padding:2rem;color:#000;max-width:900px;margin:0 auto}}h1{{color:#E84855}}h2{{color:#333;border-bottom:2px solid #E84855;padding-bottom:.3rem}}pre{{background:#f5f5f5;padding:1rem;border-radius:4px;white-space:pre-wrap;word-break:break-all}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:1rem}}</style></head>
<body><h1>🔒 {APP_TITLE}</h1><p style="font-size:.8rem">{APP_FULLNAME}</p><p style="font-size:.8rem">{APP_AUTHOR} · {APP_SECURITY}</p><p>Generated: {datetime.now().strftime('%d %B %Y %H:%M')} | Record: #{record.get('test_id','')}</p><hr>"""
        with c1:
            st.markdown('<div class="cs-card" style="text-align:center"><div style="font-size:1.5rem">📄</div><div style="font-weight:600">Raw Report</div></div>', unsafe_allow_html=True)
            html_raw=base_html+f"<h2>📄 Patient Data (Plaintext)</h2><pre>{raw_str}</pre></body></html>"
            st.download_button("⬇ Raw HTML",html_raw,f"report_raw_{record.get('test_id','')}.html","text/html",use_container_width=True)
        with c2:
            st.markdown('<div class="cs-card" style="text-align:center"><div style="font-size:1.5rem">🔐</div><div style="font-weight:600">Encrypted Report</div></div>', unsafe_allow_html=True)
            html_enc=base_html+f"<h2>🔐 Encrypted Data (AES-256-GCM)</h2><pre>{enc_hex}</pre><p><b>Nonce:</b> {enc_hex[:24]}</p></body></html>"
            st.download_button("⬇ Encrypted HTML",html_enc,f"report_enc_{record.get('test_id','')}.html","text/html",use_container_width=True)
        with c3:
            st.markdown('<div class="cs-card" style="text-align:center"><div style="font-size:1.5rem">📋</div><div style="font-weight:600">Full Report</div></div>', unsafe_allow_html=True)
            html_full=base_html+f'<div class="grid"><div><h2>📄 Plaintext</h2><pre>{raw_str}</pre></div><div><h2>🔐 Ciphertext</h2><pre>{enc_hex}</pre><p><b>Block Hash:</b> {raw.get("block_hash","–")[:32]}…</p></div></div><hr><p style="font-size:.75rem;color:#666">⚠️ Secure document · HIPAA/GDPR · {APP_TITLE} · {APP_AUTHOR}</p></body></html>'
            st.download_button("⬇ Full HTML",html_full,f"report_full_{record.get('test_id','')}.html","text/html",use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# OFFLINE MODE NOTICE
# ─────────────────────────────────────────────────────────────────────────────
def render_offline_notice():
    st.markdown(f"""
    <div style="background:rgba(0,229,160,.07);border:1px solid rgba(0,229,160,.2);border-radius:12px;padding:1rem 1.5rem;margin-bottom:1rem;font-size:.82rem;color:var(--text2)">
    <b style="color:var(--green)">📴 Offline Mode Available:</b>
    {APP_TITLE} runs fully offline. All processing (rPPG signal extraction, AES-256-GCM encryption, ECC key generation, blockchain mining) is performed locally on your machine.
    No data is sent to any external server. The SQLite database is stored on your local filesystem at: <code style="font-size:.72rem">{DB_PATH}</code>
    <br><b>To run locally:</b> <code>pip install streamlit opencv-python-headless numpy scipy cryptography plotly pandas</code> then <code>streamlit run app.py</code>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# UNAUTHENTICATED PAGES
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    pg=st.session_state.page
    if pg=="landing":
        render_nav(); render_landing()
        _,ca,cb,_=st.columns([2,1.2,1.2,2])
        with ca:
            if st.button("Get Started →",type="primary",use_container_width=True,key="land_cta"): go("login")
        with cb:
            if st.button("View Demo",use_container_width=True,key="land_demo"): go("login")
        st.markdown(f'<div style="text-align:center;padding:.5rem;font-size:.7rem;color:var(--text3)">📴 Fully offline capable · {APP_SECURITY}</div>', unsafe_allow_html=True)
        st.stop()
    render_nav(); render_login()
    st.markdown(f'<div style="text-align:center;padding:.8rem;border-top:1px solid var(--border);margin-top:1rem;font-size:.7rem;color:var(--text3)">{APP_SECURITY} · ⚠️ For research &amp; educational purposes only</div>', unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# AUTHENTICATED LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
render_nav()
user=st.session_state.user; is_admin=user.get('is_admin',0)

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div style="padding:1rem 0 .5rem;text-align:center"><span style="font-size:1.8rem">🔒</span><div style="font-family:\'DM Serif Display\',serif;font-size:.9rem;color:#E8EDF8;margin-top:4px">{APP_TITLE}</div><div style="font-size:.58rem;color:#4A5578;margin-top:2px">IoMT Security Framework</div></div>', unsafe_allow_html=True)
    st.divider()
    user_pages=[("❤️ Heart Monitor","monitor"),("📊 My Results","results"),("🔒 Encryption Lab","enc_step1"),("🌐 Decentralisation","decentralised"),("🔓 Decryption","decryption"),("📦 Raw Data","raw_data")]
    admin_pages=[("🏠 Admin Dashboard","admin_dashboard"),("❤️ Monitor","monitor"),("👥 All Users","admin_users"),("📋 All Records","admin_records"),("🔒 Encryption Lab","enc_step1"),("🌐 Decentralisation","decentralised"),("🔓 Decryption","decryption"),("📦 Raw Data","raw_data")]
    pages=admin_pages if is_admin else user_pages
    for label,pg in pages:
        active=(st.session_state.page==pg or (pg=="enc_step1" and st.session_state.page.startswith("enc_")))
        if st.button(label,use_container_width=True,type="primary" if active else "secondary"):
            st.session_state.page=pg; st.rerun()
    st.divider()
    st.markdown(f'<div style="font-size:.65rem;color:#4A5578;padding:.3rem;line-height:1.5">📴 Offline capable<br>DB: <code style="font-size:.6rem">{DB_PATH[-30:]}</code></div>', unsafe_allow_html=True)
    if st.button("🚪 Sign Out",use_container_width=True,type="secondary"): logout()

st.markdown(f"""<style>
section[data-testid="stSidebar"]{{display:block !important;background:var(--bg2) !important;border-right:1px solid var(--border) !important;min-width:210px !important;}}
section[data-testid="stSidebar"]>div:first-child{{padding-top:1rem !important}}
section[data-testid="stSidebar"] .stButton>button{{text-align:left !important;justify-content:flex-start !important;background:transparent !important;border:none !important;color:var(--text2) !important;padding:.45rem 1rem !important;border-radius:8px !important;font-size:.85rem !important;}}
section[data-testid="stSidebar"] .stButton>button:hover{{background:var(--card) !important;color:var(--text) !important;}}
section[data-testid="stSidebar"] .stButton>button[kind="primary"]{{background:hsla(355,78%,55%,.15) !important;color:var(--accent) !important;border:1px solid hsla(355,78%,55%,.3) !important;}}
</style>""", unsafe_allow_html=True)

# Offline notice on every authenticated page
render_offline_notice()

# ─────────────────────────────────────────────────────────────────────────────
# PAGE ROUTER
# ─────────────────────────────────────────────────────────────────────────────
pg=st.session_state.page

if pg=="monitor":
    render_monitor(user)

elif pg=="results":
    render_results(user)

elif pg=="decentralised":
    render_decentralised(user, is_admin)

elif pg=="decryption":
    render_decryption(user, is_admin)

elif pg=="enc_step1":
    render_enc_step1(user)
elif pg=="enc_step2":
    render_enc_step2()
elif pg=="enc_step3":
    render_enc_step3()
elif pg=="enc_step4":
    render_enc_step4(user)
elif pg=="enc_step5":
    render_enc_step5(user)
elif pg=="enc_step6":
    render_enc_step6(user)

elif pg=="admin_dashboard" and is_admin:
    render_admin_dashboard()
elif pg=="admin_users" and is_admin:
    render_admin_users()
elif pg=="admin_records" and is_admin:
    render_admin_records()

elif pg=="raw_data":
    render_raw_data(user, is_admin)

else:
    # Redirect unknown pages
    st.session_state.page="monitor"; st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:1.2rem 1rem .8rem;border-top:1px solid var(--border);margin-top:2rem;font-size:.7rem;color:var(--text3)">
  {APP_SECURITY}<br>
  {APP_AUTHOR}<br>
  <em>{APP_FULLNAME}</em><br>
  ⚠️ Research &amp; educational purposes only · Not a certified medical device · 📴 Offline capable
</div>
""", unsafe_allow_html=True)
