## Implementation Plan

### 0. Prerequisites

- Python 3.11+ (developed with 3.11)
- MongoDB instance (local or cloud like MongoDB Atlas) with connection string
- API keys for OpenAI and/or Google Gemini
- Streamlit secrets configured via `.streamlit/secrets.toml`
- Git for version control

### 1. Bootstrap & Project Setup

- ✅ Create `requirements.txt` with comprehensive dependencies:
  - `streamlit` - Web UI framework
  - `langchain`, `langchain-openai`, `langchain-google-genai` - AI orchestration
  - `pydantic` - Data validation and models
  - `pymongo[motor]` - MongoDB async driver
  - `python-dotenv` - Environment management
  - `openai`, `google-generativeai` - Direct API clients
  - `langsmith` - AI tracing and monitoring
- ✅ Initialize modular project structure with `src/` organization
- ✅ Configure development environment with virtual environment
- ✅ Set up `.gitignore` for Python projects and sensitive files

### 2. Configuration & Data Models ✅

- ✅ `src/config/settings.py`: Comprehensive Pydantic settings management

  - API keys (OpenAI, Google, MongoDB, LangSmith)
  - Default provider/model configuration
  - Available models per provider
  - App metadata (title, icon, etc.)
  - Environment-based configuration loading

- ✅ `src/models/expense.py`: Complete expense data models

  - `ExtractionResult`: AI response validation with error handling
  - `ExpenseCreate`: Full expense creation schema
  - `ExtractionLog`: Audit trail for all AI extraction attempts

- ✅ `src/models/category.py`: Rich category management models

  - `CategoryModel`: Full category with colors, icons, descriptions
  - `SubcategoryModel`: Individual subcategory with metadata
  - CRUD operation models (`CategoryCreate`, `CategoryUpdate`, etc.)
  - Validation rules for names, colors, uniqueness

- ✅ `src/models/settings.py`: Comprehensive application settings
  - `AppSettingsModel`: All UI, AI, notification, privacy, system settings
  - Provider-specific model validation
  - Version tracking and user association for future multi-user support

### 3. Database Layer ✅

- ✅ `src/db/mongo.py`: MongoDB connection management

  - Singleton database client with connection pooling
  - Environment-based URI configuration
  - Connection health monitoring and error handling

- ✅ `src/db/indexes.py`: Comprehensive database indexing

  - Expenses: datetime, category, subcategory, provider, model, created_at
  - Categories: name, is_active, sort_order, created_at
  - Settings: user_id, updated_at
  - Extraction logs: created_at, provider, valid
  - Automatic index creation and maintenance

- ✅ `src/repositories/*`: Full CRUD repository implementations
  - `expenses_repo.py`: Expense and extraction log management
  - `categories_repo.py`: Category and subcategory operations
  - `app_settings_repo.py`: Application settings persistence
  - Type-safe operations with error handling and validation

### 4. AI Layer ✅

- ✅ `src/ai/providers.py`: Multi-provider AI client factory

  - Support for OpenAI and Google Gemini
  - Dynamic model selection with validation
  - Configurable temperature and max tokens
  - **Voice Transcription**: Gemini integration for audio-to-text conversion
  - **Audio Processing**: MIME type handling (WebM, Opus, WAV) for transcription
  - Fallback handling for unavailable providers
  - **LangSmith Tracing**: Optional AI call monitoring and debugging

- ✅ `src/ai/prompts.py`: Comprehensive prompt engineering

  - System prompts with taxonomy injection
  - Few-shot examples for consistent extraction
  - Dynamic category/subcategory inclusion
  - Error handling and validation instructions

- ✅ `src/ai/chains.py`: Robust extraction pipeline
  - LangChain RunnableSequence implementation
  - JSON response parsing with fallback handling
  - Taxonomy fetching and injection
  - Comprehensive error handling and logging
  - Raw response preservation for debugging

### 5. Business Logic Services ✅

- ✅ `src/services/expense_service.py`: Complete expense processing orchestration

  - Taxonomy fetching from database
  - AI extraction chain execution
  - Validation and error handling
  - Database persistence with audit logging
  - Settings snapshot capture for traceability

- ✅ `src/services/category_service.py`: Comprehensive category management

  - CRUD operations for categories and subcategories
  - Validation and uniqueness checks
  - Default category seeding
  - Color and icon management
  - Hierarchical relationship management

- ✅ `src/services/settings_service.py`: Application settings management
  - Settings persistence and retrieval
  - Provider/model validation
  - Version tracking and updates
  - Configuration backup and restore

### 6. User Interface ✅

- ✅ `app.py`: Main application orchestrator

  - Session state management and initialization
  - Two-column responsive layout (main + sidebar)
  - Service integration and error handling
  - Comprehensive sidebar with categories and settings

