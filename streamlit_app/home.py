"""
Home page for Streamlit authentication and landing dashboard.
"""

import logging
import streamlit as st
from utils.api_client import create_user, login_user, get_api_token, verify_jwt_token

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="app.log",
    filemode="a",
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Adaptive RAG", layout="centered", page_icon="🧠")

# Custom CSS for modern styling
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        font-weight: 800;
        font-size: 3rem;
        background: -webkit-linear-gradient(45deg, #FF4B2B, #FF416C);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .sub-title {
        text-align: center;
        font-size: 1.2rem;
        color: #888;
        margin-bottom: 40px;
    }
    .feature-box {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
        border: 1px solid #333;
        transition: transform 0.2s;
    }
    .feature-box:hover {
        transform: translateY(-5px);
        border-color: #FF416C;
    }
    </style>
""", unsafe_allow_html=True)

# Use native Streamlit context for reading cookies synchronously
import streamlit.components.v1 as components

def set_cookie(name: str, value: str):
    components.html(f'<script>document.cookie = "{name}={value}; max-age=604800; path=/";</script>', height=0)

def delete_cookie(name: str):
    components.html(f'<script>document.cookie = "{name}=; max-age=0; path=/";</script>', height=0)

# Check for existing cookie session synchronously
if "jwt_token" not in st.session_state:
    token_from_cookie = st.context.cookies.get('jwt_token')
    if token_from_cookie:
        res = verify_jwt_token(token_from_cookie)
        if res and res.get("valid"):
            st.session_state["jwt_token"] = token_from_cookie
            st.session_state["username"] = res.get("username")
        else:
            delete_cookie('jwt_token')

# ----------------- Dashboard View (Logged In) -----------------
if "jwt_token" in st.session_state:
    st.markdown('<div class="main-title">Adaptive RAG</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Agentic AI Chatbot & Document Assistant</div>', unsafe_allow_html=True)
    
    st.write("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="feature-box"><h3>📄<br>Doc RAG</h3>Upload your PDFs and chat instantly with your data.</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="feature-box"><h3>🌐<br>Web Search</h3>Real-time web browsing via Tavily for fresh answers.</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="feature-box"><h3>🤖<br>ReAct AI</h3>LangGraph-powered agent decides when to search or read.</div>', unsafe_allow_html=True)
    
    st.write("---")
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("🚀 Go to Chat", type="primary", use_container_width=True):
            st.switch_page("pages/chat.py")
        if st.button("🔒 Logout", use_container_width=True):
            delete_cookie('jwt_token')
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            import time
            time.sleep(0.5)
            st.rerun()

# ----------------- Login View (Logged Out) -----------------
else:
    # Hide sidebar for logged-out users
    hide_sidebar_style = """
        <style>
            [data-testid="stSidebar"] { display: none; }
        </style>
    """
    st.markdown(hide_sidebar_style, unsafe_allow_html=True)

    st.markdown('<div class="main-title">Welcome</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Sign in to your Adaptive RAG workspace</div>', unsafe_allow_html=True)

    # Fetch API token only once per session
    if "session_id" not in st.session_state:
        token = get_api_token()
        if token:
            st.session_state["session_id"] = token
        else:
            st.error("Failed to initialize API token.")
            st.stop()

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.container(border=True):
            with st.form("auth_form"):
                mode = st.radio("Choose action:", ["Login", "Create Account"], horizontal=True)
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submit = st.form_submit_button("Proceed", type="primary", use_container_width=True)

        if submit:
            if not username or not password:
                st.error("Username and password required.")
            else:
                if mode == "Create Account":
                    success = create_user(username, password, st.session_state["session_id"])
                    if success:
                        st.success("Account created successfully! Please select Login.")
                    else:
                        st.error("User creation failed.")
                else:
                    response = login_user(username, password, st.session_state["session_id"])
                    if response and response.get("jwt"):
                        st.session_state["jwt_token"] = response["jwt"]
                        st.session_state["username"] = username
                        set_cookie('jwt_token', response["jwt"])
                        import time
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Login failed. Invalid credentials.")
