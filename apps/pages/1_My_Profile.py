"""My Profile page — create and manage contestant profiles."""

import uuid

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from pageant_assistant.personas.manager import (
    list_personas,
    load_persona,
    save_persona,
    delete_persona,
)
from pageant_assistant.personas.models import Persona, PersonalStory
from pydantic import ValidationError

st.set_page_config(
    page_title="My Profile — Pageant AI Coach",
    page_icon="👑",
    layout="wide",
)

# --- CSS (shared theme) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

    .stApp {
        background: linear-gradient(160deg, #0a0a0f 0%, #121218 40%, #0e0e14 100%);
    }

    .page-header {
        text-align: center;
        padding: 1.5rem 0 1rem;
    }
    .page-header h1 {
        font-family: 'Cormorant Garamond', serif;
        font-weight: 600;
        font-size: 2rem;
        letter-spacing: 3px;
        background: linear-gradient(135deg, #c9a84c 0%, #f0d78c 50%, #c9a84c 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    .page-header p {
        font-family: 'Inter', sans-serif;
        font-weight: 300;
        font-size: 0.8rem;
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
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #d4b358 0%, #c9a84c 100%);
        box-shadow: 0 4px 20px rgba(201, 168, 76, 0.25);
    }

    .profile-card {
        background: linear-gradient(145deg, #16161f 0%, #13131b 100%);
        border: 1px solid #252535;
        border-left: 3px solid #c9a84c;
        border-radius: 6px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 0.75rem;
    }
    .profile-card h3 {
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.3rem;
        color: #e8e8ec;
        margin: 0 0 0.25rem;
    }
    .profile-card .meta {
        font-family: 'Inter', sans-serif;
        font-size: 0.7rem;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #6b6b7b;
    }

    section[data-testid="stSidebar"] {
        background-color: #0c0c12;
        border-right: 1px solid #1a1a24;
    }

    [data-testid="stSidebarNav"] ul {display: none;}
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Session state ---
if "editing_persona_id" not in st.session_state:
    st.session_state.editing_persona_id = None

# --- Header ---
st.markdown("""
<div class="page-header">
    <h1>My Profile</h1>
    <p>Tell us about yourself so your answers feel like you</p>
</div>
""", unsafe_allow_html=True)

# --- Layout ---
col_list, col_spacer, col_editor = st.columns([0.8, 0.05, 1.2])

with col_list:
    st.markdown(
        '<div class="section-label">My Profiles</div>',
        unsafe_allow_html=True,
    )

    profiles = list_personas()

    if st.button("Create New Profile", use_container_width=True):
        st.session_state.editing_persona_id = "__new__"
        st.rerun()

    st.write("")

    if not profiles:
        st.markdown(
            "<div style='text-align: center; padding: 2rem; color: #3a3a4a; "
            "font-family: Inter, sans-serif; font-size: 0.85rem;'>"
            "No profiles yet.<br>Create one to get personalized coaching."
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        for p in profiles:
            col_card, col_actions = st.columns([3, 1])
            with col_card:
                st.markdown(
                    f'<div class="profile-card">'
                    f'<h3>{p["name"]}</h3>'
                    f'<div class="meta">{p["country"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with col_actions:
                st.write("")
                if st.button("Edit", key=f"edit_{p['id']}", use_container_width=True):
                    st.session_state.editing_persona_id = p["id"]
                    st.rerun()
                if st.button("Delete", key=f"del_{p['id']}", use_container_width=True):
                    delete_persona(p["id"])
                    if st.session_state.editing_persona_id == p["id"]:
                        st.session_state.editing_persona_id = None
                    if st.session_state.get("active_persona_id") == p["id"]:
                        st.session_state.active_persona_id = None
                        st.session_state.active_persona = None
                    st.rerun()

with col_editor:
    st.markdown(
        '<div class="section-label">Edit Profile</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.editing_persona_id is None:
        st.markdown(
            "<div style='text-align: center; padding: 4rem 2rem; color: #3a3a4a; "
            "font-family: Inter, sans-serif; font-size: 0.85rem;'>"
            "Select a profile to edit, or create a new one."
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        is_new = st.session_state.editing_persona_id == "__new__"
        persona = None if is_new else load_persona(
            st.session_state.editing_persona_id,
        )

        if not is_new and persona is None:
            st.warning(
                "This profile could not be loaded (it may be corrupted). "
                "You can re-enter your information below to fix it."
            )

        p_name = st.text_input(
            "Your name", value=persona.name if persona else "",
        )
        p_country = st.text_input(
            "Country you represent", value=persona.country if persona else "",
        )
        p_platform = st.text_input(
            "Your platform / advocacy",
            value=persona.platform if persona else "",
            help="e.g. 'Mental health awareness for youth'",
        )
        p_values_str = st.text_input(
            "Your core values (comma-separated)",
            value=", ".join(persona.values) if persona else "",
            help="e.g. 'resilience, empathy, education'",
        )

        st.write("")
        st.markdown(
            '<div class="section-label">Your Stories</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "These are real experiences from your life that the coach will "
            "weave into your answers. The more specific, the better."
        )

        existing_stories = persona.personal_stories if persona else []
        story_count = st.number_input(
            "Number of stories",
            min_value=0,
            max_value=5,
            value=len(existing_stories),
        )

        stories: list[PersonalStory] = []
        story_errors: list[str] = []
        for i in range(int(story_count)):
            existing = existing_stories[i] if i < len(existing_stories) else None
            st.markdown(f"**Story {i + 1}**")
            s_title = st.text_input(
                "Title",
                value=existing.title if existing else "",
                key=f"story_title_{i}",
                placeholder="e.g. 'Teaching in Rural Zambia'",
            )
            s_text = st.text_area(
                "What happened?",
                value=existing.text if existing else "",
                key=f"story_text_{i}",
                height=100,
                placeholder="Describe the experience in 2-4 sentences.",
                help="At least 10 characters. Tell us what happened in enough detail to feel real.",
            )
            s_lesson = st.text_input(
                "What did you learn?",
                value=existing.key_lesson if existing else "",
                key=f"story_lesson_{i}",
                placeholder="The one takeaway from this experience.",
                help="At least 5 characters. What's the lesson you carry forward?",
            )
            if s_title and s_text and s_lesson:
                try:
                    stories.append(
                        PersonalStory(title=s_title, text=s_text, key_lesson=s_lesson),
                    )
                except ValidationError as e:
                    for err in e.errors():
                        field = err["loc"][-1] if err["loc"] else "field"
                        friendly = {
                            "title": "Story title",
                            "text": "Story description",
                            "key_lesson": "Key lesson",
                        }.get(field, field)
                        story_errors.append(f"Story {i + 1} — {friendly}: {err['msg']}")
            st.divider()

        if story_errors:
            for err_msg in story_errors:
                st.warning(err_msg)

        st.write("")
        col_save, col_cancel = st.columns([1, 1])

        with col_save:
            if st.button("Save Profile", use_container_width=True):
                if p_name and p_country and p_platform and p_values_str:
                    values = [
                        v.strip() for v in p_values_str.split(",") if v.strip()
                    ]
                    try:
                        new_persona = Persona(
                            id=persona.id if persona else uuid.uuid4().hex[:12],
                            name=p_name,
                            country=p_country,
                            platform=p_platform,
                            values=values,
                            personal_stories=stories,
                        )
                        saved = save_persona(new_persona)
                        st.session_state.editing_persona_id = saved.id
                        # Auto-select as active profile after saving
                        st.session_state.active_persona = saved
                        st.session_state.active_persona_id = saved.id
                        st.success(f"Saved! {saved.name} is now your active profile.")
                        st.rerun()
                    except ValidationError as e:
                        for err in e.errors():
                            field = err["loc"][-1] if err["loc"] else "field"
                            st.error(f"Could not save profile — {field}: {err['msg']}")
                else:
                    st.warning(
                        "Please fill in your name, country, platform, and values.",
                    )

        with col_cancel:
            if st.button("Cancel", use_container_width=True):
                st.session_state.editing_persona_id = None
                st.rerun()

    # --- Guided flow: go to coaching ---
    st.write("")
    st.write("")
    if st.session_state.get("active_persona_id"):
        active = st.session_state.get("active_persona")
        if active:
            st.markdown(
                f"<div style='font-family: Inter, sans-serif; font-size: 0.8rem; "
                f"color: #6b6b7b; text-align: center; margin-bottom: 0.5rem;'>"
                f"Active profile: <strong style='color: #c9a84c;'>{active.name}</strong>"
                f"</div>",
                unsafe_allow_html=True,
            )
        st.page_link(
            "streamlit_app.py",
            label="Start Coaching Session",
            use_container_width=True,
        )
    elif profiles:
        st.caption("Select or create a profile, then head to coaching.")
