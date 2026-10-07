from __future__ import annotations

import streamlit as st


def render_navigation(*, show_settings_hint: bool = True) -> None:
    """Render the same simple navigation on every Streamlit page.

    The normal user journey lives on Guided Research. Other pages are specialist
    workspaces and should be opened only when the guided flow points to them.
    """
    with st.sidebar:
        st.header("Navigate")
        st.page_link("main.py", label="🏠 Guided Research", help="Normal end-to-end workflow")
        st.page_link("pages/5_User_Guide.py", label="📘 User Guide", help="First-run walkthrough and terminology")
        st.divider()
        st.caption("Specialist workspaces")
        st.page_link("pages/3_Research_Evidence.py", label="🔎 Research Evidence")
        st.page_link("pages/4_Deep_Research_Thesis_Challenge.py", label="⚖️ Deep Research & Thesis Challenge")
        st.page_link("pages/1_Operator_Control.py", label="🎛️ Operator Control")
        st.page_link("pages/2_Runtime_Settings.py", label="⚙️ Runtime Settings")
        if show_settings_hint:
            st.caption("Tip: stay on Guided Research unless a step sends you here for more detail or control.")
