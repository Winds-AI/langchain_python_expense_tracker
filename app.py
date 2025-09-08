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

def main_page():
    """Main page with expense input and recent expenses"""

    st.header("Add New Expense")

    is_admin = st.session_state.get('role') == 'admin'

    # Expense input form (admin only)
    if is_admin:
        with st.form("expense_form"):
            # Voice input row: audio input + inline controls + text area
            st.markdown("### Input")
            vcol1, vcol2 = st.columns([1, 3])

            with vcol1:
                audio = st.audio_input("🎙️ Record", key="voice_input")
                st.caption("Tip: Chrome/Edge often record WebM/Opus. WAV or Opus usually gives better results.")

            with vcol2:
                expense_text = st.text_area(
                    "Describe your expense:",
                    value=st.session_state.expense_input,
                    height=100,
                    placeholder="e.g., Paid 250 for lunch at SpiceHub yesterday, or Bus fare 45 to office",
                    help="Enter your expense or use voice above; we'll transcribe and fill this for confirmation."
                )

            # Inline controls under input
            c1, c2, c3 = st.columns([1, 1, 2])
            with c1:
                transcribe_btn = st.form_submit_button("📝 Transcribe", use_container_width=True)
            with c2:
                clear_voice_btn = st.form_submit_button("❌ Clear Voice", use_container_width=True)

            col_extract, col_clear = st.columns(2)

            with col_extract:
                extract_button = st.form_submit_button(
                    "🔍 Extract & Save",
                    type="primary",
                    use_container_width=True
                )

            with col_clear:
                clear_button = st.form_submit_button(
                    "🗑️ Clear",
                    use_container_width=True
                )
    else:
        st.info("Guest mode: Sign in as Admin to add new expenses.")
        # Initialize placeholders to avoid reference issues
        audio = None
        expense_text = st.session_state.get('expense_input', '')
        transcribe_btn = False
        clear_voice_btn = False
        extract_button = False
        clear_button = False

    # Voice UI actions inside the same form submit cycle
    if 'is_transcribing' not in st.session_state:
        st.session_state.is_transcribing = False

    if is_admin and clear_voice_btn:
        st.session_state.pop('voice_input', None)
        st.toast("Voice input cleared", icon="✅")

    if is_admin and transcribe_btn:
        if audio and audio.type:
            try:
                from src.ai.providers import transcribe_with_gemini
                st.session_state.is_transcribing = True
                with st.spinner("Transcribing voice to text with Gemini…"):
                    audio_bytes = audio.getvalue()
                    # Normalize MIME to prefer explicit codec hints for better STT
                    raw_mime = audio.type or ""
                    if raw_mime == "audio/webm":
                        mime_type = "audio/webm;codecs=opus"
                    elif raw_mime == "audio/ogg":
                        mime_type = "audio/ogg;codecs=opus"
                    else:
                        mime_type = raw_mime or "audio/wav"
                    # Prefer a cheap, STT-capable Gemini model
                    transcript = transcribe_with_gemini(
                        audio_bytes=audio_bytes,
                        mime_type=mime_type,
                        model="gemini-1.5-flash",
                        prompt=None,
                    )
                st.session_state.is_transcribing = False
                if transcript:
                    # Append or replace based on existing text (read from state for consistency)
                    existing = st.session_state.get('expense_input', '')
                    merged = (existing + " \n" + transcript).strip() if existing.strip() else transcript
                    # Update both the backing state and the widget state for instant render
                    st.session_state.expense_input = merged
                    st.success("✅ Transcription complete. Confirm/edit before extracting.")
                    st.rerun()
                else:
                    st.warning("No transcription returned. Try recording again.")
            except Exception as e:
                st.session_state.is_transcribing = False
                st.error(f"Transcription failed: {e}")
        else:
            st.warning("Please record audio first.")

    # Handle extract submission
    if is_admin and extract_button:
        if expense_text.strip():
            provider = st.session_state.settings['provider']
            model = st.session_state.settings['model']
            try:
                result, expense_id, log_id = extract_and_save(
                    original_query=expense_text,
                    provider=provider,
                    model=model,
                    settings_snapshot={
                        'provider': provider,
                        'model': model,
                    },
                )
            except Exception as e:
                # Surface error in UI and debug panel
                result = ExtractionResult(valid=False, missing_fields=["amount"], error=str(e))
                expense_id = ""
                log_id = ""

            st.session_state.extraction_result = result.model_dump()
            st.session_state.extraction_result['expense_id'] = expense_id
            st.session_state.extraction_result['log_id'] = log_id
            st.session_state.expense_input = expense_text

            if result.valid:
                # Reload latest from DB for accuracy
                try:
                    db = get_database()
                    repo = ExpensesRepository(db)
                    st.session_state.expenses = repo.list_recent(limit=20)
                except Exception:
                    pass
                st.session_state.show_success = True
                st.session_state.expense_input = ""
            else:
                st.session_state.show_success = False
        else:
            st.error("Please enter an expense description.")

    if is_admin and clear_button:
        st.session_state.expense_input = ""
        st.session_state.extraction_result = None
        st.session_state.show_success = False

    # Show extraction result
    if st.session_state.extraction_result:
        display_extraction_result()

    # Show success message
    if st.session_state.show_success:
        st.success("✅ Expense saved successfully!")
        st.session_state.show_success = False

    # Recent expenses
    st.header("Recent Expenses")

    if st.session_state.expenses:
        for i, expense in enumerate(st.session_state.expenses[:5]):  # Show last 5
            with st.expander(f"₹{expense['amount']} - {expense['description']} ({expense['category']})"):
                # Action buttons
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.empty()  # Spacer
                with col2:
                    if st.button("✏️ Edit", key=f"edit_expense_{i}", disabled=st.session_state.get('role') != 'admin'):
                        st.session_state.editing_expense = expense
                        st.rerun()
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_expense_{i}", disabled=st.session_state.get('role') != 'admin'):
                        st.session_state.confirm_delete_expense = expense
                        st.rerun()

                # Expense details
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Category:** {expense['category']}")
                    st.write(f"**Subcategory:** {expense['subcategory']}")
                    st.write(f"**Amount:** ₹{expense['amount']}")
                with col2:
                    try:
                        dt = expense['datetime']
                        dt_show = (dt.strftime('%Y-%m-%d %H:%M') if hasattr(dt, 'strftime') else str(dt))
                    except Exception:
                        dt_show = "-"
                    st.write(f"**Date:** {dt_show}")
                    st.write(f"**Provider:** {expense['provider']} ({expense['model']})")
    else:
        st.info("No expenses yet. Add your first expense above!")

    # Handle edit expense dialog
    if st.session_state.get('role') == 'admin' and st.session_state.editing_expense:
        show_edit_expense_dialog()

    # Handle delete confirmation dialog
    if st.session_state.get('role') == 'admin' and st.session_state.confirm_delete_expense:
        show_delete_confirmation_dialog()

