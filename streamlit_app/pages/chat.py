"""
Chat page for the Streamlit application.
"""

import streamlit as st
from utils.api_client import query_backend, document_upload_rag, get_chat_history, verify_jwt_token

# Configure page settings
st.set_page_config(
    page_title="Adaptive RAG - Chat",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="💬"
)

# Custom CSS for premium chat bubbles
st.markdown("""
    <style>
    /* User Message Bubble */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #2b313e;
        border-radius: 15px;
        padding: 10px 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #3d4556;
    }
    /* AI Message Bubble */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #1e1e1e;
        border-radius: 15px;
        padding: 10px 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #333;
    }
    /* Sidebar styling */
    .sidebar-section {
        background-color: #232323;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #333;
    }
    </style>
""", unsafe_allow_html=True)

# Use native Streamlit context for reading cookies synchronously
import streamlit.components.v1 as components

def delete_cookie(name: str):
    components.html(f'<script>document.cookie = "{name}=; max-age=0; path=/";</script>', height=0)

# Check and hydrate authentication from cookie synchronously
if "jwt_token" not in st.session_state:
    token_from_cookie = st.context.cookies.get('jwt_token')
    if token_from_cookie:
        res = verify_jwt_token(token_from_cookie)
        if res and res.get("valid"):
            st.session_state["jwt_token"] = token_from_cookie
            st.session_state["username"] = res.get("username")
        else:
            delete_cookie('jwt_token')

# Check authentication
if "jwt_token" not in st.session_state:
    st.warning("🔒 Please login from the Home page first.")
    st.stop()

# Initialize logout confirmation state
if "show_logout_confirm" not in st.session_state:
    st.session_state.show_logout_confirm = False

# Sidebar design
with st.sidebar:
    st.markdown("### 🧠 Adaptive RAG")
    st.caption(f"Logged in as **{st.session_state.get('username', 'User')}**")
    st.write("---")
    
    st.markdown("### 📂 Knowledge Base")
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload a PDF or TXT file", type=["pdf", "txt"], label_visibility="collapsed")
    
    file_description = None
    if uploaded_file:
        file_description = st.text_input(
            "📄 Document Description",
            max_chars=300,
            placeholder="E.g. Technical spec for Project X"
        )

        if "uploaded_files" not in st.session_state:
            st.session_state.uploaded_files = {}

        file_key = f"{uploaded_file.name}_{file_description}"

        if file_description:
            if file_key not in st.session_state.uploaded_files:
                with st.spinner("Processing document..."):
                    success = document_upload_rag(uploaded_file, file_description)
                if success:
                    st.success(f"Added to knowledge base: {uploaded_file.name}")
                    st.session_state.uploaded_files[file_key] = True
                else:
                    st.error(f"Failed to process: {uploaded_file.name}")
            else:
                st.info(f"Active in knowledge base: {uploaded_file.name}")
        else:
            st.warning("Please provide a short description to index this document.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.write("---")
    
    # Logout section in sidebar
    if st.button("🔒 Logout", use_container_width=True):
        st.session_state.show_logout_confirm = True

    if st.session_state.show_logout_confirm:
        st.warning("Are you sure?")
        col_confirm, col_cancel = st.columns(2)
        with col_confirm:
            if st.button("✅ Yes"):
                delete_cookie('jwt_token')
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                import time
                time.sleep(0.5)
                st.switch_page("home.py")
        with col_cancel:
            if st.button("❌ No"):
                st.session_state.show_logout_confirm = False
                st.rerun()

# Main Chat Interface
st.title("💬 Chat Session")
st.caption("Ask questions about your documents, general knowledge, or search the web.")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    # Fetch history from backend
    backend_history = get_chat_history(st.session_state["jwt_token"])
    if backend_history:
        for msg in backend_history:
            st.session_state.chat_history.append((msg["role"], msg["content"]))

# Display chat history
for role, text in st.session_state.chat_history:
    st.chat_message(role).write(text)

# User input
user_input = st.chat_input("Type your message here...")

# Process user input and get response
if user_input:
    st.session_state.chat_history.append(("user", user_input))
    st.chat_message("user").write(user_input)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = query_backend(user_input, st.session_state["jwt_token"])
            st.write(response)
            
    st.session_state.chat_history.append(("assistant", response))
