"""
TVS 3-wheeler call rating desk: upload audio → diarize + translate + align transcript,
then score the call against TVS_3wheeler_call_qa_rubric.md (1–5 stars per criterion).
"""

from __future__ import annotations

import html
import json
import os
import re
import tempfile
from pathlib import Path

import streamlit as st
from groq import APIStatusError, Groq

from aligned_transcript import _load_dotenv
from call_audio_pipeline import process_call_recording

SCRIPT_DIR = Path(__file__).resolve().parent
RUBRIC_PATH = SCRIPT_DIR / "TVS_3wheeler_call_qa_rubric.md"

CRITERION_LABELS: dict[str, str] = {
    "1.1": "Greeting & identity",
    "1.2": "Purpose & consent",
    "1.3": "Callback handling",
    "1.4": "Not interested path",
    "2.1": "Customer details",
    "2.2": "Buying intent & lead tag",
    "2.3": "Product / scheme pitch",
    "2.4": "MH eligibility & documents",
    "2.5": "Closing",
    "3.1": "Follow-up script",
    "3.2": "Enquiry in progress (E1–E5)",
}

ALL_CRITERION_IDS: tuple[str, ...] = tuple(CRITERION_LABELS.keys())

_load_dotenv(SCRIPT_DIR / ".env")

_APP_STYLES = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  --jam-ink: #0c1222;
  --jam-muted: #64748b;
  --jam-border: rgba(15, 23, 42, 0.1);
}