def show_edit_expense_dialog():
    """Display the edit expense dialog"""
    expense = st.session_state.editing_expense
    if not expense:
        return

    st.header("✏️ Edit Expense")

    with st.form("edit_expense_form"):
        # Pre-populate form with current values
        amount = st.number_input("Amount", value=float(expense.get('amount', 0)), min_value=0.01, step=0.01)
        description = st.text_input("Description", value=expense.get('description', ''))
        category = st.text_input("Category", value=expense.get('category', ''))
        subcategory = st.text_input("Subcategory", value=expense.get('subcategory', ''))

        # Date input
        try:
            dt = expense.get('datetime')
            if hasattr(dt, 'date'):
                default_date = dt.date()
                default_time = dt.time()
            else:
                from datetime import datetime
                default_date = datetime.now().date()
                default_time = datetime.now().time()
        except:
            from datetime import datetime
            default_date = datetime.now().date()
            default_time = datetime.now().time()

        date = st.date_input("Date", value=default_date)
        time = st.time_input("Time", value=default_time)

        col1, col2 = st.columns(2)
        with col1:
            save_button = st.form_submit_button("💾 Save Changes", type="primary")
        with col2:
            cancel_button = st.form_submit_button("❌ Cancel")

    if save_button:
        try:
            from datetime import datetime
            from src.services.expense_service import update_expense
            from src.models.expense import ExpenseUpdate
            from src.utils.datetime_utils import to_utc

            # Combine date and time
            combined_datetime = datetime.combine(date, time)
            utc_datetime = to_utc(combined_datetime)

            # Create update object
            updates = ExpenseUpdate(
                amount=amount,
                description=description,
                category=category,
                subcategory=subcategory,
                datetime=utc_datetime
            )

            # Update the expense
            expense_id = str(expense['_id'])
            updated_expense = update_expense(expense_id, updates)

            if updated_expense:
                st.success("✅ Expense updated successfully!")
                # Refresh expenses list
                db = get_database()
                repo = ExpensesRepository(db)
                st.session_state.expenses = repo.list_recent(limit=20)
            else:
                st.error("❌ Failed to update expense")

        except Exception as e:
            st.error(f"❌ Error updating expense: {e}")

        # Clear edit state
        st.session_state.editing_expense = None
        st.rerun()

    if cancel_button:
        st.session_state.editing_expense = None
        st.rerun()

