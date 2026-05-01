# TVS call ratings — Streamlit app (deploy bundle)

Zip this **whole folder** (or push it as a Git repo) and deploy on [Streamlit Community Cloud](https://streamlit.io/cloud).

## What’s included

| File | Role |
|------|------|
| `streamlit_app.py` | **Main file** for Cloud — injects secrets, then runs the UI |
| `call_review_app.py` | Streamlit UI (upload audio, pipeline, rubric upload, scoring) |
| `call_audio_pipeline.py` | Pyannote + Groq Whisper translation + alignment |
| `aligned_transcript.py` | Speaker–word alignment logic |
| `TVS_3wheeler_call_qa_rubric.md` | Default QA rubric (optional override via in-app upload) |

## Deploy on Streamlit Cloud

1. Put this folder in a **GitHub** repo (root = these files).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Pick the repo, branch, and set **Main file path** to:  
   `streamlit_app.py`
4. Under **Advanced settings** → **Python version** — use **3.11** or **3.12** (recommended).
5. **Secrets** (app gear → Secrets). Add **TOML**:

```toml
GROQ_API_KEY = "gsk_..."
PYANNOTE_API_KEY = "sk_..."
```

Save and **Reboot** the app.

6. Open the app URL. First **Run pipeline** on a WAV/MP3, then **Score this call**.

## Local run (optional)

```bash
cd streamlit_cloud_bundle
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
# copy .env with GROQ_API_KEY and PYANNOTE_API_KEY, or rely on secrets only in Cloud
streamlit run streamlit_app.py
```

## Notes

- **Do not commit** real API keys. Use Cloud **Secrets** or a local `.env` (listed in `.gitignore`).
- **Rubric**: the app loads `TVS_3wheeler_call_qa_rubric.md` from this folder, or you can upload another `.md` in the UI.
- **Audio**: Pyannote + Groq calls use your keys; long calls may hit rate/size limits on free tiers.

## Support

If the app fails to start, check Cloud **Logs** for missing secrets or import errors.
