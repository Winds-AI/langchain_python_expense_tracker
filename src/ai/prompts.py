"""
Prompt templates for expense extraction.
"""

from __future__ import annotations

from langchain_core.prompts import PromptTemplate


EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["text", "now_iso", "categories_block"],
    template=(
        "You are a careful information extractor. Extract expense info from Gujlish (Gujarati+English, incl. WhatsApp-style slang). Keep description exactly as written.\n\n"
        "Current time (IST, ISO8601 with timezone): {now_iso}. Use this to resolve relative words like 'today/yesterday/tomorrow' and Gujarati words like 'aaje' (today) and 'kaale' (yesterday or tomorrow based on context). If ambiguous, assume 'kaale' means the most recent past unless the text clearly indicates future.\n\n"
        "Allowed categories and subcategories (choose only from these; pick the closest match):\n"
        "{categories_block}\n\n"
        "Extraction rules:\n"
        "- amount: numeric value only. Recognize 'rs', 'rupiya', 'rupees', '₹', and patterns like '20rs', '20 rs', '₹20', '20 rupiya', '20 na'.\n"
        "- Gujarati snack terms map to subcategory 'Snacks' under 'Food' when appropriate (e.g., 'padika/padikaa/padika', 'nashto', 'farsan/farshan', 'fafda', 'gathiya').\n"
        "- description: ORIGINAL TEXT EXACTLY AS WRITTEN (no translation).\n"
        "- datetime: Return ISO8601 string with timezone if present in text; if not specified, use current IST time. If text includes relative time, resolve using the provided current time.\n"
        "- category/subcategory: choose exactly one each from the allowed lists. If none fits, set null and add the field name to missing_fields.\n"
        "- Only return JSON. No extra text, no code fences.\n\n"
        "Output JSON schema:\n"
        "{{\"valid\": boolean, \"amount\": number|null, \"category\": string|null, \"subcategory\": string|null, \"description\": string, \"datetime\": string, \"missing_fields\": []}}\n\n"
        "Examples:\n"
        "Input: '20rs na padika' -> {{\"valid\": true, \"amount\": 20, \"category\": \"Food\", \"subcategory\": \"Snacks\", \"description\": \"20rs na padika\", \"datetime\": \"{now_iso}\", \"missing_fields\": []}}\n"
        "Input: 'kaale bus ma 15 rupiya' -> amount 15, category 'Transportation', subcategory 'Bus', datetime resolved to yesterday based on current time.\n\n"
        "Input: {text}"
    ),
)

