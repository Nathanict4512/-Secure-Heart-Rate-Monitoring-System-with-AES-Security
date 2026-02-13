# app.py
import streamlit as st
import numpy as np
import time
from datetime import datetime
import random

# ───────────────────────────────────────────────
#  Page config
# ───────────────────────────────────────────────

st.set_page_config(
    page_title="CardioSecure – Heart Rate Monitor",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ───────────────────────────────────────────────
#  Custom CSS – trying to match your design tokens
# ───────────────────────────────────────────────

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@300;400;500&display=swap');

:root {
    --bg:           hsl(222,58%,5%);
    --bg2:          hsl(222,50%,8%);
    --card:         hsl(222,40%,12%);
    --card2:        hsl(222,35%,16%);
    --border:       hsl(222,30%,22%);
    --text:         hsl(220,30%,92%);
    --text2:        hsl(220,15%,55%);
    --text3:        hsl(222,20%,35%);
    --accent:       hsl(355,78%,55%);
    --accent2:      hsl(355,78%,68%);
    --green:        hsl(160,100%,45%);
    --yellow:       hsl(40,100%,70%);
    --cyan:         hsl(195,100%,50%);
    --purple:       hsl(265,70%,60%);
    --radius:       0.75rem;
}

[data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse at 10% 20%, hsla(355,78%,55%,0.07) 0%, transparent 50%),
                radial-gradient(ellipse at 90% 80%, hsla(195,100%,50%,0.05) 0%, transparent 50%),
                var(--bg);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3, h4 {
    font-family: 'DM Serif Display', serif;
}

code, pre, .stCode, .stMarkdown code {
    font-family: 'DM Mono', monospace !important;
    background: var(--card2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius);
}

/* Navbar approximation */
section[data-testid="stSidebar"] { display: none !important; }

div[data-testid="stToolbar"] { display: none !important; }

header { visibility: hidden !important; }

.st-emotion-cache-1y4p8pa {
    max-width: 1400px !important;
    padding: 1rem 2rem !important;
}

/* Card & glow effect */
.card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
    transition: all 0.25s ease;
}

.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04),
                0 0 0 1px hsla(355,78%,55%,0.18);
}

/* Badge styles */
.badge-normal  { background: hsla(160,100%,45%,0.15); color: hsl(160,100%,45%); border: 1px solid hsla(160,100%,45%,0.4); }
.badge-warning { background: hsla(40,100%,70%,0.15);  color: hsl(40,100%,70%);  border: 1px solid hsla(40,100%,70%,0.4);  }
.badge-danger  { background: hsla(355,78%,55%,0.15);  color: hsl(355,78%,55%);  border: 1px solid hsla(355,78%,55%,0.4);  }

.badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.8125rem;
    font-weight: 500;
}

/* Heartbeat pulse */
@keyframes heartbeat {
    0%, 100% { transform: scale(1); }
    14%  { transform: scale(1.18); }
    28%  { transform: scale(1); }
    42%  { transform: scale(1.12); }
    70%  { transform: scale(1); }
}
.heartbeat { animation: heartbeat 1.8s ease-in-out infinite; }

/* ECG line */
.ecg-line {
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    margin: 1.5rem 0;
    animation: ecg 3.5s linear infinite;
}
@keyframes ecg { 0%,100% { opacity: 0.4; } 50% { opacity: 1; } }

