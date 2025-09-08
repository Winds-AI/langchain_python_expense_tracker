## UI/UX Plan ✅

### Design Principles

- **Mobile-First Responsive**: Two-column layout that gracefully adapts to mobile with stacked columns
- **Rich Visual Design**: Color-coded categories with icons and custom color picker
- **Error Recovery**: Input preservation on errors with clear validation feedback
- **Progressive Enhancement**: Debug mode and advanced features for power users
- **Cultural Adaptation**: Gujlish-friendly interface with appropriate examples
- **Accessibility**: Semantic HTML, keyboard navigation, and screen reader support

### Information Architecture

- **Main Content Area**:

  - Natural language expense input with Gujlish examples
  - Real-time extraction results with preview
  - Recent expenses display with expandable details
  - Success/error feedback with contextual messages

- **Comprehensive Sidebar**:
  - **Categories Management**: Rich category CRUD with colors and icons
  - **Settings Hub**: Multi-section settings (AI, UI, notifications, privacy, system)
  - **Debug Panel**: System status and detailed logging
  - **Database Status**: Connection monitoring and health indicators

### Main Page Layout ✅

- **Header Section**:

  - App title with emoji icon: "💰 Expense Tracker"
  - Subtitle: Natural language expense tracking with AI extraction
  - User role indicator: "Admin" or "Guest (read-only)"

- **Expense Input Form** (Admin Only):

  - **Voice Input Row**: Two-column layout for audio recording and text area

    - Left column: Audio input button with recording status and transcribe button
    - Right column: Large multi-line text area (height: 100px) with helpful Gujlish placeholder
    - Example: "e.g., 20rs na padika, or Bus fare 45 to office yesterday"
    - Voice transcription with Gemini AI integration
    - Inline controls: "📝 Transcribe" and "❌ Clear Voice" buttons

  - **Action Row**: Two-column layout for main actions

    - Primary button: "🔍 Extract & Save" (full-width, primary style)
    - Secondary button: "🗑️ Clear" (outlined style)

  - **Guest Mode**: Read-only message when not logged in as admin

- **Extraction Results Display**:

  - Success state: Formatted preview with amount metric and field cards
  - Error state: Clear error messages with missing fields highlighted
  - Debug mode: Expandable panel with raw AI responses and metadata
  - Field display: Amount (prominent metric), Category/Subcategory, Description, IST datetime

- **Recent Expenses Section**:
  - Header: "Recent Expenses"
  - Last 5 expenses as expandable cards with action buttons
  - Each card shows: amount, description, category, datetime, provider
  - **Action Buttons** (Admin only):
    - "✏️ Edit" button to modify expense details
    - "🗑️ Delete" button with confirmation dialog
  - **Edit Dialog**: Modal form for updating expense fields (amount, description, category, subcategory, date/time)
  - **Delete Confirmation**: Warning dialog with expense details and confirmation buttons
  - Empty state: Encouraging message when no expenses exist

### Sidebar: Categories Manager ✅

- **Visual Design**: Color-coded categories with icons and expandable sections
- **Add Category Form**:

  - Category name input with validation
  - Custom color picker with curated pastel palette (15 trendy colors + custom hex)
  - Icon selection (emoji/text input)
  - Real-time validation and duplicate prevention

- **Category Management**:

  - Expandable sections showing subcategory counts
  - Visual color swatches and icons for each category
  - Edit and delete actions per category
  - Success/error feedback for all operations

- **Subcategory Management**:
  - Add subcategory forms within each category section
  - Individual delete buttons for each subcategory
  - Validation and duplicate checking
  - Hierarchical relationship visualization

### Sidebar: Settings Hub ✅

- **AI Provider Settings**:

  - Provider selection (OpenAI/Gemini) with dynamic model loading
  - Model dropdown populated based on selected provider
  - Advanced parameters: temperature slider, max tokens input
  - API key configuration guidance

