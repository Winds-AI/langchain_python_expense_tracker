## AI Data Extraction Plan (LangChain)

### Objectives

- Extract structured fields from a single natural language input:
  - amount (required, number)
  - category (required; must be in categories list)
  - subcategory (required; must be in selected category's subcategories)
  - description (required, text)
  - datetime (optional; default to now if absent)
- Enforce taxonomy (no hallucinated categories/subcategories).
- Return `valid=false` with `missing_fields` and `reason` when extraction incomplete.

### Provider Abstraction ✅

- **Supported Providers**: OpenAI, Google Gemini
- **Configuration**: Dynamic provider/model selection from settings; temperature=0 for deterministic output
- **LangChain Integration**:
  - OpenAI: `langchain-openai` ChatOpenAI with API key validation
  - Gemini: `langchain-google-genai` ChatGoogleGenerativeAI with API key validation
- **LangSmith Tracing**: Optional integration for AI call monitoring and debugging
- **Available Models**:
  - OpenAI: gpt-3.5-turbo, gpt-4, gpt-4-turbo, gpt-4o, gpt-4o-mini, gpt-5-mini
  - Gemini: gemini-pro, gemini-pro-vision, gemini-1.5-flash, gemini-1.5-pro

### Structured Output Strategy

- Prefer `with_structured_output(pydantic_model)` when supported; fallback to robust JSON parsing via `PydanticOutputParser` or `StructuredOutputParser` with format instructions.
- Pydantic schema `ExtractionResult`:
  - valid: bool
  - missing_fields: list[str]
  - reason: str | None
  - amount: float | None
  - category: str | None
  - subcategory: str | None
  - description: str | None
  - datetime: str | None (ISO 8601)

### Prompt Design ✅

- **Multi-Language Support**: Gujlish (Gujarati+English) and Hindi-English code-switching
- **System Instructions**:

  - Careful information extractor specialized in Gujlish expense descriptions
  - Preserve original text exactly (no translation) for description field
  - Gujarati snack terms mapping to appropriate subcategories
  - Strict taxonomy enforcement - only use provided categories/subcategories
  - Return `valid=false` with specific missing fields when extraction incomplete

- **Dynamic Taxonomy Injection**:

  - Real-time category and subcategory lists from database
  - Formatted as readable bullet points for each category
  - Automatic fallback to default categories if database unavailable

- **Advanced Extraction Rules**:

  - Amount recognition: 'rs', 'rupiya', 'rupees', '₹', 'na' patterns
  - Gujarati time terms: 'aaje' (today), 'kaale' (yesterday/tomorrow context)
  - Relative time resolution using current IST timestamp
  - Exact description preservation for cultural context

- **Few-Shot Examples**:
  - Gujlish expense examples: '20rs na padika', 'kaale bus ma 15 rupiya'
  - Successful extraction demonstrations
  - Error case demonstrations with proper missing_fields handling

### Validation & Post-Processing ✅

- **Taxonomy Enforcement**: Strict validation against database categories/subcategories
- **Datetime Processing**: IST timezone handling with Gujarati relative terms support
- **Amount Validation**: Float conversion with negative amount rejection
- **Error Propagation**: Structured error reporting with missing_fields and reasons
- **Fallback Mechanisms**: Default categories when database unavailable

### Date/Time Handling ✅

- **Timezone Support**: Indian Standard Time (IST) as primary timezone
- **Gujarati Terms**: 'aaje' (today), 'kaale' (yesterday/tomorrow based on context)
- **Relative Resolution**: Dynamic resolution using current IST timestamp
- **ISO 8601 Output**: Consistent datetime formatting with timezone information
- **Fallback Strategy**: Current time default when datetime cannot be determined

### Error Handling ✅

- **Provider Validation**: API key verification before AI calls
- **Network Resilience**: Automatic retry mechanisms for transient failures
- **Structured Errors**: Clear differentiation between configuration and runtime errors
- **Graceful Degradation**: Fallback to default responses when AI unavailable
- **User Feedback**: Specific error messages for different failure scenarios

### Observability & Logging ✅

- **Comprehensive Audit Trail**: Every extraction attempt logged with full context
- **LangSmith Integration**: Optional AI call tracing and performance monitoring
- **Raw Response Preservation**: Complete AI responses stored for debugging
- **Performance Metrics**: Provider, model, and latency tracking
- **Debug Information**: Extraction snapshots and settings preservation

### Security & Determinism ✅

- **Temperature Control**: Fixed at 0.0 for consistent, deterministic outputs
- **Schema Enforcement**: Strict JSON output validation with fallback parsing
- **Input Sanitization**: Safe prompt construction with taxonomy injection
- **Uncertainty Handling**: Explicit instruction to return `valid=false` rather than guessing
- **Output Length Limits**: Controlled response sizes for consistent processing

### Current Implementation Status ✅

- **Fully Implemented**: All core extraction features working
- **Multi-Provider Support**: OpenAI and Gemini with seamless switching
- **Cultural Adaptation**: Gujlish and Hindi-English support for Indian users
- **Production Ready**: Comprehensive error handling and logging
- **Debug Capabilities**: Full transparency with raw response preservation

### Advanced Features Implemented ✅

- **Dynamic Taxonomy**: Real-time category updates affect extraction immediately
- **Audit Trail**: Complete logging of all extraction attempts with full context
- **Performance Monitoring**: LangSmith integration for AI call analysis
- **Timezone Intelligence**: IST-focused datetime handling with Gujarati terms
- **Fallback Resilience**: Graceful degradation when services unavailable

### Example Outputs

**Successful Gujlish Extraction:**

```json
{
  "valid": true,
  "amount": 20.0,
  "category": "Food",
  "subcategory": "Snacks",
  "description": "20rs na padika",
  "datetime": "2024-01-15T14:30:00+05:30",
  "missing_fields": []
}
```

**Error Case with Missing Fields:**

```json
{
  "valid": false,
  "amount": null,
  "category": null,
  "subcategory": null,
  "description": "some random text",
  "datetime": "2024-01-15T14:30:00+05:30",
  "missing_fields": ["amount", "category", "subcategory"],
  "error": "Could not extract required expense information"
}
```