[data-testid="stAppViewContainer"] {
  background: linear-gradient(165deg, #f0f7f5 0%, #edf2fb 45%, #f7f4fc 100%) !important;
  background-attachment: fixed !important;
}

[data-testid="stHeader"] {
  background: transparent !important;
}

.block-container {
  padding-top: 1.5rem !important;
  padding-bottom: 2.5rem !important;
  max-width: 1400px !important; /* Widened for better side-by-side view */
}

.stApp,
.stApp button,
.stApp input,
.stApp textarea,
[data-testid="stMarkdownContainer"] {
  font-family: 'Outfit', system-ui, sans-serif !important;
}

.hero-title {
  font-family: 'Outfit', system-ui, sans-serif !important;
  font-weight: 700 !important;
  font-size: 1.85rem !important;
  letter-spacing: -0.025em !important;
  color: var(--jam-ink) !important;
  margin: 0 0 0.35rem 0 !important;
  line-height: 1.2 !important;
}

.hero-sub {
  font-family: 'Outfit', system-ui, sans-serif !important;
  font-size: 0.95rem !important;
  color: var(--jam-muted) !important;
  line-height: 1.55 !important;
  margin: 0 !important;
  max-width: 44rem;
}

.section-title {
  font-family: 'Outfit', system-ui, sans-serif !important;
  font-weight: 600 !important;
  font-size: 1.08rem !important;
  color: var(--jam-ink) !important;
  margin: 0 0 0.35rem 0 !important;
  letter-spacing: -0.02em !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
  background: rgba(255, 255, 255, 0.88) !important;
  backdrop-filter: blur(10px);
  border-radius: 14px !important;
  box-shadow: 0 2px 16px rgba(15, 23, 42, 0.05) !important;
  padding: 0.25rem 0.5rem 0.75rem 0.5rem !important;
  border-color: var(--jam-border) !important;
  overflow: visible !important;
}

[data-testid="stFileUploader"] {
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif !important;
}

.stButton > button[kind="primary"] {
  border-radius: 10px !important;
  font-weight: 600 !important;
  min-height: 2.75rem !important;
  background: linear-gradient(180deg, #14b8a6 0%, #0d9488 55%, #0f766e 100%) !important;
  border: none !important;
  box-shadow: 0 2px 10px rgba(13, 148, 136, 0.3) !important;
}

.stButton > button[kind="primary"]:disabled {
  background: #e2e8f0 !important;
  color: #94a3b8 !important;
  box-shadow: none !important;
}

/* Enhanced Transcript Readability */
div[data-testid="stTextArea"] textarea {
  font-family: 'IBM Plex Mono', ui-monospace, monospace !important;
  font-size: 0.9rem !important;
  line-height: 1.6 !important;
  border-radius: 10px !important;
  border: 1px solid var(--jam-border) !important;
  background: #f8fafc !important;
  color: #1e293b !important;
  -webkit-text-fill-color: #1e293b !important; /* Forces color in disabled state on WebKit/Chrome */
  opacity: 1 !important; /* Prevents the browser from fading the text */
}

/* Specific override for the disabled state */
div[data-testid="stTextArea"] textarea:disabled {
  background: #f1f5f9 !important; /* Slightly darker background to indicate it's read-only */
  color: #1e293b !important;
  -webkit-text-fill-color: #1e293b !important;
  cursor: text !important; /* Keeps the text selection cursor instead of the 'not-allowed' circle */
}

[data-testid="stExpander"] {
  border: 1px solid var(--jam-border) !important;
  border-radius: 10px !important;
  background: rgba(255, 255, 255, 0.7) !important;
}

.rating-overall {
  font-size: 2.5rem;
  letter-spacing: 0.05em;
  color: #0d9488;
  font-weight: 700;
}

# /* --- Fix for invisible text in Dark Mode --- */
# [data-testid="stMarkdownContainer"] p,
# [data-testid="stMarkdownContainer"] span {
#   color: var(--jam-ink) !important;
# }

# [data-testid="stCaptionContainer"] p,
# [data-testid="stCaptionContainer"] span,
# div[data-testid="caption"] {
#   color: var(--jam-muted) !important;
# }

# /* --- Fix for invisible text in Dark Mode --- */
# [data-testid="stMarkdownContainer"] p,
# [data-testid="stMarkdownContainer"] span,
# [data-testid="stMarkdownContainer"] strong,
# [data-testid="stMarkdownContainer"] b,
# [data-testid="stMarkdownContainer"] li {
#   color: var(--jam-ink) !important;
# }

# [data-testid="stCaptionContainer"] p,
# [data-testid="stCaptionContainer"] span,
# div[data-testid="caption"] {
#   color: var(--jam-muted) !important;
# }

/* --- Fix for text colors across Main and Sidebar --- */

/* 1. Main Area: Force dark text for the light background */
.block-container [data-testid="stMarkdownContainer"] p,
.block-container [data-testid="stMarkdownContainer"] span,
.block-container [data-testid="stMarkdownContainer"] strong,
.block-container [data-testid="stMarkdownContainer"] b,
.block-container [data-testid="stMarkdownContainer"] li {
  color: var(--jam-ink) !important;
}

.block-container [data-testid="stCaptionContainer"] p,
.block-container [data-testid="stCaptionContainer"] span,
.block-container div[data-testid="caption"] {
  color: var(--jam-muted) !important;
}

/* 2. Sidebar: Force light text for the dark sidebar background */
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] b {
  color: #f8fafc !important; 
}

[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] span,
[data-testid="stSidebar"] div[data-testid="caption"] {
  color: #94a3b8 !important; 
}

/* 3. Fix the Sidebar Expand/Toggle Arrow */
/* 3. Fix the Sidebar Expand/Toggle Arrows (Hardcoded Dark Background) */

/* Arrow outside (to open sidebar) */
[data-testid="collapsedControl"],
[data-testid="collapsedControl"]:hover,
[data-testid="collapsedControl"]:focus {
  background-color: var(--jam-ink) !important; /* Dark/Black background */
  border-radius: 6px !important;
  box-shadow: 0 4px 12px rgba(12, 18, 34, 0.15) !important;
  transition: all 0.2s ease;
}

[data-testid="collapsedControl"] svg {
  fill: #ffffff !important; /* Crisp white arrow icon */
  color: #ffffff !important;
}

/* Arrow inside (to close sidebar) */
[data-testid="stSidebarCollapseButton"] svg,
button[kind="headerNoPadding"] svg {
  fill: #ffffff !important; /* White arrow inside the dark sidebar */
  color: #ffffff !important;
}
"""

def _inject_app_styles() -> None:
    st.markdown(f"<style>{_APP_STYLES}</style>", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def _read_default_rubric_from_disk(path: str, mtime: float) -> str:
    p = Path(path)
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8")

def _default_rubric_text() -> str:
    if not RUBRIC_PATH.is_file():
        return ""
    try:
        mt = RUBRIC_PATH.stat().st_mtime
    except OSError:
        mt = 0.0
    return _read_default_rubric_from_disk(str(RUBRIC_PATH.resolve()), mt)

def _get_active_rubric() -> tuple[str, str]:
    """Return (rubric markdown, human-readable source label)."""
    up = st.session_state.get("uploaded_rubric_md")
    if isinstance(up, str) and up.strip():
        name = st.session_state.get("uploaded_rubric_name") or "uploaded.md"
        return up.strip(), f"uploaded: {name}"
    disk = _default_rubric_text()
    if disk.strip():
        return disk.strip(), f"default: {RUBRIC_PATH.name}"
    return "", "(none)"

def _stars_unicode(n: int | None) -> str:
    if n is None or n == "N/A" or (isinstance(n, str) and n.upper() == "N/A"):
        return "— N/A"
    try:
        v = int(n)
    except (TypeError, ValueError):
        return "— ?"
    v = max(1, min(5, v))
    return "★" * v + "☆" * (5 - v) + f" ({v}/5)"

def _extract_json_object(text: str) -> dict:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
        t = re.sub(r"\s*```\s*$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    i = t.find("{")
    j = t.rfind("}")
    if i != -1 and j > i:
        try:
            return json.loads(t[i : j + 1])
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON parse failed inside extracted object: {e}") from e
    raise ValueError("Model output did not contain a parseable JSON object.")

def _build_rating_messages(rubric: str, aligned: str, english: str) -> list[dict[str, str]]:
    schema = """{
  "call_type_guess": "first_contact|callback|follow_up|enquiry_in_progress|not_interested|unknown",
  "scores": [
    {"id": "1.1", "stars": <integer 1-5 or null if not applicable>, "evidence": "<short quote or paraphrase>", "notes": "<optional>"}
  ],
  "overall_call_quality_stars": <integer 1-5>,
  "top_3_improvements": ["<string>", "<string>", "<string>"]
}"""
    rules = f"""You are a strict, fair QA scorer for TVS Motor 3-wheeler outbound calls.

RUBRIC (follow star anchors and criteria IDs from this document):
---
{rubric}
---

TASK:
- Read the CALL TRANSCRIPT below.
- For EACH criterion ID in this exact list: {list(ALL_CRITERION_IDS)}
  produce exactly one object in "scores" with field "id" set to that criterion.
- Use "stars": null only when that criterion truly does not apply to this call (e.g. 1.4 if customer was interested throughout).
- Otherwise stars must be an integer from 1 to 5 per rubric anchors.
- "evidence": one short line tied to the transcript when stars is not null.
- Set overall_call_quality_stars (1-5) holistically.
- top_3_improvements: exactly 3 concise bullets for the agent.

OUTPUT RULES:
- Respond with ONE JSON object only. No markdown fences, no commentary before or after the JSON."""

    user_body = f"""CALL TRANSCRIPT (diarized, English translation timeline):

{aligned}

---
FULL ENGLISH TEXT (same call, single block):

{english if english.strip() else "(not provided)"}

---
JSON schema to match (types as described):
{schema}"""

    return [
        {"role": "system", "content": rules},
        {"role": "user", "content": user_body},
    ]

def _clip_for_llm(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[… truncated for API size; tail omitted …]"

def _run_tvs_rating(groq_key: str, aligned: str, english: str, rubric: str) -> dict:
    rubric = rubric.strip()
    if not rubric:
        raise FileNotFoundError(
            "No rubric text: upload a reference .md file in the scorecard panel, "
            f"or add `{RUBRIC_PATH.name}` beside the app."
        )
    rubric_c = _clip_for_llm(rubric, 100_000)
    aligned_c = _clip_for_llm(aligned.strip(), 48_000)
    english_c = _clip_for_llm((english or "").strip(), 24_000)
    client = Groq(api_key=groq_key)
    messages = _build_rating_messages(rubric_c, aligned_c, english_c)
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.1,
    )
    raw = (resp.choices[0].message.content or "").strip()
    if not raw:
        raise ValueError("Groq returned an empty response for scoring.")
    return {"raw": raw, "data": _extract_json_object(raw)}

def _normalize_scores(data: dict) -> list[dict]:
    by_id: dict[str, dict] = {}
    for row in data.get("scores") or []:
        if isinstance(row, dict) and row.get("id"):
            by_id[str(row["id"])] = row
    out: list[dict] = []
    for cid in ALL_CRITERION_IDS:
        r = by_id.get(cid, {"id": cid, "stars": None, "evidence": "", "notes": ""})
        out.append(r)
    return out

def _init_session() -> None:
    defaults = {
        "audio_bytes": None,
        "audio_name": "",
        "aligned_text": "",
        "lines": [],
        "english_translation": "",
        "warnings": [],
        "tvs_rating": None,
        "tvs_rating_raw": "",
        "tvs_rating_error": "",
        "uploaded_rubric_md": None,
        "uploaded_rubric_name": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def _render_rating_block(data: dict) -> None:
    ctype = html.escape(str(data.get("call_type_guess") or "unknown"))
    
    overall = data.get("overall_call_quality_stars")
    try:
        oi = int(overall) if overall is not None else None
    except (TypeError, ValueError):
        oi = None
        
    # High-level metrics at the top of the container
    st.markdown(
        f'<div style="text-align: center; padding-bottom: 1rem;">'
        f'<p class="rating-overall">{html.escape(_stars_unicode(oi))}</p>'
        f'<p style="margin:0;font-size:0.95rem;color:#64748b;font-weight:500;">Overall Quality · Model Guess: {ctype.replace("_", " ").title()}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    rows = _normalize_scores(data)
    for row in rows:
        cid = row.get("id", "")
        label = CRITERION_LABELS.get(str(cid), str(cid))
        stars = row.get("stars")
        ev = str(row.get("evidence") or "").strip()
        notes = str(row.get("notes") or "").strip()
        su = _stars_unicode(stars if stars is not None else None)
        st.markdown(f"**{html.escape(str(cid))}** — {html.escape(label)}  \n{html.escape(su)}")
        if ev:
            st.caption(f"_{html.escape(ev[:280] + ('…' if len(ev) > 280 else ''))}_")
        if notes:
            st.caption("Note: " + html.escape(notes[:200]))
        st.markdown("")

    imp = data.get("top_3_improvements") or []
    if isinstance(imp, list) and imp:
        st.divider()
        st.markdown("**💡 Top 3 Improvements**")
        for i, line in enumerate(imp[:3], 1):
            st.markdown(f"{i}. {html.escape(str(line))}")

def main() -> None:
    st.set_page_config(
        page_title="TVS call ratings · JAM",
        layout="wide",
        page_icon="⭐",
        initial_sidebar_state="expanded",
    )
    _init_session()
    _inject_app_styles()

    # ==========================================
    # 1. SIDEBAR: Workflow & Inputs
    # ==========================================
    with st.sidebar:
        st.markdown("### ⚙️ Workflow Control")
        
        # Step 1: Audio Upload
        st.markdown("**1. Upload Recording**")
        uploaded = st.file_uploader(
            "audio_uploader",
            type=["wav", "mp3"],
            label_visibility="collapsed",
            help="Two-speaker calls align best."
        )

        if uploaded is not None:
            st.session_state.audio_bytes = uploaded.getvalue()
            st.session_state.audio_name = uploaded.name
            st.audio(st.session_state.audio_bytes, format=f"audio/{uploaded.name.split('.')[-1]}")

        run_clicked = st.button(
            "Run pipeline",
            type="primary",
            disabled=uploaded is None,
            use_container_width=True,
            key="tvs_run_pipeline_btn",
            help="Diarize + translate to English + align speakers."
        )

        st.divider()

        # Step 2: Rubric Configuration
        st.markdown("**2. Quality Rubric**")
        rub_file = st.file_uploader(
            "reference_rubric_md",
            type=["md"],
            label_visibility="collapsed",
            help="Optional. Replaces the default rubric on disk for this session.",
            key="reference_rubric_md_uploader",
        )
        
        if rub_file is not None:
            try:
                st.session_state.uploaded_rubric_md = rub_file.getvalue().decode("utf-8", errors="replace")
                st.session_state.uploaded_rubric_name = rub_file.name
            except Exception as e:
                st.warning(f"Could not read rubric: {e}")

        if st.session_state.uploaded_rubric_md:
            st.caption(f"Uploaded: **{html.escape(st.session_state.uploaded_rubric_name or 'script.md')}**")
            if st.button("Use default rubric", key="tvs_clear_rubric_btn", use_container_width=True):
                st.session_state.uploaded_rubric_md = None
                st.session_state.uploaded_rubric_name = ""
                st.session_state.tvs_rating = None
                st.session_state.tvs_rating_raw = ""
                st.session_state.tvs_rating_error = ""
                st.rerun()
        else:
            _, rubric_src = _get_active_rubric()
            st.caption(f"Active rubric: `{html.escape(rubric_src)}`")

        st.divider()

        # Step 3: Scoring Trigger
        st.markdown("**3. QA Scoring**")
        has_tr = bool(st.session_state.aligned_text.strip())
        score_clicked = st.button(
            "Score this call",
            type="primary",
            disabled=not has_tr,
            use_container_width=True,
            key="tvs_score_call_btn",
            help="Scores the transcript with Groq + TVS rubric.",
        )

    # ==========================================
    # 2. EVENT HANDLERS (Pipeline & Scoring)
    # ==========================================
    if run_clicked and uploaded is not None:
        suffix = Path(uploaded.name).suffix or ".wav"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp_path = Path(tmp.name)
        try:
            tmp.write(uploaded.getvalue())
            tmp.flush()
            with st.spinner("Diarizing & translating…"):
                out = process_call_recording(tmp_path, script_dir=SCRIPT_DIR)
            st.session_state.aligned_text = out["text"]
            st.session_state.lines = out["lines"]
            st.session_state.english_translation = out.get("english_translation") or ""
            st.session_state.warnings = list(out.get("warnings") or [])
            st.session_state.tvs_rating = None
            st.session_state.tvs_rating_raw = ""
            st.session_state.tvs_rating_error = ""
            st.success("Transcript ready! Click 'Score this call' in the sidebar.")
        except Exception as e:
            st.error(str(e))
        finally:
            try:
                tmp.close()
            except Exception:
                pass
            if tmp_path.is_file():
                tmp_path.unlink(missing_ok=True)

    if score_clicked and has_tr:
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            st.session_state.tvs_rating_error = "GROQ_API_KEY missing in .env"
            st.session_state.tvs_rating = None
        else:
            st.session_state.tvs_rating_error = ""
            st.session_state.tvs_rating_raw = ""
            try:
                rb, _src = _get_active_rubric()
                if not rb.strip():
                    st.session_state.tvs_rating = None
                    st.session_state.tvs_rating_error = f"No rubric text found. Ensure `{RUBRIC_PATH.name}` exists."
                else:
                    with st.spinner("Scoring call against rubric…"):
                        out = _run_tvs_rating(
                            groq_key,
                            st.session_state.aligned_text,
                            st.session_state.english_translation or "",
                            rb,
                        )
                    st.session_state.tvs_rating = out["data"]
                    st.session_state.tvs_rating_raw = out["raw"]
                    st.toast("Scorecard updated.", icon="⭐")
            except Exception as e:
                st.session_state.tvs_rating = None
                st.session_state.tvs_rating_error = str(e)

    # ==========================================
    # 3. MAIN AREA: Dashboard Display
    # ==========================================
    st.markdown(
        '<p class="hero-title">JAM Customer Support Call Review</p>'
        '<p class="hero-sub">Upload an audio file in the sidebar to generate a transcript, then score it against your rubric.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    for w in st.session_state.warnings:
        st.warning(w)

    if st.session_state.tvs_rating_error:
        st.error(st.session_state.tvs_rating_error)

    if not st.session_state.aligned_text:
        st.info("👈 Please upload an audio file and run the pipeline from the sidebar to begin.")
    else:
        # Transcript gets slightly more room than the scorecard
        col_transcript, col_scorecard = st.columns([1.3, 1], gap="large")

        with col_transcript:
            st.markdown('<p class="section-title">📝 Aligned Transcript</p>', unsafe_allow_html=True)
            st.text_area(
                "transcript",
                st.session_state.aligned_text,
                height=650,
                label_visibility="collapsed",
                disabled=True
            )
            if st.session_state.english_translation:
                with st.expander("View Full English text (single block)"):
                    st.markdown(
                        '<div style="font-size:0.92rem;line-height:1.65;color:#334155;">'
                        + html.escape(st.session_state.english_translation).replace("\n", "<br/>")
                        + "</div>",
                        unsafe_allow_html=True,
                    )

        with col_scorecard:
            st.markdown('<p class="section-title">🎯 QA Scorecard</p>', unsafe_allow_html=True)
            if not st.session_state.tvs_rating:
                st.info("Transcript generated. Click **Score this call** in the sidebar to view ratings.")
            else:
                with st.container(height=650, border=True):  # Added height=650 here!
                    _render_rating_block(st.session_state.tvs_rating)
                
                with st.expander("Raw model JSON"):
                    st.code(json.dumps(st.session_state.tvs_rating, ensure_ascii=False, indent=2), language="json")

if __name__ == "__main__":
    main()







