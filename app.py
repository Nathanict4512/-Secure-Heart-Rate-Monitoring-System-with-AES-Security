def render_nav():
    """Sticky navbar — SVG logo + REAL Streamlit nav buttons (clickable)."""
    u = st.session_state.user

    if u and u.get("is_admin"):
        nav_items = [
            ("admin_dashboard", "🏠 Dashboard"),
            ("monitor",         "❤️ Monitor"),
            ("admin_users",     "👥 Users"),
            ("admin_records",   "📋 Records"),
            ("enc_step1",       "🔒 Encryption Lab"),
        ]
    elif u:
        nav_items = [
            ("monitor",    "❤️ Monitor"),
            ("results",    "📊 My Results"),
            ("enc_step1",  "🔒 Encryption Lab"),
            ("raw_data",   "📦 Data"),
        ]
    else:
        nav_items = []

    # ── Inject CSS to make st.button look like nav links ─────────────────────
    st.markdown("""
    <style>
    /* Nav wrapper — sticky bar */
    .cs-nav-row {
      display:flex; align-items:center; justify-content:space-between;
      background:var(--nav_bg, #0F1628);
      border-bottom:1px solid var(--border);
      padding:.55rem 1.5rem;
      margin-bottom:1.5rem;
      position:sticky; top:0; z-index:100;
      box-shadow:0 4px 20px rgba(0,0,0,.4);
    }
    /* Hide all default button chrome inside nav buttons zone */
    div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button {
      background: transparent !important;
      border: none !important;
      color: var(--text2) !important;
      font-size: .83rem !important;
      font-weight: 500 !important;
      padding: 5px 11px !important;
      border-radius: 8px !important;
      transition: all .2s !important;
      box-shadow: none !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button:hover {
      background: hsla(355,78%,55%,.08) !important;
      color: var(--text) !important;
      transform: none !important;
    }
    /* Active page button highlight */
    div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button[data-active="true"],
    .nav-btn-active > button {
      color: var(--accent) !important;
      background: hsla(355,78%,55%,.1) !important;
      border: 1px solid hsla(355,78%,55%,.2) !important;
    }
    /* Sign Out button in nav */
    .nav-signout > button {
      background: transparent !important;
      border: 1px solid var(--border) !important;
      color: var(--text2) !important;
      font-size: .78rem !important;
      padding: 4px 14px !important;
      border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Top brand row (logo + date) ───────────────────────────────────────────
    user_label = ""
    admin_badge = ""
    if u:
        admin_badge = " · <span style='color:#FFD166;font-size:.7rem'>ADMIN</span>" if u.get("is_admin") else ""
        user_label = f"👤 {u['full_name']}{admin_badge}"

    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
         padding:.45rem 1.5rem .1rem;border-bottom:none">
      <div style="display:flex;align-items:center;gap:.65rem">
        <div style="animation:heartbeat 1.5s ease-in-out infinite;display:flex">
          {LOGO_SVG_SM}
        </div>
        <div>
          <div style="font-family:'DM Serif Display',serif;font-size:1.05rem;
                      color:var(--text);line-height:1">CardioSecure</div>
          <div style="font-size:.58rem;color:var(--text3);letter-spacing:.1em;
                      text-transform:uppercase;margin-top:1px">Heart Rate Monitor</div>
        </div>
        <span style="font-size:.58rem;color:var(--text3);letter-spacing:.1em;
                     text-transform:uppercase;padding:2px 6px;
                     border:1px solid var(--border);border-radius:4px;
                     margin-left:2px;align-self:flex-start;margin-top:4px">v2.0</span>
      </div>
      <div style="font-size:.78rem;color:var(--text2)">
        {user_label} &nbsp;·&nbsp; {datetime.now().strftime("%d %b %Y")}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Nav buttons row ───────────────────────────────────────────────────────
    if not u:
        # Unauthenticated: just Sign In / Home
        _, cb, _ = st.columns([5, 1, 0.3])
        with cb:
            if st.session_state.page == "landing":
                if st.button("Sign In", key="nav_signin", type="primary"):
                    go("login")
            else:
                if st.button("← Home", key="nav_home"):
                    go("landing")
        st.markdown('<hr style="margin:0 0 .5rem;border-color:var(--border)">', unsafe_allow_html=True)
        return

    # Build columns: nav items + spacer + sign out
    num_items = len(nav_items)
    # Columns: [logo_spacer(2), item cols..., spacer(3), signout(1.2)]
    col_widths = [2] + [1.1] * num_items + [3, 1.2]
    all_cols = st.columns(col_widths)

    # Skip col 0 (spacer under logo)
    for i, (page_id, label) in enumerate(nav_items):
        col = all_cols[i + 1]
        is_active = (st.session_state.page == page_id or
                     (page_id == "enc_step1" and st.session_state.page.startswith("enc_")))
        with col:
            # Inject active styling via a wrapper div keyed to active state
            if is_active:
                st.markdown('<div class="nav-btn-active">', unsafe_allow_html=True)
            clicked = st.button(label, key=f"nav_{page_id}", use_container_width=False)
            if is_active:
                st.markdown('</div>', unsafe_allow_html=True)
            if clicked:
                go(page_id)

    # Sign out in last column
    with all_cols[-1]:
        st.markdown('<div class="nav-signout">', unsafe_allow_html=True)
        if st.button("Sign Out", key="nav_signout_main"):
            logout()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<hr style="margin:0 0 1rem;border-color:var(--border)">', unsafe_allow_html=True)
