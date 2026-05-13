"""
auth.py — Authentication & Authorization
"""

import streamlit as st
import hashlib
import extra_streamlit_components as stx
from datetime import datetime, timedelta
from modules import sheets_db
from modules.utils import generate_id, now_str, hash_password_simple, verify_password_simple


# ---------------------------------------------------------------------------
# Cookie Manager
# ---------------------------------------------------------------------------

def get_cookie_manager():
    if "cookie_manager" not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager()
    return st.session_state.cookie_manager


# ---------------------------------------------------------------------------
# Password Hashing
# ---------------------------------------------------------------------------

def _hash_pw(password: str) -> str:
    return hash_password_simple(password)


def _verify_pw(password: str, hashed: str) -> bool:
    return verify_password_simple(password, hashed)


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------

def get_user_by_username(username: str):
    return sheets_db.find_one_by_field("users", "username", username)


def authenticate(username: str, password: str) -> dict | None:
    """Authenticate user. Returns user dict or None."""
    user = get_user_by_username(username)
    if not user:
        return None
    if not _verify_pw(password, user.get("password_hash", "")):
        return None
    if str(user.get("active", "1")) not in ("1", "True", "true", "yes"):
        return None
    # Update last login
    sheets_db.update_record("users", user["id"], {"last_login": now_str()})
    return user


def create_user(username: str, password: str, fullname: str, role: str,
                email: str = "", phone: str = ""):
    """Create a new user. Returns user dict or raises."""
    existing = get_user_by_username(username)
    if existing:
        raise ValueError(f"Username '{username}' sudah digunakan.")
    user = {
        "id": generate_id(),
        "username": username,
        "password_hash": _hash_pw(password),
        "fullname": fullname,
        "role": role,
        "email": email,
        "phone": phone,
        "active": "1",
        "last_login": "",
        "created_at": now_str(),
    }
    sheets_db.add_record("users", user)
    return user


def update_user(user_id: str, updates: dict):
    if "password" in updates and updates["password"]:
        updates["password_hash"] = _hash_pw(updates.pop("password"))
    elif "password" in updates:
        updates.pop("password")
    sheets_db.update_record("users", user_id, updates)


def init_default_admin():
    """Create default admin if no users exist."""
    users = sheets_db.get_all_records("users")
    if not users:
        default_pw = st.secrets.get("app", {}).get("default_admin_password", "Admin@2026")
        create_user(
            username="admin",
            password=default_pw,
            fullname="Administrator",
            role="admin",
            email="admin@ekepeg.local",
        )


# ---------------------------------------------------------------------------
# Session Management
# ---------------------------------------------------------------------------

def login_user(user: dict):
    st.session_state["authenticated"] = True
    st.session_state["user"] = {
        "id": user["id"],
        "username": user["username"],
        "fullname": user["fullname"],
        "role": user["role"],
        "email": user.get("email", ""),
    }
    st.session_state["login_time"] = now_str()


def logout_user():
    keys_to_keep = ["cookie_manager"]
    for key in list(st.session_state.keys()):
        if key not in keys_to_keep:
            del st.session_state[key]
    st.session_state["authenticated"] = False


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def get_current_user() -> dict:
    return st.session_state.get("user", {})


def require_auth():
    """Block access if not authenticated."""
    if not is_authenticated():
        st.warning("Silakan login terlebih dahulu.")
        st.stop()


def require_role(allowed_roles: list[str]):
    """Block access if user role is not in allowed_roles."""
    require_auth()
    user = get_current_user()
    if user.get("role") not in allowed_roles:
        st.error("Anda tidak memiliki akses ke halaman ini.")
        st.stop()


def has_role(roles: list[str]) -> bool:
    user = get_current_user()
    return user.get("role") in roles


# ---------------------------------------------------------------------------
# Login Page UI
# ---------------------------------------------------------------------------

def render_login_page():
    """Render the login page."""
    st.markdown("""
    <style>
    .login-container {
        max-width: 420px;
        margin: 60px auto;
        padding: 2.5rem;
        background: white;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(26,35,126,0.12);
    }
    .login-title {
        text-align: center;
        color: #1a237e;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 800;
        font-size: 1.8rem;
        margin-bottom: 0.2rem;
    }
    .login-subtitle {
        text-align: center;
        color: #546e7a;
        font-size: 0.9rem;
        margin-bottom: 2rem;
    }
    .login-logo {
        text-align: center;
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    </style>
    <div class="login-container">
        <div class="login-logo">🏛️</div>
        <div class="login-title">e-Kepegawaian</div>
        <div class="login-subtitle">Sistem Arsip & Manajemen Data Kepegawaian</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("👤 Username", placeholder="Masukkan username")
        password = st.text_input("🔒 Password", type="password", placeholder="Masukkan password")
        remember = st.checkbox("Ingat saya")
        submitted = st.form_submit_button("🔐 Masuk", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("Username dan password harus diisi.")
                return
            user = authenticate(username.strip(), password)
            if user:
                login_user(user)
                st.success(f"Selamat datang, {user['fullname']}!")
                st.rerun()
            else:
                st.error("Username atau password salah.")

    st.markdown(
        "<p style='text-align:center; color:#90a4ae; font-size:0.8rem; margin-top:1rem;'>"
        "Default: admin / Admin@2026</p>",
        unsafe_allow_html=True,
    )
