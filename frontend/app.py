"""
VideoMind AI — Streamlit Frontend
===================================
Main application entry point is here
"""

import os
import time

from components.cards import render_chat_assistant, render_chat_user, render_search_result
from components.player import get_seek_script_html
from components.skeleton import (
    skeleton_chat_response,
    skeleton_results,
    skeleton_status,
    skeleton_video,
)
from components.status import render_pipeline_stepper
import requests
import streamlit as st
from theme import get_google_fonts_html, get_theme_css

# Configure page
st.set_page_config(
    page_title="VideoMind AI", page_icon="🎬", layout="wide", initial_sidebar_state="collapsed"
)

# Set API Base URL from environment or default to local development
API_BASE_URL = os.environ.get("API_URL", "http://localhost:8000/api/v1")
TIMEOUT = 300.0

# Initialize Session State
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"
if "video_id" not in st.session_state:
    st.session_state["video_id"] = None
if "video_path" not in st.session_state:
    st.session_state["video_path"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# --- Theme Injection ---
st.markdown(get_google_fonts_html(), unsafe_allow_html=True)
st.markdown(get_theme_css(st.session_state["theme"]), unsafe_allow_html=True)
st.components.v1.html(get_seek_script_html(), height=0, width=0)

# --- Header & Controls ---
col1, col2, col3, col4 = st.columns([8, 1, 1, 1])
with col1:
    st.markdown("### 🎬 VideoMind AI")

def set_theme(t) -> None:
    st.session_state["theme"] = t

with col2:
    if st.button("🌙", key="btn_dark", help="Dark Mode", use_container_width=True):
        set_theme("dark")
        st.rerun()
with col3:
    if st.button("☀️", key="btn_light", help="Light Mode", use_container_width=True):
        set_theme("light")
        st.rerun()
with col4:
    if st.button("🪟", key="btn_glass", help="Glass Mode", use_container_width=True):
        set_theme("glass")
        st.rerun()

st.markdown("---")

# --- Upload & Processing ---
if not st.session_state["video_id"]:
    # Center the upload area if no video is selected
    st.markdown("<div style='text-align: center; padding-top: 50px;'><div class='icon' style='font-size: 3rem;'>🎬</div><h3>Upload a video to start chatting</h3></div>", unsafe_allow_html=True)
    
    col_upload1, col_upload2, col_upload3 = st.columns([1, 2, 1])
    with col_upload2:
        uploaded_file = st.file_uploader(
            "Drag & drop your video here", type=["mp4", "mov", "avi"], label_visibility="collapsed"
        )

        if uploaded_file and st.button("Upload & Process", use_container_width=True):
            st.toast("⚙️ Processing started...", icon="⚙️")
            try:
                files = {"file": (uploaded_file.name, uploaded_file, "video/mp4")}
                res = requests.post(f"{API_BASE_URL}/videos/upload", files=files, timeout=TIMEOUT)
                res.raise_for_status()

                data = res.json()
                st.session_state["video_id"] = data["video_id"]
                # Save a local temp copy for the UI to play, since API serves from backend DATA_DIR
                os.makedirs("data", exist_ok=True)
                temp_path = os.path.join("data", f"ui_{uploaded_file.name}")
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                st.session_state["video_path"] = temp_path

                st.toast("✅ Video uploaded successfully", icon="✅")
                st.session_state["chat_history"] = []  # Reset chat
                st.rerun()
            except Exception:
                st.toast("❌ Upload failed — check file format or server connection", icon="❌")
                st.error("Failed to upload video to the backend.")

else:
    # Processing Status Tracker
    status_placeholder = st.empty()

    # PERFORMANCE: Avoid tight while True loops which block the Streamlit UI thread.
    # Instead, we check status once per render and use st.rerun() to schedule the next check.
    try:
        res = requests.get(
            f"{API_BASE_URL}/videos/{st.session_state['video_id']}/status", timeout=TIMEOUT
        )
        if res.status_code == 200:
            status_data = res.json()
            if status_data.get("status") not in ("completed", "failed"):
                status_placeholder.markdown(
                    render_pipeline_stepper(status_data.get("progress_message", "")),
                    unsafe_allow_html=True,
                )
                time.sleep(3)
                st.rerun()
            else:
                status_placeholder.empty()
    except Exception:
        status_placeholder.markdown(skeleton_status(), unsafe_allow_html=True)

    # --- Main Video Area ---
    if st.session_state["video_path"] and os.path.exists(st.session_state["video_path"]):
        st.markdown("<div class='vm-video-container'>", unsafe_allow_html=True)
        st.video(st.session_state["video_path"])
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(skeleton_video(), unsafe_allow_html=True)

    st.markdown("---")

    # Tabs
    tab_chat, tab_search, tab_summary = st.tabs(["💬 Chat", "🔍 Search", "📋 Summary"])

    with tab_chat:
        st.markdown("<div class='vm-chat-container'>", unsafe_allow_html=True)

        if not st.session_state["chat_history"]:
            st.markdown(
                "<div class='vm-empty-state'><div class='icon'>💬</div><p>Ask anything about your video</p></div>",
                unsafe_allow_html=True,
            )

        for msg in st.session_state["chat_history"]:
            if msg["role"] == "user":
                st.markdown(render_chat_user(msg["content"]), unsafe_allow_html=True)
            else:
                st.markdown(
                    render_chat_assistant(msg["content"], msg.get("sources")),
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)

        # Chat input at bottom
        user_query = st.chat_input("Ask a question about the video...")
        if user_query:
            # Add user message
            st.session_state["chat_history"].append({"role": "user", "content": user_query})
            st.rerun()

    # If the last message is from the user, fetch assistant response
    if (
        tab_chat
        and st.session_state["chat_history"]
        and st.session_state["chat_history"][-1]["role"] == "user"
    ):
        with tab_chat:
            loading_placeholder = st.empty()
            loading_placeholder.markdown(skeleton_chat_response(), unsafe_allow_html=True)

            try:
                payload = {
                    "question": st.session_state["chat_history"][-1]["content"],
                    "video_id": st.session_state["video_id"],
                }
                res = requests.post(f"{API_BASE_URL}/chat", json=payload, timeout=TIMEOUT)
                res.raise_for_status()
                data = res.json()

                loading_placeholder.empty()
                st.session_state["chat_history"].append(
                    {
                        "role": "assistant",
                        "content": data["answer"],
                        "sources": data.get("sources", []),
                    }
                )
                st.rerun()
            except requests.exceptions.Timeout:
                loading_placeholder.empty()
                st.error("The model took too long to respond. Please try again.")
                st.session_state["chat_history"].pop()  # Remove pending user message
            except Exception:
                loading_placeholder.empty()
                st.error(
                    "Failed to generate response. Please ensure Ollama and backend are running."
                )
                st.session_state["chat_history"].pop()

    with tab_search:
        search_query = st.text_input(
            "🔍 Search within video (e.g., 'Docker setup', 'Show me the whiteboard')",
            key="search_input",
        )
        if search_query:
            search_placeholder = st.empty()
            search_placeholder.markdown(skeleton_results(), unsafe_allow_html=True)

            try:
                payload = {
                    "query": search_query,
                    "video_id": st.session_state["video_id"],
                    "top_k": 5,
                }
                res = requests.post(f"{API_BASE_URL}/search", json=payload, timeout=TIMEOUT)
                res.raise_for_status()
                data = res.json()

                search_placeholder.empty()
                results = data.get("results", [])

                if not results:
                    st.markdown(
                        "<div class='vm-empty-state'><div class='icon'>🤷</div><p>No results found — try different keywords</p></div>",
                        unsafe_allow_html=True,
                    )
                else:
                    for r in results:
                        st.markdown(render_search_result(r), unsafe_allow_html=True)

            except Exception:
                search_placeholder.empty()
                st.error("Failed to fetch search results. Please ensure the backend is running.")

    with tab_summary:
        st.markdown(
            "<div class='vm-empty-state'><div class='icon'>📋</div><p>Video summarization coming soon</p></div>",
            unsafe_allow_html=True,
        )
