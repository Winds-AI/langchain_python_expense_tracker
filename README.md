# 💰 Expense Tracker

A minimal Streamlit application for tracking expenses with natural language input and AI-powered data extraction.

## Features

- **Natural Language Input**: Describe your expenses in plain English
- **AI-Powered Extraction**: Automatically extracts amount, category, and subcategory
- **Category Management**: Add and manage custom categories and subcategories
- **Provider Settings**: Choose between OpenAI and Gemini AI providers
- **Responsive UI**: Works well on both desktop and mobile devices
- **Mock Data**: Includes sample data for demonstration

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

2. **Edit `.streamlit/secrets.toml` with your actual API keys:**

   ```toml
   # Add your API keys here (match .streamlit/secrets.toml.sample)
   openai_api_key = "sk-your-actual-openai-key"
   google_api_key = "your-actual-google-key"
   ```

3. **Get API keys:**
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

- "Lunch 250 at SpiceHub yesterday"
- "Bus fare 45 to office this morning"
- "Movie tickets 120 for Avengers"
- "Electricity bill 90 for this month"
- "Coffee and pastry 15.50"
