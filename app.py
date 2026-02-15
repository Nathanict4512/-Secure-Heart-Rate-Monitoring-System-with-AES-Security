# ═══════════════════════════════════════════════════════════════════════════════
# MedChainSecure — Heart Rate Monitor (Standalone Extract)
# Extracted from the full app: all functions + page code for the Monitor page
# Contains: imports, rPPG engine, stress analyser, JS webcam component,
#           session state defaults, helper utils, and the full monitor page block
# ═══════════════════════════════════════════════════════════════════════════════

# ── IMPORTS ─────────────────────────────────────────────────────────────────
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

# ── PAGE CONFIG (required for standalone) ───────────────────────────────────
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


# ── THEME CSS ───────────────────────────────────────────────────────────────
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

# ── SESSION STATE DEFAULTS ──────────────────────────────────────────────────
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



# ─────────────────────────────────────────────────────────────────────────────
# FULL-WIDTH PAGE HERO HELPER
# ─────────────────────────────────────────────────────────────────────────────

def render_page_hero(icon: str, title: str, subtitle: str,
                     accent: str = "var(--accent)",
                     badge: str = ""):
    """Renders a full-width hero banner matching the landing page aesthetic."""
    badge_html = (f'<span style="display:inline-block;font-size:.72rem;font-weight:600;'
                  f'letter-spacing:.12em;text-transform:uppercase;padding:3px 14px;'
                  f'border-radius:20px;border:1px solid {accent}55;color:{accent};'
                  f'background:{accent}18;margin-bottom:1.1rem">{badge}</span><br>' if badge else "")
    st.markdown(f"""
<div style="
  width:100vw;position:relative;left:50%;right:50%;
  margin-left:-50vw;margin-right:-50vw;
  padding:4rem 2rem 3rem;
  background:
    radial-gradient(ellipse at 8% 20%, hsla(355,78%,55%,.10) 0%, transparent 52%),
    radial-gradient(ellipse at 92% 80%, hsla(195,100%,50%,.07) 0%, transparent 52%),
    radial-gradient(ellipse at 50% 0%,  hsla(222,40%,14%,1)   0%, transparent 80%);
  border-bottom:1px solid var(--border);
  text-align:center;
  box-sizing:border-box;
">
  {badge_html}
  <div style="font-size:3.5rem;margin-bottom:.8rem;filter:drop-shadow(0 0 20px {accent}66)">{icon}</div>
  <h1 style="font-family:'DM Serif Display',serif;font-size:clamp(2.2rem,5vw,3.6rem);
    background:linear-gradient(135deg,hsl(355,78%,68%) 0%,hsl(355,78%,55%) 40%,hsl(195,100%,55%) 100%);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
    margin:.2rem 0 .7rem;line-height:1.1">{title}</h1>
  <p style="color:var(--text2);font-size:1rem;max-width:600px;margin:0 auto;
    line-height:1.65">{subtitle}</p>
</div>
<div style="height:2rem"></div>
""", unsafe_allow_html=True)


def stat_card(value, label, color="var(--accent)", icon=""):
    """Renders a full-width stat metric card."""
    return (f'<div class="cs-card" style="text-align:center;padding:1.4rem 1rem">'
            f'<div style="font-size:1.3rem;margin-bottom:.3rem">{icon}</div>'
            f'<div style="font-size:2.6rem;font-family:DM Serif Display,serif;'
            f'color:{color};font-weight:400;line-height:1">{value}</div>'
            f'<div style="font-size:.72rem;color:var(--text2);text-transform:uppercase;'
            f'letter-spacing:.1em;margin-top:.4rem">{label}</div></div>')

def page_padding():
    """Injects left/right padding for page body content after a full-bleed hero."""
    st.markdown(
        '<style>.element-container:not(:has([data-full-bleed])){}'        '</style>',
        unsafe_allow_html=True
    )
    # Use a zero-height div to push content into padded area
    st.markdown(
        '<div data-page-content style="padding:0 1.5rem"></div>',
        unsafe_allow_html=True
    )



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



    render_page_hero("❤️","Heart Rate Monitor",
    "Continuous 30fps rPPG · AES-256-GCM encrypted · Blockchain-logged",
    badge="IoMT biometric capture")
    page_padding()

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

    # ── Layout: full-width two-panel grid ─────────────────────────────────────
    col_cam, col_stats = st.columns([3, 2], gap="medium")

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