</style>""", unsafe_allow_html=True)

# ───────────────────────────────────────────────
#  Fake session / auth
# ───────────────────────────────────────────────

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "page" not in st.session_state:
    st.session_state.page = "landing"

# ───────────────────────────────────────────────
#  Simple top navigation
# ───────────────────────────────────────────────

def nav_bar():
    cols = st.columns([1,5,1])

    with cols[0]:
        st.markdown("<div style='font-size:1.6rem; font-family:DM Serif Display,serif; color:var(--text);'>❤️ CardioSecure</div>", unsafe_allow_html=True)

    with cols[1]:
        if st.session_state.logged_in:
            pages = ["Monitor", "Results", "Encryption Lab"]
            if st.session_state.is_admin:
                pages += ["Admin Dashboard", "Users"]

            sel = st.segmented_control("page", pages, default="Monitor",
                                       format_func=lambda x: f"  {x}  ")
            st.session_state.page = sel.lower().replace(" ", "_")

    with cols[2]:
        if st.session_state.logged_in:
            if st.button("Sign out", type="secondary"):
                st.session_state.logged_in = False
                st.session_state.page = "landing"
                st.rerun()
        else:
            if st.button("Sign in", type="primary"):
                st.session_state.logged_in = True
                st.session_state.is_admin = random.random() < 0.25   # demo
                st.session_state.page = "monitor"
                st.rerun()

# ───────────────────────────────────────────────
#  Fake heart rate monitor page
# ───────────────────────────────────────────────

def page_monitor():
    st.markdown("<h1 class='gradient-text' style='background: linear-gradient(90deg, var(--accent), var(--cyan)); -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>Heart Rate Monitor</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:var(--text2);'>Real-time rPPG via webcam • Hybrid encrypted storage</p>", unsafe_allow_html=True)

    colA, colB = st.columns([3,2], gap="md")

    with colA:
        st.markdown("<div class='card'>", unsafe_allow_html=True)

        placeholder = st.empty()

        if st.button("Start Measurement", type="primary", use_container_width=True):
            with st.spinner("Acquiring signal..."):
                for i in range(1, 101):
                    time.sleep(0.08)
                    bpm = random.randint(58, 98)
                    placeholder.markdown(f"""
                    <div style='text-align:center; padding:2rem 0;'>
                        <div style='font-size:5.5rem; line-height:1;' class='heartbeat'>❤️</div>
                        <div style='font-size:4.2rem; font-weight:600; color:var(--accent);'>{bpm}</div>
                        <div style='font-size:1.4rem; color:var(--text2);'>BPM</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3>Current Status</h3>", unsafe_allow_html=True)

        bpm = random.randint(62, 92)
        if bpm < 60:
            cat, cls = "Bradycardia", "badge-danger"
        elif bpm <= 100:
            cat, cls = "Normal", "badge-normal"
        else:
            cat, cls = "Tachycardia", "badge-warning"

        st.markdown(f"""
        <div style='text-align:center; padding:1.5rem 0;'>
            <div style='font-size:3.8rem; font-weight:700; color:var(--accent);'>{bpm}</div>
            <div style='font-size:1.1rem; color:var(--text2); margin:0.4rem 0;'>beats per minute</div>
            <span class='badge {cls}' style='font-size:1rem; padding:0.5rem 1.2rem;'>{cat}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='ecg-line'></div>", unsafe_allow_html=True)

        st.caption("• Resting heart rate (adult)")
        st.caption("• Measured via remote photoplethysmography")
        st.caption("• Not a medical device – research only")

        st.markdown("</div>", unsafe_allow_html=True)

# ───────────────────────────────────────────────
#  Very simplified other pages
# ───────────────────────────────────────────────

def page_landing():
    st.markdown("""
    <div style='text-align:center; padding:6rem 1rem 4rem;'>
        <div style='font-size:7rem;' class='heartbeat'>❤️</div>
        <h1 style='font-size:4.2rem; margin:1.5rem 0 1rem;'>CardioSecure</h1>
        <p style='font-size:1.4rem; color:var(--text2); max-width:42rem; margin:0 auto 2.5rem;'>
            Non-contact heart rate monitoring with hybrid encryption
        </p>
        <div>
            <button style='font-size:1.3rem; padding:1rem 2.5rem; background:var(--accent); color:white; border:none; border-radius:var(--radius); cursor:pointer;'>
                Begin Measurement →
            </button>
        </div>
    </div>
    """, unsafe_allow_html=True)

def page_results():
    st.title("Measurement History")
    st.info("This is a placeholder – real implementation would show encrypted & decrypted records")

def page_encryption_lab():
    st.title("Encryption Laboratory")
    st.markdown("Step-by-step visualization of AES-256-GCM + ECC key exchange")

def page_admin_dashboard():
    st.title("Admin Dashboard")
    st.markdown("Overview – users – recent activity – system metrics")

# ───────────────────────────────────────────────
#  Router
# ───────────────────────────────────────────────

nav_bar()

if not st.session_state.logged_in:
    page_landing()
else:
    match st.session_state.page:
        case "monitor":
            page_monitor()
        case "results":
            page_results()
        case "encryption_lab":
            page_encryption_lab()
        case "admin_dashboard" | "users":
            page_admin_dashboard()
        case _:
            page_monitor()

# Footer
st.markdown("""
<div style='margin-top:6rem; padding:2rem; text-align:center; color:var(--text2); font-size:0.95rem; border-top:1px solid var(--border);'>
    🔒 AES-256-GCM + ECC-SECP256R1 • Research & educational use only • Not a certified medical device
    <br><br>
    EBSU/PG/PhD/2021/10930 • Yunisa Sunday
</div>
""", unsafe_allow_html=True)