import os
import requests
import streamlit as st
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass


st.set_page_config(page_title="LinkedIn Post Generator", page_icon="💼", layout="centered")
st.title("LinkedIn Post Generator")
st.caption("Type a topic, generate a concise LinkedIn-style post.")


default_api = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
with st.sidebar:
    st.header("Settings")
    api_base = st.text_input("API base URL", value=default_api).rstrip("/")
    style = st.text_input("Optional style (e.g., bold, storytelling)", value="")


with st.form("post_form", clear_on_submit=False):
    topic = st.text_area("What do you want to post about?", height=150, placeholder="e.g., AI in GIS, lessons from a hackathon, leadership learnings")
    submitted = st.form_submit_button("Generate Post")


def call_backend_generate(base_url: str, topic_text: str, style_text: str):
    try:
        resp = requests.post(
            f"{base_url}/generate",
            json={"topic": topic_text, "style": style_text or None},
            timeout=45,
        )
        try:
            resp.raise_for_status()
        except requests.HTTPError:
            # Show backend error details to user for debugging
            content = None
            try:
                content = resp.json()
            except Exception:
                content = resp.text
            return False, content
        return True, resp.json().get("post", "")
    except Exception as exc:
        return False, str(exc)


st.divider()
if submitted:
    clean_topic = (topic or "").strip()
    if not clean_topic:
        st.error("Please enter a topic before generating.")
    else:
        with st.spinner("Generating..."):
            ok, result = call_backend_generate(api_base, clean_topic, style)
        if ok:
            st.success("Generated Post")
            st.write("")
            st.markdown(result)
            st.write("")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Copy to clipboard"):
                    st.session_state.generated_post = result
                    st.toast("Copy from below text box.")
            with c2:
                st.caption("Tip: tweak the style and regenerate.")
            st.text_area("Output (you can copy)", value=result, height=220)
        else:
            st.error("Generation failed.")
            st.code(result)

st.divider()
st.caption("Backend expects `GROQ_API_KEY` env var and exposes `/generate`.")


