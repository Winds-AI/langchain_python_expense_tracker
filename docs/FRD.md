## Functional Requirements Document (FRD)

### 1. Overview

- **Purpose**: Build a minimal Streamlit application to capture expenses in natural language, extract structured data using LangChain with selectable AI providers (OpenAI, Gemini) and its selected model, and persist to MongoDB. Categories and subcategories are user-controlled within the app and must constrain AI classification.- **Primary User**: Single-user personal expense tracking.
- **Platforms**: Streamlit web app, responsive for mobile.

### 2. Goals and Non-Goals

- **Goals**:
  - **Natural language input** to capture expenses with text and voice support.
  - **Voice transcription** using Gemini AI for audio-to-text conversion.
  - **Deterministic classification** into user-defined categories/subcategories only.
  - **Expense management** with full CRUD operations (create, read, update, delete).
  - **Validation**: If required details are missing, show errors and persist the input for quick edits.
  - **Persistence**: Store extracted expense data in MongoDB with audit trails.
  - **Management**: Add/update categories and subcategories via sidebar UI with visual enhancements.
  - **Provider settings**: Choose provider (OpenAI/Gemini) and model with advanced configuration.
  - **Authentication**: Secure admin access with PBKDF2-SHA256 hashing and guest read-only mode.
  - **Debug capabilities**: Advanced debugging with raw AI responses and system monitoring.
  - **Responsive UI** suitable for mobile with PWA support.
- **Non-Goals (Initial)**:
  - Budgeting/analytics/dashboards.
  - Multi-user auth/roles.
  - OCR, receipt uploads.
  - Currency conversion.

### 3. Functional Requirements

