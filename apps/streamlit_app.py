import logging

import requests
import streamlit as st
from dotenv import load_dotenv

# Load env before any pageant_assistant imports
load_dotenv()

from pageant_assistant.config.settings import (
    DEFAULT_STYLE,
    DEFAULT_TIME_LIMIT,
    GROQ_API_KEY,
    STYLE_PRESETS,
    VALID_TIME_LIMITS,
    WORDS_PER_SECOND,
)
from pageant_assistant.graphs.refiner import build_refiner_graph
from pageant_assistant.personas.manager import (
    format_persona_context,
    list_personas,
    load_persona,
)
from pageant_assistant.questions.bank import get_filter_options, get_random_question
from pageant_assistant.voice.audio import synthesize_speech, transcribe_audio

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Pageant AI Coach",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Session state defaults ---
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "shown_question_ids" not in st.session_state:
    st.session_state.shown_question_ids = set()
if "tts_audio" not in st.session_state:
    st.session_state.tts_audio = None
if "transcribed_text" not in st.session_state:
    st.session_state.transcribed_text = ""
if "result" not in st.session_state:
    st.session_state.result = None
if "active_persona_id" not in st.session_state:
    st.session_state.active_persona_id = None
if "active_persona" not in st.session_state:
    st.session_state.active_persona = None

