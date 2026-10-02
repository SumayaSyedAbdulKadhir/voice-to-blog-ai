"""Voice-to-Blog AI: Streamlit front end.

This file only handles the user interface and session state.
Speech-to-text, prompts, LLM calls and helpers live in src/.
"""

import hashlib

import streamlit as st

from src import blog_generator as bg
from src import utils
from src.prompts import AUDIENCES, LENGTHS, PLATFORMS, TONES
from src.speech_to_text import TranscriptionError, get_model_settings, transcribe_audio

st.set_page_config(page_title="Voice-to-Blog AI", page_icon="🎙️", layout="centered")

# ---------------------------------------------------------------- state

DEFAULTS = {
    "nonce": 0,                    # bumped on "Start new" to reset audio widgets
    "transcript": "",              # original transcript from Whisper
    "transcript_text": "",         # editable transcript (bound to a text_area)
    "transcribed_hash": None,      # hash of the audio we already transcribed
    "transcript_confirmed": False,
    "final_transcript": "",        # transcript the user approved
    "blog_text": "",               # editable blog (bound to a text_area)
    "title_options": [],
    "tone": TONES[0],
    "length": LENGTHS[1],
    "audience": AUDIENCES[0],
    "platform": PLATFORMS[0],
    "new_tone": TONES[0],
}


def init_state() -> None:
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)


def reset_all() -> None:
    """Clear everything and return to the initial screen (used as a button callback)."""
    nonce = st.session_state.get("nonce", 0) + 1
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state["nonce"] = nonce  # new widget keys => audio widgets are emptied


def run_action(spinner_text: str, func, *args) -> None:
    """Run an LLM action and store the result as the current blog text.

    Must be called BEFORE the blog text_area is drawn in the same script run,
    because Streamlit forbids changing a widget's state after it is created.
    """
    try:
        with st.spinner(spinner_text):
            result = func(*args)
        st.session_state.blog_text = result
        st.session_state.title_options = []
    except bg.BlogGenerationError as err:
        st.error(str(err))


def generate_from_settings() -> None:
    s = st.session_state
    run_action(
        "Turning your ideas into a blog...",
        bg.generate_blog,
        s.final_transcript, s.tone, s.length, s.audience, s.platform,
    )


# ------------------------------------------------------------ UI pieces


def render_sidebar() -> None:
    with st.sidebar:
        st.header("About")
        st.write(
            "Speech is transcribed **on your computer**. Only the transcript text "
            "is sent to Google's Gemini API to write the blog."
        )
        st.caption(
            "Free-tier note: Google may use free-tier prompts to improve its "
            "products, so avoid confidential content."
        )
        whisper = get_model_settings()
        st.caption(f"Whisper model: `{whisper['model_size']}` on `{whisper['device']}`")
        st.caption(f"LLM: `{bg.get_model()}`")
        if bg.is_api_key_configured():
            st.success("Gemini API key found")
        else:
            st.error("GEMINI_API_KEY missing. Add it to .env and restart.")


def render_header() -> None:
    st.title("🎙️ Voice-to-Blog AI")
    st.markdown("**Turn your spoken ideas into polished blog posts.**")
    st.caption("Speak your ideas. Let AI turn them into polished blogs.")


def render_audio_section() -> None:
    st.subheader("1. Add your audio")
    nonce = st.session_state.nonce
    tab_record, tab_upload = st.tabs(["Record", "Upload"])

    with tab_record:
        if hasattr(st, "audio_input"):
            recorded = st.audio_input("Record a voice note", key=f"rec_{nonce}")
        else:
            recorded = None
            st.warning("Recording needs Streamlit 1.39+. Upgrade, or use Upload.")

    with tab_upload:
        extensions = [e.lstrip(".") for e in utils.SUPPORTED_AUDIO_EXTENSIONS]
        uploaded = st.file_uploader(
            "Upload an audio file", type=extensions, key=f"up_{nonce}"
        )
        st.caption(
            "Supported: " + ", ".join(e.upper() for e in extensions)
            + f". Max {utils.MAX_AUDIO_MB} MB / {utils.MAX_AUDIO_MINUTES} minutes."
        )

    audio = uploaded if uploaded is not None else recorded

    if audio is None:
        st.info("Record or upload audio to begin.")
        render_paste_fallback()
        return

    data = audio.getvalue()
    name = getattr(audio, "name", "") or "recording.wav"
    st.audio(data, format=getattr(audio, "type", None) or "audio/wav")

    duration = utils.get_audio_duration_seconds(data)
    details = f"**{name}**, {len(data) / 1_048_576:.1f} MB"
    if duration is not None:
        details += f", {utils.format_duration(duration)}"
    st.caption(details)

    if st.button("🎧 Convert Speech to Text", type="primary"):
        audio_hash = hashlib.sha256(data).hexdigest()
        ok, message = utils.validate_audio(name, len(data), duration)
        if not ok:
            st.error(message)
        elif audio_hash == st.session_state.transcribed_hash and st.session_state.transcript:
            st.info("This audio is already transcribed. Edit the transcript below.")
        else:
            try:
                with st.spinner(
                    "Transcribing locally... the first run downloads the Whisper "
                    "model, which can take a few minutes."
                ):
                    text = transcribe_audio(data)
                st.session_state.transcript = text
                st.session_state.transcript_text = text
                st.session_state.transcribed_hash = audio_hash
                st.session_state.transcript_confirmed = False
                st.session_state.blog_text = ""
            except TranscriptionError as err:
                st.error(str(err))

    render_paste_fallback()