- **3.1 Expense Input and Extraction**

  - The main page provides dual input methods: text field for natural language expense entry and voice recording with automatic transcription.
  - **Text Input**: Single text area with Gujlish examples and helpful placeholders.
  - **Voice Input**: Audio recording button with Gemini AI transcription, supporting WebM/Opus/WAV formats.
  - **Transcription Flow**: Audio → Gemini STT → Text area population → Manual review → Extraction.
  - On submit, the app invokes an AI extraction chain that returns:
    - **amount** (required, numeric)
    - **category** (required, must be one of user-defined)
    - **subcategory** (required, must be one of the selected category's subcategories)
    - **description** (required, text from the query)
    - **datetime** (optional; if missing, use current date/time in the user's timezone)
  - If any required field cannot be extracted confidently, the chain returns `valid=false` with `missing_fields` and an explanatory `reason`. The UI shows an error and keeps the user's text in the input for quick editing.
  - On success, the extracted data is shown in a preview and saved to MongoDB with full audit logging.

- **3.1.1 Expense Management (CRUD Operations)**

  - **Read**: Display recent expenses with expandable details and action buttons.
  - **Update**: Edit existing expenses through modal dialogs with form validation.
  - **Delete**: Remove expenses with confirmation dialogs and soft delete options.
  - **Create**: Enhanced expense creation with voice/text input and validation.
  - All operations include audit logging and session state management.

- **3.2 Categories and Subcategories Management**

  - Sidebar section with comprehensive category management:
    - Create categories with name, description, color, and icon
    - Create subcategories with name and description
    - Delete categories and subcategories
    - Visual color picker with curated pastel color palette
    - Real-time validation and duplicate checking
    - Expandable category sections showing subcategory counts
  - Rich category model with:
    - Color coding for visual organization
    - Icon support (emoji/text)
    - Sort ordering for custom arrangement
    - Active/inactive status
    - Full CRUD operations with proper error handling
  - Changes persist to MongoDB and immediately affect AI extraction
  - The complete taxonomy (including descriptions) is injected into AI prompts

- **3.3 Comprehensive Settings Management**

  - **AI Provider Settings**:

    - Select Provider: OpenAI or Gemini with dynamic model loading
    - Model selection with provider-specific validation
    - Advanced AI parameters: temperature (0.0-2.0), max tokens (1-4096)
    - API key validation and configuration guidance

  - **UI Customization Settings**:

    - Theme selection: Light, Dark, Auto
    - Currency format (3-letter codes: USD, EUR, INR, etc.)
    - Date format options: DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD, DD-MM-YYYY
    - Items per page (1-100 for pagination)

  - **Notification Settings**:

    - Enable/disable notifications
    - Sound effects toggle

  - **Privacy & Analytics**:

    - Analytics tracking enable/disable
    - Error reporting enable/disable

  - **System Settings**:

    - Debug mode toggle with detailed logging
    - Log level configuration (DEBUG, INFO, WARNING, ERROR)

  - **Security & Configuration**:
    - API keys managed via Streamlit secrets (.streamlit/secrets.toml)
    - Database connection settings
    - LangSmith tracing integration
    - All settings persisted to MongoDB with versioning

- **3.4 Validation and Feedback**

  - **Input Validation**:

    - Client-side validation for empty input and basic format checking
    - Real-time validation for category and subcategory names (length, characters, uniqueness)
    - Hex color format validation for custom colors
    - Model selection validation against available provider models

  - **AI Response Validation**:

    - Structured JSON response parsing with fallback error handling
    - Validation of required fields (amount, category, subcategory, description)
    - Missing fields detection with specific error messaging
    - Raw response preservation for debugging

  - **User Feedback**:

    - Loading spinners during AI extraction and database operations
    - Success toasts with confirmation messages
    - Error messages with specific field-level feedback
    - Input preservation on validation errors for easy editing
    - Debug panel with raw AI responses, expense/log IDs, and system status

  - **Error Recovery**:
    - Graceful fallback to default categories if database unavailable
    - Retry mechanisms for API failures
    - Session state preservation during errors
    - Clear error messages with actionable guidance

- **3.5 Persistence**

  - **MongoDB Collections**:

    - **Expenses**: Complete expense records with all extracted fields, metadata, and audit trail
    - **Categories**: Rich category model with subcategories, colors, icons, and full metadata
    - **App Settings**: Comprehensive application settings with versioning and user association
    - **Extraction Logs**: Complete audit trail of all AI extraction attempts with raw responses

  - **Data Fields**:

    - Expenses: amount, category, subcategory, description, datetime, provider, model, original_query, created_at
    - Categories: id, name, description, subcategories[], color, icon, is_active, sort_order, created_at, updated_at
    - Settings: Complete settings model with AI, UI, notification, privacy, and system preferences
    - Logs: original_query, provider, model, created_at, settings_snapshot, extraction_result

  - **Database Indexes**:

    - expenses: datetime, category, subcategory, provider, model
    - categories: name, is_active, sort_order
    - settings: user_id, updated_at
    - extraction_logs: created_at, provider, valid

  - **Data Integrity**:
    - Automatic index creation and maintenance
    - Foreign key relationships through category references
    - Audit logging for all extraction attempts
    - Version tracking for settings changes

- **3.6 Responsiveness**
  - Use a single-column layout for mobile.
  - Ensure sidebar navigation is usable on small screens; leverage Streamlit’s responsive layout and minimal custom CSS.

### 4. Non-Functional Requirements

- **Performance**:

  - AI extraction response target: < 3s on average for short inputs (2-3 sentences)
  - Database operations: < 500ms for typical CRUD operations
  - UI responsiveness: Immediate feedback for form interactions
  - Memory efficient: Session state management with selective data loading
  - Optimized queries: Database indexes on frequently accessed fields

- **Reliability**:

  - Graceful degradation when AI provider/model unavailable with fallback options
  - Comprehensive error handling with user-friendly messages
  - Session state preservation during network/API failures
  - Database connection resilience with automatic reconnection
  - Input validation at multiple layers (client, service, database)

- **Usability**:

  - Responsive design suitable for mobile and desktop
  - Intuitive natural language input with helpful placeholder examples
  - Visual feedback with loading states, success/error messages
  - Input preservation on validation errors for seamless editing
  - Color-coded categories with customizable visual themes
  - Expandable sections for organized information display

- **Maintainability**:

  - Modular architecture: `ai`, `db`, `models`, `repositories`, `services`, `ui`, `utils` layers
  - Type-safe development with Pydantic models and comprehensive validation
  - Comprehensive logging with configurable levels (DEBUG, INFO, WARNING, ERROR)
  - Database indexes and constraints for data integrity
  - Version tracking for settings and application updates

- **Security**:
  - API keys managed via Streamlit secrets (.streamlit/secrets.toml)
  - No sensitive data persisted in application database
  - Input sanitization and validation to prevent injection attacks
  - Secure configuration management with environment variable support
  - LangSmith integration for AI call tracing and monitoring

### 5. Data Model (Logical)

- **Expense**

  - amount: number (required)
  - category: string (required)
  - subcategory: string (required)
  - description: string (required)
  - datetime: datetime (required; defaults to now if not provided)
  - provider: string (required)
  - model: string (required)
  - original_query: string (required)
  - created_at: datetime (required)

- **Category**

  - id: string (MongoDB ObjectId)
  - name: string (unique, required, 2-50 chars, alphanumeric + spaces/hyphens/underscores/ampersands)
  - description: string (optional, max 200 chars)
  - subcategories: array<SubcategoryModel> (may be empty)
  - color: string (optional, hex color #RRGGBB)
  - icon: string (optional, max 50 chars, emoji/text)
  - is_active: boolean (default: true)
  - sort_order: integer (default: 0)
  - created_at: datetime
  - updated_at: datetime

- **Subcategory**

  - name: string (required, 1-50 chars, alphanumeric + spaces/hyphens/underscores)
  - description: string (optional, max 200 chars)
  - created_at: datetime
  - updated_at: datetime

- **App Settings**

  - id: string (MongoDB ObjectId)
  - user_id: string (optional, for future multi-user support)

  - **AI Settings**

    - ai_provider: enum{"openai","gemini"} (required)
    - ai_model: string (required, validated against provider)
    - ai_temperature: float (0.0-2.0, default: 0.0)
    - ai_max_tokens: integer (optional, 1-4096)

  - **UI Settings**

    - theme: enum{"light","dark","auto"} (default: "auto")
    - currency: string (3-letter code, default: "INR")
    - date_format: enum{"DD/MM/YYYY","MM/DD/YYYY","YYYY-MM-DD","DD-MM-YYYY"} (default: "DD/MM/YYYY")
    - items_per_page: integer (1-100, default: 10)

  - **Notification Settings**

    - enable_notifications: boolean (default: true)
    - enable_sound: boolean (default: false)

  - **Privacy Settings**

    - enable_analytics: boolean (default: false)
    - enable_error_reporting: boolean (default: true)

  - **System Settings**

    - debug_mode: boolean (default: false)
    - log_level: enum{"DEBUG","INFO","WARNING","ERROR"} (default: "INFO")

  - **Metadata**
    - created_at: datetime
    - updated_at: datetime
    - version: string (default: "1.0.0")

### 6. User Flows

- **6.1 Expense Entry and Save**

  1. User has two input options:
     - **Text Input**: Enters natural language text in the main text area with Gujlish placeholder examples.
     - **Voice Input**: Clicks audio recording button, speaks expense description, clicks "📝 Transcribe" to convert audio to text.
  2. User reviews transcribed/entered text and can edit if needed.
  3. User clicks "🔍 Extract & Save" or uses "🗑️ Clear" to reset.
  4. App validates input (non-empty) and shows loading spinner during processing.
  5. App fetches current categories/subcategories taxonomy from database.
  6. App calls AI extraction chain with current provider/model, taxonomy, and user input.
  7. AI processes the request and returns structured JSON result.
     - If `valid=false`: Shows specific error message with missing fields, preserves user input for editing.
     - If `valid=true`: Displays extraction preview with amount, category, subcategory, description, and datetime.
  8. On success: Saves to MongoDB, shows success toast, clears input, refreshes recent expenses list.
  9. Recent expenses display shows last 5 entries with expandable details and action buttons.

- **6.1.1 Expense Editing and Deletion**

  1. User views recent expenses with "✏️ Edit" and "🗑️ Delete" buttons (Admin only).
  2. **Edit Flow**:
     - User clicks "✏️ Edit" on any expense.
     - Modal dialog opens with pre-populated form fields.
     - User modifies amount, description, category, subcategory, or date/time.
     - User clicks "💾 Save Changes" or "❌ Cancel".
     - On save: Updates database, shows success message, refreshes expense list.
  3. **Delete Flow**:
     - User clicks "🗑️ Delete" on any expense.
     - Confirmation dialog appears with expense details.
     - User clicks "🗑️ Yes, Delete" or "❌ Cancel".
     - On delete: Removes from database, shows success message, refreshes expense list.

- **6.2 Manage Categories/Subcategories**

  1. User expands "📂 Categories" section in sidebar.
  2. **Add Category**: Uses form with name, description, color picker (curated pastels + custom hex), and icon input.
  3. **Add Subcategory**: Within each category expander, uses form to add subcategories with name and description.
  4. **Visual Management**: Categories show with colors, icons, and subcategory counts.
  5. **Delete Operations**: Individual subcategory delete buttons and category delete buttons with confirmation.
  6. **Validation**: Real-time validation prevents duplicates and enforces naming rules.
  7. **Persistence**: All changes immediately saved to MongoDB and affect subsequent AI extractions.

- **6.3 Settings Management**

  1. User expands "⚙️ Settings" section in sidebar.
  2. **AI Provider Settings**: Select provider (OpenAI/Gemini), model from dynamic dropdown, temperature, max tokens.
  3. **UI Settings**: Theme (Light/Dark/Auto), currency format, date format, items per page.
  4. **Notifications**: Enable/disable notifications and sound effects.
  5. **Privacy**: Analytics and error reporting toggles.
  6. **System**: Debug mode toggle and log level selection.
  7. **Save**: Settings persisted to MongoDB with version tracking and immediate application.

### 7. Error Cases and Handling

- **AI Extraction Errors**:

  - Missing required fields (amount/category/subcategory/description) → Display specific error message with missing fields list, preserve user input for editing
  - Invalid JSON response from AI → Fallback error handling with raw response preservation
  - Provider/model unavailable → Graceful degradation with clear error messaging

- **Configuration Errors**:

  - Missing API keys → Settings prompt with configuration guidance for secrets.toml
  - Invalid model selection → Provider-specific validation with available model suggestions
  - Database connection failure → Clear error display with connection status

- **Input Validation Errors**:

  - Empty expense input → Client-side validation prevents submission
  - Invalid category/subcategory names → Real-time validation with character/length requirements
  - Duplicate category names → Immediate feedback with existing category reference
  - Invalid hex color format → Color picker validation with fallback to defaults

- **Network and System Errors**:

  - API rate limits/network failures → Retry mechanisms with exponential backoff
  - MongoDB write failures → Error display, input preservation, manual retry capability
  - Database index creation failures → Graceful fallback with logging

- **Recovery Mechanisms**:
  - Session state preservation during errors
  - Input field restoration for quick editing
  - Fallback to default categories if database unavailable
  - Debug mode for detailed error inspection and troubleshooting

### 8. Dependencies

- **Core Framework**: Streamlit for responsive web UI with session state management
- **AI/ML**: LangChain for LLM orchestration, OpenAI SDK, Google Generative AI SDK
- **Database**: PyMongo/Motor for MongoDB async operations, MongoDB for document storage
- **Data Validation**: Pydantic for type-safe data models and validation
- **Utilities**: python-dotenv for environment management, datetime utilities for timezone handling
- **Development**: pytest for testing, black/flake8 for code formatting and linting

### 9. Acceptance Criteria

- **Natural Language Processing**: Successfully extract structured expense data from sentences like "Lunch 250 at SpiceHub yesterday 1 PM" with accurate amount, category, subcategory, description, and datetime parsing.
- **Error Handling**: When input lacks required fields or fails taxonomy validation, display specific error messages and preserve user input for editing.
- **Category Management**: Rich category/subcategory management with visual color coding, icons, descriptions, and immediate persistence affecting AI extractions.
- **Provider Configuration**: Dynamic AI provider/model selection (OpenAI/Gemini) with advanced parameters (temperature, max tokens) and real-time validation.
- **Settings Management**: Comprehensive application settings including UI themes, currency formats, date formats, notifications, privacy controls, and debug modes.
- **Data Persistence**: Reliable MongoDB storage with automatic indexing, audit logging of all extraction attempts, and version-tracked settings.
- **User Experience**: Responsive design with loading states, success/error feedback, input validation, and debug capabilities for troubleshooting.
- **Debug Features**: Debug mode providing detailed logs, raw AI responses, expense/log IDs, and system status information for development and troubleshooting.
