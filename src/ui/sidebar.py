"""
Sidebar helpers - extracted from app.py for better organization
"""
import streamlit as st
from datetime import datetime
from src.db.mongo import get_database
from src.db.indexes import ensure_indexes
from src.config.settings import settings
from src.services.category_service import CategoryService
from src.models.category import CategoryCreate, SubcategoryCreate


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
