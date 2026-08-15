"""
SAGE - Streamlit chat UI with PDF upload.

Pure-Python web UI that talks to the FastAPI backend.
Run with:
    streamlit run frontend/app.py

The backend must be running first at http://localhost:8000.

Owner: Minhazul (Frontend) - scaffolded by Abrar
"""

import os
import uuid

import requests
import streamlit as st

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------

API_URL = os.getenv("SAGE_API_URL", "http://localhost:8000/api/v1")

# ----------------------------------------------------------------------
# PAGE SETUP
# ----------------------------------------------------------------------

st.set_page_config(
    page_title="SAGE - Student Academic Guidance Engine",
    page_icon="🎓",
    layout="centered",
)

st.title("🎓 SAGE")
st.caption("Student Academic Guidance Engine — your AI study assistant")


# ----------------------------------------------------------------------
# SESSION STATE
# ----------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "active_collection" not in st.session_state:
    st.session_state.active_collection = None
if "active_doc_name" not in st.session_state:
    st.session_state.active_doc_name = None
if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = None
if "access_token" not in st.session_state:
    st.session_state.access_token = None


if not st.session_state.access_token:
    st.subheader("Sign in to continue")
    login_tab, signup_tab = st.tabs(["Sign in", "Create account"])
    with login_tab:
        with st.form("login"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign in"):
                response = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password}, timeout=15)
                if response.ok:
                    data = response.json()
                    st.session_state.access_token = data["access_token"]
                    st.session_state.user = data["user"]
                    st.rerun()
                else:
                    st.error(response.json().get("detail", "Sign in failed."))
    with signup_tab:
        with st.form("signup"):
            name = st.text_input("Full name")
            signup_email = st.text_input("Email", key="signup_email")
            signup_password = st.text_input("Password (at least 8 characters)", type="password", key="signup_password")
            if st.form_submit_button("Create account"):
                response = requests.post(f"{API_URL}/auth/signup", json={"name": name, "email": signup_email, "password": signup_password}, timeout=15)
                if response.ok:
                    data = response.json()
                    st.session_state.access_token = data["access_token"]
                    st.session_state.user = data["user"]
                    st.rerun()
                else:
                    st.error(response.json().get("detail", "Signup failed."))
    st.stop()

AUTH_HEADERS = {"Authorization": f"Bearer {st.session_state.access_token}"}


# ----------------------------------------------------------------------
# SIDEBAR — upload + connection info
# ----------------------------------------------------------------------

with st.sidebar:
    st.header("📚 Your Document")

    uploaded = st.file_uploader(
        "Upload a PDF to chat with",
        type=["pdf"],
        help="Drop a lecture PDF, paper, or notes file here.",
    )

    if uploaded is not None and uploaded.name != st.session_state.uploaded_filename:
        # New file detected — upload it
        with st.spinner(f"Ingesting {uploaded.name}... (may take a minute)"):
            try:
                response = requests.post(
                    f"{API_URL}/documents/upload",
                    headers=AUTH_HEADERS,
                    files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
                    timeout=300,  # ingestion can take time for big PDFs
                )
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.active_collection = data["collection_name"]
                    st.session_state.active_doc_name = data["filename"]
                    st.session_state.uploaded_filename = uploaded.name
                    st.success(f"✓ Indexed {data['chunk_count']} chunks from {data['filename']}")
                    st.rerun()
                else:
                    st.error(f"Upload failed ({response.status_code}): {response.text[:300]}")
            except Exception as exc:
                st.error(f"Upload error: {type(exc).__name__}: {exc}")

    if st.session_state.active_collection:
        st.success(f"📄 Active: **{st.session_state.active_doc_name}**")
        if st.button("Forget current document"):
            st.session_state.active_collection = None
            st.session_state.active_doc_name = None
            st.session_state.uploaded_filename = None
            st.rerun()
    else:
        st.info("No document loaded. Upload a PDF above to ground SAGE in your materials.")

    st.divider()
    st.subheader("Session Info")
    st.text_input("Signed in as", value=st.session_state.user["email"], disabled=True)
    st.text_input("Session ID", value=st.session_state.session_id, disabled=True)

    st.divider()
    st.subheader("Backend")
    st.code(API_URL, language=None)
    try:
        r = requests.get(API_URL.replace("/api/v1", "/"), timeout=2)
        if r.status_code == 200:
            st.success("✓ Backend is healthy")
        else:
            st.error(f"Backend returned {r.status_code}")
    except Exception:
        st.error("✗ Backend not reachable")

    st.divider()
    if st.button("Clear chat (local view only)"):
        st.session_state.messages = []
        st.rerun()
    if st.button("Sign out"):
        st.session_state.clear()
        st.rerun()


# ----------------------------------------------------------------------
# CHAT HISTORY DISPLAY
# ----------------------------------------------------------------------

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("tools"):
            st.caption(f"🔧 Tools used: {', '.join(msg['tools'])}")


# ----------------------------------------------------------------------
# CHAT INPUT
# ----------------------------------------------------------------------

user_input = st.chat_input("Ask SAGE anything about your studies...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input, "tools": []})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("SAGE is thinking..."):
            try:
                response = requests.post(
                    f"{API_URL}/chat",
                    headers=AUTH_HEADERS,
                    json={
                        "session_id": st.session_state.session_id,
                        "message": user_input,
                        "collection_name": st.session_state.active_collection,
                    },
                    timeout=120,
                )

                if response.status_code == 200:
                    data = response.json()
                    reply = data["reply"]
                    tools = data.get("tools_used", [])

                    st.markdown(reply)
                    if tools:
                        st.caption(f"🔧 Tools used: {', '.join(tools)}")

                    st.session_state.messages.append(
                        {"role": "assistant", "content": reply, "tools": tools}
                    )
                else:
                    err = f"Backend error {response.status_code}: {response.text[:300]}"
                    st.error(err)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": err, "tools": []}
                    )

            except requests.exceptions.ConnectionError:
                msg = "Could not reach the backend. Is uvicorn running on port 8000?"
                st.error(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg, "tools": []})

            except requests.exceptions.Timeout:
                msg = "The backend took too long to respond (>120s)."
                st.error(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg, "tools": []})

            except Exception as exc:
                msg = f"Unexpected error: {type(exc).__name__}: {exc}"
                st.error(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg, "tools": []})