# --- CSS ---
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

    .stApp {
        background: linear-gradient(160deg, #0a0a0f 0%, #121218 40%, #0e0e14 100%);
    }

    .app-header {
        text-align: center;
        padding: 2rem 0 1rem;
    }
    .app-header h1 {
        font-family: 'Cormorant Garamond', serif;
        font-weight: 600;
        font-size: 2.4rem;
        letter-spacing: 3px;
        background: linear-gradient(135deg, #c9a84c 0%, #f0d78c 50%, #c9a84c 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    .app-header p {
        font-family: 'Inter', sans-serif;
        font-weight: 300;
        font-size: 0.85rem;
        letter-spacing: 4px;
        text-transform: uppercase;
        color: #6b6b7b;
    }

    .section-label {
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        font-size: 0.7rem;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: #c9a84c;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #1e1e2a;
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #13131b !important;
        color: #e0e0e0 !important;
        border: 1px solid #252535 !important;
        border-radius: 6px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.9rem !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #c9a84c !important;
        box-shadow: 0 0 0 1px rgba(201, 168, 76, 0.2) !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #c9a84c 0%, #a8893e 100%);
        color: #0a0a0f;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.75rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        border: none;
        border-radius: 4px;
        padding: 0.8rem 2rem;
        width: 100%;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #d4b358 0%, #c9a84c 100%);
        box-shadow: 0 4px 20px rgba(201, 168, 76, 0.25);
    }

    .question-card {
        background: linear-gradient(145deg, #16161f 0%, #13131b 100%);
        border: 1px solid #252535;
        border-left: 3px solid #c9a84c;
        border-radius: 6px;
        padding: 1.25rem 1.5rem;
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.3rem;
        font-weight: 500;
        line-height: 1.6;
        color: #e8e8ec;
        margin-bottom: 1rem;
    }
    .question-meta {
        font-family: 'Inter', sans-serif;
        font-size: 0.65rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #4a4a5a;
        margin-top: 0.75rem;
    }

    .answer-card {
        background: linear-gradient(145deg, #16161f 0%, #13131b 100%);
        border: 1px solid #252535;
        border-left: 3px solid #c9a84c;
        border-radius: 6px;
        padding: 1.5rem 2rem;
        font-family: 'Inter', sans-serif;
        font-size: 1.05rem;
        line-height: 1.9;
        color: #e8e8ec;
        letter-spacing: 0.2px;
    }

    section[data-testid="stSidebar"] {
        background-color: #0c0c12;
        border-right: 1px solid #1a1a24;
    }
    section[data-testid="stSidebar"] .stRadio > label,
    section[data-testid="stSidebar"] .stSelectbox > label {
        font-family: 'Inter', sans-serif;
        font-weight: 400;
        font-size: 0.8rem;
        color: #8888a0;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 1px solid #1e1e2a;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        font-size: 0.75rem;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #6b6b7b;
        padding: 0.6rem 1.5rem;
        border-bottom: 2px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #c9a84c !important;
        border-bottom: 2px solid #c9a84c !important;
    }

    .stStatus {
        background-color: #13131b !important;
        border: 1px solid #252535 !important;
    }

    #MainMenu, footer {visibility: hidden;}
    /* Keep the header visible — it contains the sidebar toggle arrow.
       Only hide the Streamlit "Deploy" button inside it. */
    [data-testid="stToolbar"] {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)

# --- Header ---
st.markdown(
    """
<div class="app-header">
    <h1>Pageant AI Coach</h1>
    <p>Refine &middot; Rehearse &middot; Reign</p>
</div>
""",
    unsafe_allow_html=True,
)


# --- Seed evidence store once per server session ---
@st.cache_resource(show_spinner=False)
def _seed_evidence_store() -> int:
    """Seed the Chroma evidence store with Kenya/Africa corpus on first run.

    Wrapped in cache_resource so it executes only once per Streamlit server
    session, not on every page rerun.

    Returns:
        Number of chunks in the collection after seeding.
    """
    try:
        from pageant_assistant.rag.seed import seed_if_empty

        n = seed_if_empty()
        logger.info("Evidence store ready — %d chunk(s)", n)
        return n
    except Exception as exc:
        logger.warning("Evidence store seeding failed: %s", exc)
        return 0


_seed_evidence_store()

# --- Check API key ---
if not GROQ_API_KEY:
    st.error(
        "No Groq API key found. Add `GROQ_API_KEY=your_key` to your `.env` file "
        "in the PAGEANT_ASSISTANT directory and restart the app."
    )
    st.stop()

# --- Sidebar ---
filters = get_filter_options()

with st.sidebar:
    # --- Profile picker ---
    st.markdown(
        '<div class="section-label">My Profile</div>',
        unsafe_allow_html=True,
    )

    profiles = list_personas()
    persona_map: dict = {None: "(No profile selected)"}
    persona_map.update({p["id"]: f"{p['name']} ({p['country']})" for p in profiles})
    persona_ids = list(persona_map.keys())

    current_idx = 0
    if st.session_state.active_persona_id in persona_ids:
        current_idx = persona_ids.index(st.session_state.active_persona_id)

    selected_persona_id = st.selectbox(
        "Active profile",
        options=persona_ids,
        index=current_idx,
        format_func=lambda pid: persona_map.get(pid, "(Unknown)"),
        key="persona_selector",
        label_visibility="collapsed",
    )
    if selected_persona_id != st.session_state.active_persona_id:
        st.session_state.active_persona_id = selected_persona_id
        if selected_persona_id:
            st.session_state.active_persona = load_persona(selected_persona_id)
        else:
            st.session_state.active_persona = None
        st.session_state.result = None

    st.page_link("pages/1_My_Profile.py", label="Edit My Profile", use_container_width=True)

    if not profiles:
        st.caption("Head over to **My Profile** to set up your contestant profile.")

    st.divider()
    st.markdown('<div class="section-label">Configuration</div>', unsafe_allow_html=True)

    time_limit = st.radio(
        "Time limit",
        options=VALID_TIME_LIMITS,
        index=VALID_TIME_LIMITS.index(DEFAULT_TIME_LIMIT),
        format_func=lambda x: f"{x}s",
        horizontal=True,
    )

    style_preset = st.selectbox(
        "Speaking style",
        options=list(STYLE_PRESETS.keys()),
        index=list(STYLE_PRESETS.keys()).index(DEFAULT_STYLE),
        format_func=lambda x: STYLE_PRESETS[x],
    )

    st.divider()
    st.markdown('<div class="section-label">Question Filters</div>', unsafe_allow_html=True)

    filter_pageant = st.selectbox(
        "Pageant",
        options=[k for k, _ in filters["pageant_type"]],
        format_func=lambda x: dict(filters["pageant_type"])[x],
    )
    filter_type = st.selectbox(
        "Question type",
        options=[k for k, _ in filters["question_type"]],
        format_func=lambda x: dict(filters["question_type"])[x],
    )
    filter_difficulty = st.selectbox(
        "Difficulty",
        options=[k for k, _ in filters["difficulty"]],
        format_func=lambda x: dict(filters["difficulty"])[x],
    )

    st.divider()
    word_budget = int(time_limit * WORDS_PER_SECOND)
    st.markdown(
        f"<div style='font-family: Inter, sans-serif; font-size: 0.75rem; "
        f"color: #6b6b7b; line-height: 1.8;'>"
        f"Target: ~{word_budget} words / {time_limit}s<br>"
        f"Pipeline: Analyze &rarr; Research &rarr; Draft &rarr; Critique &rarr; Rewrite &rarr; Verify &rarr; Report"
        f"</div>",
        unsafe_allow_html=True,
    )

# --- Main layout ---
col_input, col_spacer, col_output = st.columns([1, 0.05, 1.2])

with col_input:
    st.markdown('<div class="section-label">Your Stage</div>', unsafe_allow_html=True)

    # --- Draw a question ---
    if st.button("Draw a Question"):
        q = get_random_question(
            pageant_type=filter_pageant,
            question_type=filter_type,
            difficulty=filter_difficulty,
            exclude_ids=st.session_state.shown_question_ids,
        )
        st.session_state.current_question = q
        st.session_state.shown_question_ids.add(q["id"])
        # Clear previous results
        st.session_state.tts_audio = None
        st.session_state.transcribed_text = ""
        st.session_state.audio_transcribed = False
        st.session_state.result = None

    # --- Display current question ---
    if st.session_state.current_question:
        q = st.session_state.current_question
        st.markdown(
            f'<div class="question-card">'
            f'"{q["text"]}"'
            f'<div class="question-meta">'
            f"{q['pageant_type'].replace('_', ' ').title()} &middot; "
            f"{q['question_type'].replace('_', ' ').title()} &middot; "
            f"{q['difficulty'].title()}"
            f"</div></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='text-align: center; padding: 1.5rem; color: #3a3a4a; "
            "font-family: Inter, sans-serif; font-size: 0.85rem;'>"
            "Click <strong style='color: #6b6b7b;'>Draw a Question</strong> to begin."
            "</div>",
            unsafe_allow_html=True,
        )

    st.write("")

    # --- Answer input: Type or Speak ---
    answer_mode = st.radio(
        "Answer mode",
        options=["Type", "Speak"],
        horizontal=True,
        label_visibility="collapsed",
    )

    raw_answer = ""

    if answer_mode == "Type":
        raw_answer = st.text_area(
            "Your Draft Answer",
            height=180,
            placeholder="Type your draft answer here...",
            label_visibility="collapsed",
        )
    else:
        audio_input = st.audio_input("Speak your answer")
        if audio_input and not st.session_state.get("audio_transcribed"):
            with st.spinner("Transcribing..."):
                # Pass audio_input.name so Groq receives the correct file extension
                # (browsers record WebM, not WAV — the extension drives format parsing)
                st.session_state.transcribed_text = transcribe_audio(
                    audio_input.getvalue(),
                    filename=audio_input.name,
                )
                st.session_state.audio_transcribed = True
        if st.session_state.transcribed_text:
            raw_answer = st.text_area(
                "Edit transcript",
                value=st.session_state.transcribed_text,
                height=180,
                label_visibility="collapsed",
                help="Review and edit your transcript before submitting.",
            )

    st.write("")
    run_btn = st.button("Polish My Answer")

with col_output:
    st.markdown('<div class="section-label">Coaching Feedback</div>', unsafe_allow_html=True)

    # --- Run pipeline ---
    if run_btn:
        if not st.session_state.current_question:
            st.warning("Draw a question first.")
        elif not raw_answer.strip():
            st.warning("Please provide your answer — type it or speak it.")
        else:
            _NODE_LABELS = {
                "question_understanding": "Analyzing the question...",
                "rag_research": "Retrieving evidence...",
                "drafting": "Drafting your answer...",
                "critic": "Scoring against rubric...",
                "rewrite": "Polishing the answer...",
                "claim_verifier": "Verifying factual claims...",
                "coach_report": "Writing coach report...",
                "generate_exemplar": "Creating winning example...",
            }

            with st.status("The judges are deliberating...", expanded=True) as status:
                try:
                    graph = build_refiner_graph()

                    persona_ctx = ""
                    if st.session_state.active_persona:
                        persona_ctx = format_persona_context(st.session_state.active_persona)

                    input_state = {
                        "question": st.session_state.current_question["text"],
                        "raw_answer": raw_answer,
                        "time_limit": time_limit,
                        "style_preset": style_preset,
                        "question_id": st.session_state.current_question["id"],
                        "input_mode": answer_mode.lower(),
                        "iteration_count": 0,
                        "persona_id": st.session_state.active_persona_id or "",
                        "persona_context": persona_ctx,
                    }

                    # Stream node-by-node for live progress updates
                    accumulated = dict(input_state)
                    for chunk in graph.stream(input_state):
                        for node_name, node_output in chunk.items():
                            accumulated.update(node_output)
                            label = _NODE_LABELS.get(node_name)
                            if label:
                                status.write(label)

                    st.session_state.result = accumulated
                    status.update(label="Coaching complete", state="complete", expanded=False)

                except requests.HTTPError as e:
                    code = e.response.status_code if e.response is not None else 0
                    if code == 401:
                        status.update(label="Authentication failed", state="error")
                        st.error("Authentication failed. Check your GROQ_API_KEY.")
                    elif code == 429:
                        status.update(label="Rate limited", state="error")
                        st.error("Groq rate limit reached. Wait a moment and try again.")
                    else:
                        status.update(label="API error", state="error")
                        st.error(f"Groq API error ({code}): {e}")
                except (requests.ConnectionError, ConnectionError):
                    status.update(label="Connection failed", state="error")
                    st.error("Could not connect to Groq. Check your internet connection.")
                except requests.Timeout:
                    status.update(label="Request timed out", state="error")
                    st.error("Groq request timed out. Try again.")
                except Exception as e:
                    status.update(label="An error occurred", state="error")
                    st.error(f"Error: {e}")

    # --- Display results (outside st.status so they're always visible) ---
    if st.session_state.result:
        result = st.session_state.result

        tab_answer, tab_exemplar, tab_report = st.tabs(
            ["On-Stage Answer", "Winning Example", "Coach Report"]
        )

        with tab_answer:
            st.markdown(
                f'<div class="answer-card">{result.get("refined_answer", "")}</div>',
                unsafe_allow_html=True,
            )

            # --- TTS playback ---
            if not st.session_state.tts_audio:
                st.write("")
                with st.spinner("Preparing audio..."):
                    st.session_state.tts_audio = synthesize_speech(result.get("refined_answer", ""))

            if st.session_state.tts_audio:
                st.markdown(
                    "<div style='font-family: Inter, sans-serif; font-size: 0.7rem; "
                    "letter-spacing: 2px; text-transform: uppercase; color: #6b6b7b; "
                    "margin-bottom: 0.5rem;'>Listen to your answer</div>",
                    unsafe_allow_html=True,
                )
                st.audio(st.session_state.tts_audio, format="audio/wav")
                st.download_button(
                    "Download Audio",
                    data=st.session_state.tts_audio,
                    file_name="refined_answer.wav",
                    mime="audio/wav",
                )

        with tab_exemplar:
            st.markdown(
                "<div style='font-family: Inter, sans-serif; font-size: 0.7rem; "
                "letter-spacing: 2px; text-transform: uppercase; color: #6b6b7b; "
                "margin-bottom: 0.75rem;'>Reference answer &mdash; not your voice, "
                "but a model to study</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="answer-card">{result.get("exemplar_answer", "")}</div>',
                unsafe_allow_html=True,
            )

        with tab_report:
            # --- Structured rubric scores (M3) ---
            critic_scores = result.get("critic_scores")
            if critic_scores and critic_scores.get("dimension_scores"):
                overall = critic_scores.get("overall_score", 0)
                st.markdown(
                    f"<div style='font-family: Cormorant Garamond, serif; "
                    f"font-size: 2rem; font-weight: 600; text-align: center; "
                    f"color: #c9a84c; margin-bottom: 0.5rem;'>"
                    f"{overall:.1f}<span style='font-size: 1rem; color: #6b6b7b;'> / 10</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                for dim in critic_scores["dimension_scores"]:
                    score = dim.get("score", 0)
                    pct = int(score * 10)
                    bar_color = "#c9a84c" if score >= 7 else "#6b6b7b" if score >= 5 else "#a04040"
                    st.markdown(
                        f"<div style='font-family: Inter, sans-serif; font-size: 0.8rem; "
                        f"color: #e0e0e0; margin-bottom: 0.15rem;'>"
                        f"<strong>{dim.get('name', '')}</strong> — "
                        f"<span style='color: {bar_color};'>{score:.1f}</span>"
                        f"<span style='color: #4a4a5a; margin-left: 0.5rem;'>{dim.get('reason', '')}</span>"
                        f"</div>"
                        f"<div style='background: #1e1e2a; border-radius: 3px; height: 4px; "
                        f"margin-bottom: 0.6rem;'>"
                        f"<div style='background: {bar_color}; width: {pct}%; height: 100%; "
                        f"border-radius: 3px;'></div></div>",
                        unsafe_allow_html=True,
                    )

                # Genericness / risk flags
                flags = critic_scores.get("genericness_flags", []) + critic_scores.get(
                    "risk_flags", []
                )
                if flags:
                    flag_text = ", ".join(f.replace("_", " ") for f in flags)
                    st.warning(f"Flags: {flag_text}")

                # Top fixes
                fixes = critic_scores.get("top_fixes", [])
                if fixes:
                    st.markdown(
                        '<div class="section-label" style="margin-top: 1rem;">Top Fixes</div>',
                        unsafe_allow_html=True,
                    )
                    for fix in fixes:
                        st.markdown(
                            f"- **{fix.get('target', '')}**: {fix.get('instruction', '')}",
                        )

                # Claim verification flags (M4)
                claim_flags = result.get("claim_flags") or []
                if claim_flags:
                    st.markdown(
                        '<div class="section-label" style="margin-top: 1rem;">'
                        "Fact-Check Warnings</div>",
                        unsafe_allow_html=True,
                    )
                    flags_md = "\n".join(f"- {flag}" for flag in claim_flags)
                    st.warning(
                        "These claims were not found in the retrieved evidence. "
                        "Verify before using on stage:\n\n" + flags_md
                    )

                st.divider()

            # --- Full coach report text ---
            st.markdown(result.get("coach_report", ""))

    elif st.session_state.current_question and not run_btn:
        st.markdown(
            "<div style='text-align: center; padding: 4rem 2rem; color: #3a3a4a; "
            "font-family: Inter, sans-serif; font-size: 0.85rem;'>"
            "Answer the question, then click<br>"
            "<strong style='color: #6b6b7b;'>Polish My Answer</strong>."
            "</div>",
            unsafe_allow_html=True,
        )
