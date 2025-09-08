"""
Expense Tracker - Main Streamlit Application
A minimal UI for natural language expense tracking with AI extraction
"""

import streamlit as st
from datetime import datetime
import sys
import os
import hashlib
import hmac

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config.settings import settings
from src.services.expense_service import extract_and_save
from src.db.mongo import get_database
from src.db.indexes import ensure_indexes
from src.services.category_service import CategoryService
from src.models.expense import ExtractionResult
from src.repositories.expenses_repo import ExpensesRepository
from src.ai.providers import get_available_providers
from src.ui.main_page import main_page
from src.ui.sidebar import sidebar

# Available providers
AVAILABLE_PROVIDERS = get_available_providers()
from ui.components import color_picker

# -------- Authentication Helpers --------
def _get_admin_iterations() -> int:
    """Read PBKDF2 iterations from secrets/env with a safe default."""
    default_iterations = 200_000
    try:
        # Prefer Streamlit secrets if available
        if 'secrets' in dir(st):
            if 'admin_password_iterations' in st.secrets:
                return int(str(st.secrets['admin_password_iterations']).strip())
            if 'ADMIN_PASSWORD_ITERATIONS' in st.secrets:
                return int(str(st.secrets['ADMIN_PASSWORD_ITERATIONS']).strip())
    except Exception:
        pass
    try:
        from os import getenv
        env_val = getenv('ADMIN_PASSWORD_ITERATIONS')
        if env_val and env_val.strip():
            return int(env_val.strip())
    except Exception:
        pass
    return default_iterations


def verify_admin_password(plain_password: str) -> bool:
    """Verify the provided password.

    Prefers PBKDF2-SHA256 hash+salt if configured; otherwise falls back to
    comparing against an optional plaintext admin password from secrets.
    """
    try:
        stored_hash_hex = settings.admin_password_hash
        salt_hex = settings.admin_password_salt
        if stored_hash_hex and salt_hex:
            iterations = _get_admin_iterations()
            derived = hashlib.pbkdf2_hmac(
                'sha256',
                plain_password.encode('utf-8'),
                bytes.fromhex(salt_hex),
                iterations,
            )
            return hmac.compare_digest(derived.hex(), stored_hash_hex)

        # Fallback: plaintext secret
        if getattr(settings, 'admin_password_plain', None):
            return hmac.compare_digest(plain_password or "", settings.admin_password_plain)
        return False
    except Exception:
        return False


def render_auth_gate() -> None:
    """Render an access gate to choose Admin (with password) or Guest (read-only)."""
    st.title(f"{settings.app_icon} {settings.app_title}")
    st.markdown("Access required: sign in as Admin or continue as Guest (read-only)")
    with st.container(border=True):
        pwd = st.text_input("Admin Password", type="password", key="auth_password")
        c1, c2 = st.columns([1, 1])
        with c1:
            login = st.button("🔐 Login as Admin", type="primary")
        with c2:
            guest = st.button("👀 Continue as Guest")

        if login:
            if verify_admin_password(pwd or ""):
                st.session_state['role'] = 'admin'
                st.session_state.pop('auth_password', None)
                st.success("Authenticated as Admin")
                st.rerun()
            else:
                st.error("Invalid password")
        if guest:
            st.session_state['role'] = 'guest'
            st.rerun()

# Page configuration
st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# PWA: link manifest and register service worker (limited to /static scope)
st.markdown(
    """
    <link rel="manifest" href="/static/manifest.json">
    <meta name="theme-color" content="#0c6cf2">
    """,
    unsafe_allow_html=True,
)
st.components.v1.html(
    """
    <script>
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js').catch(err => console.warn('SW registration failed:', err));
      }
    </script>
    """,
    height=0,
)

# Initialize services and session state
if 'categories' not in st.session_state:
    try:
        category_service = CategoryService()
        # Seed default categories if none exist
        category_service.seed_default_categories()
        st.session_state.categories = category_service.get_all_categories()
    except Exception as e:
        st.session_state.categories = []

if 'expenses' not in st.session_state:
    try:
        db = get_database()
        ensure_indexes(db)
        repo = ExpensesRepository(db)
        st.session_state.expenses = repo.list_recent(limit=20)
    except Exception:
        st.session_state.expenses = []

if 'settings' not in st.session_state:
    st.session_state.settings = {
        'provider': settings.default_ai_provider,
        'model': settings.default_ai_model,
        'updated_at': datetime.now()
    }

if 'available_providers' not in st.session_state:
    st.session_state.available_providers = AVAILABLE_PROVIDERS

if 'expense_input' not in st.session_state:
    st.session_state.expense_input = ""

if 'extraction_result' not in st.session_state:
    st.session_state.extraction_result = None

if 'show_success' not in st.session_state:
    st.session_state.show_success = False

if 'editing_expense' not in st.session_state:
    st.session_state.editing_expense = None

if 'confirm_delete_expense' not in st.session_state:
    st.session_state.confirm_delete_expense = None

def main():
    """Main application entry point"""
    # Access gate (first visit)
    if 'role' not in st.session_state:
        render_auth_gate()
        st.stop()

    is_admin = st.session_state.get('role') == 'admin'

    # Title
    st.title(f"{settings.app_icon} {settings.app_title}")
    mode_label = "Admin" if is_admin else "Guest (read-only)"
    st.markdown(f"Track your expenses with natural language input and AI-powered extraction — **{mode_label}**")

    # Create two columns - main content and sidebar
    col1, col2 = st.columns([2, 1])

    with col1:
        main_page()

    with col2:
        sidebar()







if __name__ == "__main__":
    main()