def show_delete_confirmation_dialog():
    """Display delete confirmation dialog"""
    expense = st.session_state.confirm_delete_expense
    if not expense:
        return

    st.header("🗑️ Delete Expense")

    st.warning("Are you sure you want to delete this expense?")
    st.write(f"**Amount:** ₹{expense.get('amount', 0)}")
    st.write(f"**Description:** {expense.get('description', '')}")
    st.write(f"**Category:** {expense.get('category', '')}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Yes, Delete", type="primary"):
            try:
                from src.services.expense_service import delete_expense
                expense_id = str(expense['_id'])
                deleted = delete_expense(expense_id)

                if deleted:
                    st.success("✅ Expense deleted successfully!")
                    # Refresh expenses list
                    db = get_database()
                    repo = ExpensesRepository(db)
                    st.session_state.expenses = repo.list_recent(limit=20)
                else:
                    st.error("❌ Expense not found or already deleted")

            except Exception as e:
                st.error(f"❌ Error deleting expense: {e}")

            # Clear delete state
            st.session_state.confirm_delete_expense = None
            st.rerun()

    with col2:
        if st.button("❌ Cancel"):
            st.session_state.confirm_delete_expense = None
            st.rerun()

def mock_extract_expense(text):
    """Deprecated: kept for reference, no longer used."""
    return {
        'valid': False,
        'missing_fields': ['amount'],
        'reason': 'Deprecated mock extractor. Use AI extraction instead.'
    }

def display_extraction_result():
    """Display the extraction result"""
    result = st.session_state.extraction_result

    if result.get('valid', True):
        st.success("✅ Successfully extracted expense details!")

        # Display extracted information
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Amount", f"₹{result.get('amount', 0)}")

        with col2:
            st.write(f"**Category:** {result.get('category', 'Unknown')}")
            st.write(f"**Subcategory:** {result.get('subcategory', 'Unknown')}")

        with col3:
            # Display time in IST
            try:
                from src.utils.datetime_utils import to_ist
                dt_val = result.get('datetime', datetime.now())
                if hasattr(dt_val, 'isoformat'):
                    dt_show = to_ist(dt_val).strftime('%Y-%m-%d %H:%M')
                else:
                    dt_show = to_ist(datetime.fromisoformat(str(dt_val))).strftime('%Y-%m-%d %H:%M')
            except Exception:
                dt_show = datetime.now().strftime('%Y-%m-%d %H:%M')
            st.write(f"**Date (IST):** {dt_show}")

        st.write(f"**Description:** {result.get('description', '')}")

        # Debug panel (if enabled)
        if st.session_state.get('debug_mode', False):
            with st.expander("🔎 Debug Details", expanded=True):
                st.write("**Expense ID:**", result.get('expense_id', ''))
                st.write("**Log ID:**", result.get('log_id', ''))
                st.write("**LangSmith Tracing:**", "✅ Enabled" if settings.langsmith_api_key else "❌ Disabled")
                st.write("**Raw Response:**")
                st.json(result.get('raw_response', {}))
    else:
        st.error("❌ Could not extract expense details")

        st.write("**Missing Fields:**")
        for field in result.get('missing_fields', []):
            st.write(f"- {field.title()}")

        if result.get('reason'):
            st.write(f"**Reason:** {result['reason']}")
        if result.get('error'):
            st.write(f"**Error:** {result['error']}")

