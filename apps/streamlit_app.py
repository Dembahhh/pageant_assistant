import streamlit as st
from dotenv import load_dotenv

# Load env before any pageant_assistant imports
load_dotenv()

from pageant_assistant.graphs.refiner import build_refiner_graph
from pageant_assistant.questions.bank import get_random_question, get_filter_options
from pageant_assistant.voice.audio import transcribe_audio, synthesize_speech
from pageant_assistant.config.settings import (
    GROQ_API_KEY,
    STYLE_PRESETS,
    DEFAULT_STYLE,
    VALID_TIME_LIMITS,
    DEFAULT_TIME_LIMIT,
    WORDS_PER_SECOND,
)

st.set_page_config(
    page_title="Pageant AI Coach",
    page_icon="👑",
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

# --- CSS ---
st.markdown("""
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

    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="app-header">
    <h1>Pageant AI Coach</h1>
    <p>Refine &middot; Rehearse &middot; Reign</p>
</div>
""", unsafe_allow_html=True)

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
        f"Pipeline: Analyze &rarr; Draft &rarr; Critique &rarr; Rewrite &rarr; Exemplar"
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
        st.session_state.result = None

    # --- Display current question ---
    if st.session_state.current_question:
        q = st.session_state.current_question
        st.markdown(
            f'<div class="question-card">'
            f'"{q["text"]}"'
            f'<div class="question-meta">'
            f'{q["pageant_type"].replace("_", " ").title()} &middot; '
            f'{q["question_type"].replace("_", " ").title()} &middot; '
            f'{q["difficulty"].title()}'
            f'</div></div>',
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
        if audio_input:
            with st.spinner("Transcribing..."):
                st.session_state.transcribed_text = transcribe_audio(
                    audio_input.getvalue()
                )
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
    st.markdown(
        '<div class="section-label">Coaching Feedback</div>', unsafe_allow_html=True
    )

    # --- Run pipeline ---
    if run_btn:
        if not st.session_state.current_question:
            st.warning("Draw a question first.")
        elif not raw_answer.strip():
            st.warning("Please provide your answer — type it or speak it.")
        else:
            with st.status("The judges are deliberating...", expanded=True) as status:
                try:
                    status.write("Analyzing the question...")
                    graph = build_refiner_graph()

                    result = graph.invoke({
                        "question": st.session_state.current_question["text"],
                        "raw_answer": raw_answer,
                        "time_limit": time_limit,
                        "style_preset": style_preset,
                        "question_id": st.session_state.current_question["id"],
                        "input_mode": answer_mode.lower(),
                        "iteration_count": 0,
                    })

                    st.session_state.result = result
                    status.update(
                        label="Coaching complete", state="complete", expanded=False
                    )

                except Exception as e:
                    status.update(label="An error occurred", state="error")
                    error_msg = str(e)
                    if "api_key" in error_msg.lower() or "auth" in error_msg.lower():
                        st.error("Authentication failed. Check your GROQ_API_KEY in .env.")
                    else:
                        st.error(f"Error: {error_msg}")

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
                    st.session_state.tts_audio = synthesize_speech(
                        result.get("refined_answer", "")
                    )

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
