"""
Streamlit Cloud entrypoint.

Loads API keys from Streamlit secrets (Cloud) before importing the app, so
`call_review_app` / `call_audio_pipeline` see os.environ. Local runs still work
with a `.env` file in this folder (optional).
"""

from __future__ import annotations

import os

import streamlit as st

try:
    _secrets = st.secrets
    for _key in ("GROQ_API_KEY", "PYANNOTE_API_KEY"):
        if _key in _secrets and not os.environ.get(_key):
            os.environ[_key] = str(_secrets[_key]).strip()
except Exception:
    pass

from call_review_app import main

main()
