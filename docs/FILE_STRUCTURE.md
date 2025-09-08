## File/Folder Structure Plan

```
py_expense_tracker/
├─ app.py                          # Streamlit entrypoint
├─ docs/                           # Project documentation
│  ├─ FRD.md                      # Functional Requirements Document
│  ├─ UI_UX_PLAN.md               # UI/UX Design Plan
│  ├─ AI_EXTRACTION_PLAN.md       # AI Extraction Implementation Plan
│  ├─ IMPLEMENTATION_PLAN.md      # Implementation Plan
│  └─ FILE_STRUCTURE.md           # This file - project structure overview
├─ src/                           # Main application source code
│  ├─ ai/                         # AI/LLM integration
│  │  ├─ providers.py             # OpenAI/Gemini client factory
│  │  ├─ chains.py                # LangChain chain assembly
│  │  └─ prompts.py               # Prompt templates & few-shot examples
│  ├─ config/                     # Configuration management
│  │  └─ settings.py              # Pydantic settings (secrets/env)
│  ├─ db/                         # Database layer
│  │  ├─ mongo.py                 # Mongo client, connection management
│  │  └─ indexes.py               # Database index creation helpers
│  ├─ models/                     # Data models (Pydantic)
│  │  ├─ expense.py               # Expense data models
│  │  ├─ category.py              # Category data models
│  │  └─ settings.py              # Application settings models
│  ├─ repositories/               # Data access layer
│  │  ├─ expenses_repo.py         # CRUD operations for expenses
│  │  ├─ categories_repo.py       # CRUD for categories/subcategories
│  │  └─ app_settings_repo.py     # CRUD for provider/model settings
│  ├─ services/                   # Business logic layer
│  │  ├─ expense_service.py       # Biz logic for extraction + save
│  │  ├─ category_service.py      # Biz logic for taxonomy management
│  │  └─ settings_service.py      # Biz logic for settings management
│  ├─ ui/                         # User interface components
│  │  ├─ main_page.py             # Main page components & flow
│  │  ├─ sidebar.py               # Sidebar (categories + settings)
│  │  ├─ components.py            # Reusable UI widgets
│  │  └─ state.py                 # Session state helpers
│  └─ utils/                      # Utility functions
│     ├─ datetime_utils.py        # Timezone & parsing helpers
│     ├─ validation.py            # Schema validations
│     ├─ exceptions.py            # Custom exception classes
│     └─ logger.py                # Logging configuration
├─ .streamlit/                    # Streamlit configuration
│  ├─ secrets.toml                # API keys, Mongo URI (local only)
│  └─ secrets.toml.sample         # Template for secrets configuration
├─ venv/                          # Virtual environment (optional)
├─ requirements.txt               # Python dependencies
├─ README.md                      # Main project README
└─ README_simple.md               # Simplified README
```

### Notes

- **Architecture**: Keep Streamlit UI thin; route business logic through `services` layer.
- **Data Access**: Repositories encapsulate DB access; avoid direct DB calls from UI.
- **AI Integration**: Centralize provider selection in `ai/providers.py` with support for both text extraction and voice transcription.
- **Type Safety**: Use Pydantic models across boundaries for clarity and validation.
- **Voice Processing**: Voice transcription integrated into `ai/providers.py` with Gemini STT support.
- **Session Management**: Comprehensive state management across all UI components.
- **Error Handling**: Multi-layer validation and error recovery throughout the stack.
- **Security**: PBKDF2-SHA256 authentication with configurable iterations and secure API key management.
