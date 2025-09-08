# 💰 Expense Tracker

A minimal Streamlit application for tracking expenses with natural language input and AI-powered data extraction.

## Features

- **Natural Language Input**: Describe your expenses in plain English
- **Voice Input & Transcription**: Record audio and automatically transcribe to text using Gemini
- **AI-Powered Extraction**: Automatically extracts amount, category, and subcategory using OpenAI or Gemini
- **Category Management**: Add and manage custom categories and subcategories with colors and icons
- **Expense Management**: Edit and delete existing expenses with full CRUD operations
- **Provider Settings**: Choose between OpenAI and Gemini AI providers with model selection
- **Secure Access Gate**: Admin login with PBKDF2-SHA256 password hashing; Guest read-only mode
- **Debug Mode**: Advanced debugging with raw AI responses, system status, and detailed logging
- **Responsive UI**: Works well on both desktop and mobile devices with touch-friendly controls
- **Audit Trail**: Complete logging of all AI extraction attempts with full traceability
- **Color Picker**: Curated pastel color palette for visual category organization
- **PWA Support**: Progressive Web App features with service worker and manifest

## Quick Start

### Prerequisites

- Python 3.8 or higher

### Setup Instructions

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**

   ```bash
   streamlit run app.py
   ```

3. **Open your browser** to `http://localhost:8501`

### Configuration (Optional)

Before using AI features, configure your API keys:

1. **Copy the example file:**

   **Unix/Linux/macOS:**

   ```bash
   mkdir -p .streamlit
   cp .streamlit/secrets.toml.sample .streamlit/secrets.toml
   ```

   **Windows PowerShell:**

   ```powershell
   New-Item -ItemType Directory -Force -Path .streamlit
   Copy-Item .streamlit/secrets.toml.sample .streamlit/secrets.toml
   ```

2. **Edit `.streamlit/secrets.toml` with your actual API keys:**

   ```toml
   # Add your API keys here (match .streamlit/secrets.toml.sample)
   openai_api_key = "sk-your-actual-openai-key"
   google_api_key = "your-actual-google-key"
   ```

### Admin Authentication

To restrict interactions to Admin only and allow Guests to view-only, configure an admin password using PBKDF2-SHA256.

1. Generate a random salt (16–32 bytes) and compute the hash using the same salt and iterations (default 200000). For example, in Python:

```python
import os, hashlib
password = input('Enter admin password: ').encode('utf-8')
salt = os.urandom(16)
iterations = 200_000
derived = hashlib.pbkdf2_hmac('sha256', password, salt, iterations)
print('admin_password_salt =', salt.hex())
print('admin_password_hash =', derived.hex())
print('admin_password_iterations =', iterations)
```

2. Add these to `.streamlit/secrets.toml`:

```toml
# Admin Authentication
admin_password_salt = "<hex-salt>"
admin_password_hash = "<hex-hash>"
# Optional (default 200000)
admin_password_iterations = 200000
```

3. Start the app. You will see a gate with options:

   - Login as Admin (enter the password)
   - Continue as Guest (read-only)

4. **Get API keys:**
   - **OpenAI**: Visit [OpenAI API](https://platform.openai.com/api-keys)
   - **Google**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)

### Virtual Environment (Optional)

**Create venv (first time only):**

```bash
python -m venv venv
```

**Activate venv (every time you work on project):**

```bash
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

**Deactivate when done:**

```bash
deactivate
```

**List virtual environments:**

```bash
# Windows:
dir venv*

# macOS/Linux:
ls -la venv*
```

## Sample Expense Inputs

Try these examples:

### Text Input Examples

- "Lunch 250 at SpiceHub yesterday"
- "Bus fare 45 to office this morning"
- "Movie tickets 120 for Avengers"
- "Electricity bill 90 for this month"
- "Coffee and pastry 15.50"

### Voice Input Examples

You can also record audio and the app will transcribe it automatically:

- "Spent 250 rupees on lunch at SpiceHub yesterday afternoon"
- "Paid 45 rupees for bus fare to office this morning"
- "Bought movie tickets worth 120 rupees for Avengers"
- "Electricity bill came for 90 rupees this month"
- "Had coffee and pastry for 15 rupees 50 paise"

### Gujlish Examples

The app supports Gujarati-English mixing:

- "20rs na padika" (20 rupees worth of snacks)
- "kaale bus ma 15 rupiya" (15 rupees for bus yesterday)
- "lunch 250 SpiceHub ma" (250 rupees lunch at SpiceHub)