def sidebar():
    """Sidebar with categories management and settings"""

    # User role & logout
    with st.container(border=True):
        role = st.session_state.get('role', 'guest')
        st.markdown(f"**User:** {'Admin' if role == 'admin' else 'Guest (read-only)'}")
        if st.button("🚪 Logout"):
            for k in [
                'role', 'auth_password', 'expense_input', 'extraction_result',
                'editing_expense', 'confirm_delete_expense'
            ]:
                st.session_state.pop(k, None)
            st.rerun()

    # Categories Management
    st.header("📂 Categories")

    with st.expander("Manage Categories", expanded=False):
        if st.session_state.get('role') == 'admin':
            # Add new category
            with st.form("add_category"):
                new_category = st.text_input("New Category Name")
                # Use Streamlit's native color picker inside forms (form-safe)
                color = st.color_picker(
                    "Choose Category Color",
                    value="#F8BBD9",
                    key="category_color_picker_native",
                    help="Pick a beautiful pastel color for your category"
                )
                # Ensure color is properly formatted
                color = color.strip() if color else "#F8BBD9"
                icon = st.text_input("Icon (emoji or short text)", placeholder="🍽️")
                add_cat_btn = st.form_submit_button("Add Category")

                if add_cat_btn and new_category.strip():
                    # Check if category already exists
                    if any((cat['name'] if isinstance(cat, dict) else getattr(cat, 'name', '')).lower() == new_category.lower() for cat in st.session_state.categories):
                        st.error("Category already exists!")
                    else:
                        try:
                            # Try service-based create if available
                            from src.services.category_service import CategoryService
                            from src.models.category import CategoryCreate
                            svc = CategoryService()
                            created = svc.create_category(CategoryCreate(name=new_category.strip(), description=None, color=color, icon=icon.strip() if icon else None))
                            st.session_state.categories = svc.get_all_categories()
                            st.success(f"Category '{created.name}' added!")
                            st.rerun()
                        except Exception:
                            # Fallback to session dict for legacy demo
                            st.session_state.categories.append({
                                'name': new_category.strip(),
                                'subcategories': [],
                                'color': color,
                                'icon': icon.strip() if icon else None,
                                'created_at': datetime.now(),
                                'updated_at': datetime.now()
                            })
                            st.success(f"Category '{new_category}' added!")
                            st.rerun()
        else:
            st.info("Guest mode: Category management is disabled.")

    # Display existing categories
    for i, category in enumerate(st.session_state.categories):
        # Support both dicts (legacy mock) and CategoryModel objects
        cat_name = category.get('name') if isinstance(category, dict) else getattr(category, 'name', 'Unknown')
        cat_subs = category.get('subcategories') if isinstance(category, dict) else getattr(category, 'subcategories', [])
        cat_id = category.get('id') if isinstance(category, dict) else getattr(category, 'id', None)

        with st.expander(f"{cat_name} ({len(cat_subs)} subcategories)"):
            # Add subcategory
            if st.session_state.get('role') == 'admin':
                with st.form(f"add_sub_{i}"):
                    new_sub = st.text_input(f"Add subcategory to {cat_name}")
                    add_sub_btn = st.form_submit_button("Add Subcategory")

                    if add_sub_btn and new_sub.strip():
                        try:
                            # For dict legacy data
                            if isinstance(category, dict):
                                if new_sub.lower() in [s.lower() for s in cat_subs]:
                                    st.error("Subcategory already exists!")
                                else:
                                    st.session_state.categories[i]['subcategories'].append(new_sub.strip())
                                    st.session_state.categories[i]['updated_at'] = datetime.now()
                                    st.success(f"Subcategory '{new_sub}' added!")
                                    st.rerun()
                            else:
                                # CategoryModel via service
                                from src.services.category_service import CategoryService
                                from src.models.category import SubcategoryCreate
                                svc = CategoryService()
                                svc.add_subcategory(str(cat_id), SubcategoryCreate(name=new_sub.strip()))
                                st.session_state.categories = svc.get_all_categories()
                                st.success(f"Subcategory '{new_sub}' added!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Failed to add subcategory: {e}")
            else:
                st.caption("Guest mode: Adding subcategories is disabled.")

            # List subcategories
            if cat_subs:
                st.write("**Subcategories:**")
                for j, subcat in enumerate(cat_subs):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        # subcat may be string or SubcategoryModel
                        sub_name = subcat if isinstance(subcat, str) else getattr(subcat, 'name', str(subcat))
                        st.write(f"• {sub_name}")
                    with col2:
                        if st.button("🗑️", key=f"del_sub_{i}_{j}", disabled=st.session_state.get('role') != 'admin'):
                            try:
                                if isinstance(category, dict):
                                    st.session_state.categories[i]['subcategories'].pop(j)
                                    st.session_state.categories[i]['updated_at'] = datetime.now()
                                    st.rerun()
                                else:
                                    from src.services.category_service import CategoryService
                                    svc = CategoryService()
                                    if sub_name:
                                        svc.remove_subcategory(str(cat_id), sub_name)
                                        st.session_state.categories = svc.get_all_categories()
                                        st.rerun()
                            except Exception as e:
                                st.error(f"Failed to remove subcategory: {e}")
            else:
                st.info("No subcategories yet.")

            # Delete category
            if st.button(f"Delete {cat_name}", key=f"del_cat_{i}", disabled=st.session_state.get('role') != 'admin'):
                try:
                    if isinstance(category, dict):
                        st.session_state.categories.pop(i)
                        st.success("Category deleted!")
                        st.rerun()
                    else:
                        from src.services.category_service import CategoryService
                        svc = CategoryService()
                        if cat_id:
                            svc.delete_category(str(cat_id))
                            st.session_state.categories = svc.get_all_categories()
                            st.success("Category deleted!")
                            st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete category: {e}")

    # Settings
    st.header("⚙️ Settings")

    with st.expander("AI Provider Settings", expanded=False):
        # Provider selection
        current_provider = st.session_state.settings['provider']
        new_provider = st.selectbox(
            "AI Provider",
            options=list(st.session_state.available_providers.keys()),
            index=list(st.session_state.available_providers.keys()).index(current_provider),
            disabled=st.session_state.get('role') != 'admin'
        )

        # Model selection based on provider
        available_models = st.session_state.available_providers[new_provider]
        current_model = st.session_state.settings['model'] if st.session_state.settings['model'] in available_models else available_models[0]
        new_model = st.selectbox(
            "Model",
            options=available_models,
            index=available_models.index(current_model),
            disabled=st.session_state.get('role') != 'admin'
        )

        if st.button("Save Settings", disabled=st.session_state.get('role') != 'admin'):
            st.session_state.settings['provider'] = new_provider
            st.session_state.settings['model'] = new_model
            st.session_state.settings['updated_at'] = datetime.now()
            st.success("Settings saved!")

        st.info("💡 API keys should be configured in `.streamlit/secrets.toml`")

    # Debug
    st.header("🐞 Debug")
    debug_mode = st.toggle("Enable Debug Mode", value=st.session_state.get('debug_mode', False), disabled=st.session_state.get('role') != 'admin')
    st.session_state['debug_mode'] = debug_mode
    if debug_mode:
        st.caption("Debug mode will show detailed logs, raw model output, and errors.")

    # DB status
    with st.expander("Database Status", expanded=True):  # Expanded by default for debugging
        # Debug section to show loaded secrets
        st.subheader("Secrets Debug")
        try:
            # Show if st.secrets is available
            if 'secrets' not in dir(st):
                st.error("st.secrets is not available")
                
            # Try database connection
            db = get_database()
            ensure_indexes(db)
            st.success("Connected to MongoDB")
        except Exception as e:
            st.error(f"MongoDB connection error: {e}")
            import traceback
            st.code(traceback.format_exc())

        # LangSmith status
        if settings.langsmith_api_key:
            st.success("LangSmith Tracing: ✅ Enabled")
            st.caption("All AI calls will be traced in LangSmith dashboard")
        else:
            st.warning("LangSmith Tracing: ❌ Disabled")
            st.caption("Add langsmith_api_key to secrets.toml to enable tracing")

if __name__ == "__main__":
    main()