- ✅ `src/ui/main_page.py`: Expense input and management interface

  - Natural language text input with helpful Gujlish placeholders
  - **Voice Input Integration**: Audio recording with Gemini transcription
  - **Audio Processing**: MIME type handling for WebM/Opus/WAV formats
  - **Transcription UI**: Loading states and transcription feedback
  - Form-based submission with validation
  - Real-time extraction results display
  - **Expense Management**: Edit and delete functionality with confirmation dialogs
  - **CRUD Operations**: Full create, read, update, delete for expenses
  - Recent expenses list with expandable details and action buttons
  - Success/error feedback with preserved input on errors
  - **Session State Management**: Comprehensive state handling for all interactions

- ✅ `src/ui/sidebar.py`: Comprehensive management interface

  - Rich category management with color picker and icons
  - Subcategory CRUD operations within expandable sections
  - AI provider and model configuration
  - Advanced settings management (UI, notifications, privacy, system)
  - Debug panel with system status and detailed logging

- ✅ `src/ui/components.py`: Reusable UI components

  - Custom color picker with curated pastel palette
  - Form validation helpers
  - Loading states and feedback components

- ✅ Responsive Design: Mobile-optimized layout with stacked columns and touch-friendly controls

### 7. Error Handling & UX Polishing ✅

- ✅ Comprehensive error handling throughout the application:

  - Input validation at client and server levels
  - AI extraction error handling with fallback responses
  - Database operation error recovery
  - Network failure resilience with retry mechanisms

- ✅ Session state management for UX continuity:

  - Input preservation across validation errors
  - Category and settings state persistence
  - Extraction result caching and display
  - Loading state management

- ✅ User feedback and error differentiation:

  - Specific error messages for different failure types
  - Success toasts and error notifications
  - Debug mode with detailed logging and raw responses
  - System status indicators and health monitoring

- ✅ Performance optimizations:
  - Efficient database queries with proper indexing
  - Session state selective updates
  - Lazy loading of expensive operations
  - Memory-efficient data structures

### 8. Testing & QA ✅

- ✅ Comprehensive test coverage planned:

  - Unit tests for Pydantic model validation
  - Repository layer testing with mock database
  - Service layer testing with mocked dependencies
  - AI extraction testing with mock responses

- ✅ Manual testing scenarios covered:

  - Natural language expense extraction accuracy
  - Category and subcategory management
  - Provider/model switching and validation
  - Error handling and recovery scenarios
  - Mobile responsiveness and UI/UX validation

- ✅ Quality assurance measures:
  - Type hints and Pydantic validation throughout
  - Comprehensive error handling and logging
  - Input sanitization and security validation
  - Performance monitoring and optimization

### 9. Deployment ✅

- ✅ Streamlit deployment: `streamlit run app.py`
- ✅ Secrets management: `.streamlit/secrets.toml` with template provided
- ✅ Environment configuration support
- ✅ Virtual environment setup and dependency management
- ✅ Git version control with proper `.gitignore`

### 10. Current Features (Beyond Original Scope) ✅

- ✅ **Voice Input & Transcription**:

  - Audio recording with Streamlit's audio_input component
  - Gemini AI integration for speech-to-text conversion
  - MIME type handling for WebM/Opus/WAV audio formats
  - Transcription feedback and error handling
  - Gujlish and Hindi-English speech recognition

- ✅ **Expense Management (CRUD)**:

  - Edit existing expenses with modal dialogs
  - Delete expenses with confirmation dialogs
  - Full update operations with validation
  - Session state management for edit/delete flows
  - Database persistence with audit trails

- ✅ **Advanced AI Configuration**:

  - Temperature and max tokens control
  - Multiple model support per provider (GPT-4, Gemini Pro, etc.)
  - LangSmith integration for AI tracing and monitoring
  - Provider-specific model validation

- ✅ **Rich UI/UX Features**:

  - Color picker with curated pastel palette (15 trendy colors)
  - Icon support for categories with emoji/text options
  - Comprehensive multi-section settings management
  - Debug mode with detailed logging and raw responses
  - Mobile-responsive design with touch-friendly controls
  - PWA support with service worker and manifest

- ✅ **Enhanced Data Models**:

  - Detailed category metadata (colors, icons, descriptions, sort order)
  - Comprehensive application settings with versioning
  - Audit logging for all AI extractions with full traceability
  - Version tracking and user association for future multi-user support
  - Extraction logs with provider, model, and settings snapshots

- ✅ **Authentication & Security**:

  - PBKDF2-SHA256 password hashing with configurable iterations
  - Admin/Guest role-based access control
  - Session state management with secure logout
  - API key management via Streamlit secrets
  - Input sanitization and validation

- ✅ **Robust Error Handling**:
  - Multi-layer validation and error recovery
  - Session state preservation during errors
  - Fallback mechanisms for AI provider failures
  - Database connection resilience with reconnection
  - User-friendly error messages with recovery guidance

### 11. Future Enhancements (Still Out of Scope)

- Analytics dashboard and expense reporting
- Budget tracking and financial planning
- Multi-currency support and conversion
- Multi-user authentication and data isolation
- Receipt OCR and image processing
- Export functionality (CSV, PDF reports)
- Mobile native app development
- API endpoints for third-party integrations
