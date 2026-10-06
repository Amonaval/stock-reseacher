from __future__ import annotations

import streamlit as st

from runtime_settings import get_screener_delay, save_screener_delay

st.set_page_config(page_title="Runtime Settings · Personal AI Stock Researcher", layout="wide")
st.title("Runtime Settings")
st.caption("Control external-source behavior without changing research logic.")

st.markdown("## Screener pacing")
current = get_screener_delay()
delay = st.slider(
    "Delay between Screener requests (seconds)",
    min_value=0.0,
    max_value=10.0,
    value=float(current),
    step=0.25,
    help=(
        "Applied to connection/navigation, strategy execution, pagination and company-page research. "
        "A slower delay reduces request pressure at the cost of longer runs."
    ),
)

c1, c2 = st.columns([1, 3])
if c1.button("Save pacing", type="primary"):
    saved = save_screener_delay(delay)
    st.success(f"Saved Screener delay: {saved:.2f}s between requests.")

c2.info(
    "Recommended starting point: 1.5–2.0 seconds for normal research. "
    "Increase it if Screener becomes slow, starts rejecting requests, or you are running many companies."
)

st.markdown("### Practical presets")
st.write("**Fast local test:** 0.75–1.0s")
st.write("**Normal research:** 1.5–2.0s")
st.write("**Large run / conservative:** 2.5–4.0s")

st.warning(
    "This is pacing, not a guarantee against rate limiting. The app should remain conservative and must not attempt to bypass access controls."
)