def render_paste_fallback() -> None:
    """Lets you test the blog generator without audio."""
    with st.expander("No audio? Paste a transcript instead"):
        pasted = st.text_area("Paste text", key=f"paste_{st.session_state.nonce}", height=120)
        if st.button("Use pasted text"):
            ok, message = utils.validate_transcript(pasted)
            if ok:
                st.session_state.transcript = pasted.strip()
                st.session_state.transcript_text = pasted.strip()
                st.session_state.transcribed_hash = None
                st.session_state.transcript_confirmed = False
                st.rerun()
            else:
                st.warning(message)


def render_transcript_section() -> None:
    st.subheader("2. Review your transcript")
    st.text_area(
        "Your Transcript",
        key="transcript_text",
        height=220,
        help="Fix names, technical terms and missing words before generating.",
    )
    if st.button("Use This Transcript", type="primary"):
        ok, message = utils.validate_transcript(st.session_state.transcript_text)
        if ok:
            st.session_state.final_transcript = st.session_state.transcript_text.strip()
            st.session_state.transcript_confirmed = True
        else:
            st.session_state.transcript_confirmed = False
            st.warning(message)
    if st.session_state.transcript_confirmed:
        st.caption("✓ Transcript locked in. Click the button again if you edit it.")


def render_settings_section() -> None:
    st.subheader("3. Blog settings")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        col1.selectbox("Tone", TONES, key="tone")
        col2.selectbox("Length", LENGTHS, key="length")
        col3, col4 = st.columns(2)
        col3.selectbox("Audience", AUDIENCES, key="audience")
        col4.selectbox("Platform", PLATFORMS, key="platform")
        if st.button("✨ Generate Blog", type="primary"):
            generate_from_settings()


def render_blog_section() -> None:
    st.subheader("4. Edit your blog")
    s = st.session_state

    # Toolbar sits ABOVE the editor so it can update blog_text safely.
    row1 = st.columns(4)
    if row1[0].button("Generate again"):
        generate_from_settings()
    if row1[1].button("Improve writing"):
        run_action("Polishing the writing...", bg.improve_blog, s.blog_text)
    if row1[2].button("Make shorter"):
        run_action("Shortening...", bg.shorten_blog, s.blog_text)
    if row1[3].button("Make more detailed"):
        run_action("Expanding...", bg.expand_blog, s.blog_text, s.final_transcript)

    row2 = st.columns([2, 1, 1])
    row2[0].selectbox("New tone", TONES, key="new_tone", label_visibility="collapsed")
    if row2[1].button("Change tone"):
        run_action("Rewriting in the new tone...", bg.change_tone, s.blog_text, s.new_tone)
    if row2[2].button("New titles"):
        try:
            with st.spinner("Brainstorming titles..."):
                s.title_options = bg.generate_titles(s.blog_text)
        except bg.BlogGenerationError as err:
            st.error(str(err))

    if s.title_options:
        choice = st.radio("Pick a title", s.title_options)
        if st.button("Apply title"):
            s.blog_text = utils.apply_title(s.blog_text, choice)
            s.title_options = []

    st.text_area("Generated Blog", key="blog_text", height=520)
    st.caption(f"{utils.count_words(s.blog_text)} words")


def render_export_section() -> None:
    st.subheader("5. Export")
    blog = st.session_state.blog_text
    if not blog.strip():
        st.warning("The blog is empty, so there is nothing to export.")
        return

    col_md, col_txt = st.columns(2)
    md_data, md_name, md_mime = utils.build_download(blog, "md")
    txt_data, txt_name, txt_mime = utils.build_download(blog, "txt")
    col_md.download_button("⬇️ Download Markdown", md_data, md_name, md_mime)
    col_txt.download_button("⬇️ Download TXT", txt_data, txt_name, txt_mime)

    with st.expander("Copy to clipboard"):
        st.caption("Hover over the box and click the copy icon in its top-right corner.")
        st.code(blog, language="markdown")

    st.button("🆕 Start New Blog", on_click=reset_all)


def main() -> None:
    init_state()
    render_sidebar()
    render_header()
    render_audio_section()
    if st.session_state.transcript:
        render_transcript_section()
    if st.session_state.transcript_confirmed:
        render_settings_section()
    if st.session_state.blog_text:
        render_blog_section()
        render_export_section()


main()