- **UI Customization**:

  - Theme selection (Light/Dark/Auto)
  - Currency format selection
  - Date format options
  - Items per page configuration

- **Notifications & Privacy**:

  - Notification enable/disable toggles
  - Sound effects toggle
  - Analytics tracking controls
  - Error reporting settings

- **System Settings**:
  - Debug mode toggle with detailed logging
  - Log level configuration (DEBUG, INFO, WARNING, ERROR)
  - System status indicators
  - **Debug Panel**: Expandable section with:
    - Database connection status and health monitoring
    - MongoDB index creation status
    - LangSmith tracing status (enabled/disabled)
    - Raw AI response preservation for troubleshooting
    - Expense and log IDs for traceability
    - System performance metrics

### Authentication & Security ✅

- **Access Gate**: Initial authentication screen with Admin/Guest options
- **Admin Authentication**: PBKDF2-SHA256 password hashing with salt and iterations
- **Guest Mode**: Read-only access for demonstration and viewing
- **Session Management**: Secure session state with logout functionality
- **Role-Based UI**: Dynamic interface changes based on admin/guest permissions

### Progressive Web App Features ✅

- **Service Worker**: Background processing for offline capabilities
- **Web App Manifest**: Installation support with app icons and metadata
- **Theme Color**: Dynamic theming support with meta theme-color
- **Responsive Design**: Mobile-first approach with touch-friendly controls
- **PWA Registration**: Automatic service worker registration and updates

### Feedback & States ✅

- **Loading States**: Spinner animations during AI extraction, transcription, and database operations
- **Success Feedback**: Green success toasts with confirmation messages and automatic clearing
- **Error Handling**: Red error displays with specific field-level feedback and input preservation
- **Validation Messages**: Real-time validation with helpful error messages and recovery suggestions
- **Debug Information**: Expandable debug panels with raw responses and system details
- **Voice Processing**: Loading indicators during audio transcription with Gemini

### Responsiveness & Mobile Experience ✅

- **Adaptive Layout**: Two-column desktop layout that gracefully stacks on mobile
- **Touch-Friendly**: Large buttons (44px+ touch targets) and comfortable spacing
- **Mobile Optimization**: Full-width buttons, readable text sizes, thumb-friendly interactions
- **Progressive Enhancement**: Core features work on all screen sizes

### Accessibility Features ✅

- **Semantic HTML**: Proper heading hierarchy and ARIA labels
- **Keyboard Navigation**: Full keyboard support with logical tab order
- **Color Contrast**: WCAG-compliant contrast ratios
- **Screen Reader Support**: Descriptive labels and status announcements
- **Focus Management**: Clear focus indicators and logical navigation flow

### Advanced Features ✅

- **Color Picker Component**: Interactive color selection with 15 curated pastels + custom hex input
- **Debug Mode**: Comprehensive debugging with raw AI responses, system status, and performance metrics
- **Multi-Language Support**: Gujlish-friendly interface with culturally appropriate examples
- **Rich Category Visualization**: Color-coded categories with icons and visual hierarchy
- **Comprehensive Settings**: Multi-section settings with immediate feedback and validation

### Copy Guidelines & Microcopy ✅

- **Action-Oriented Labels**: "🔍 Extract & Save", "🗑️ Clear", "Add Category"
- **Helpful Placeholders**: Gujlish examples like "20rs na padika" and "kaale bus ma 15 rupiya"
- **Error Messages**: Specific, actionable error messages with recovery guidance
- **Success Confirmations**: Clear success messages with next action suggestions
- **Empty States**: Encouraging messages that guide users to take action

### Performance & User Experience ✅

- **Immediate Feedback**: Sub-second response times for UI interactions
- **Progressive Loading**: Content loads as needed to maintain responsiveness
- **Error Recovery**: Seamless recovery from errors without losing user context
- **Session Persistence**: User input and preferences maintained across interactions
- **Intuitive Workflows**: Logical flow from input to confirmation with clear next steps
