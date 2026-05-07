def load_css():
    import os
    import streamlit as st

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    css_path = os.path.join(BASE_DIR, "style", "custom_dash_monitora.css")

    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)