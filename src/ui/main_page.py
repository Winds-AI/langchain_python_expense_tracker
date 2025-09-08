# Main page components & flow
import streamlit as st
from datetime import datetime
from src.services.expense_service import extract_and_save, update_expense, delete_expense
from src.db.mongo import get_database
from src.repositories.expenses_repo import ExpensesRepository
from src.models.expense import ExpenseUpdate, ExtractionResult
from src.utils.datetime_utils import to_utc, to_ist
from src.ai.providers import transcribe_with_gemini
from src.config.settings import settings


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
