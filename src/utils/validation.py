# Schema validations

from __future__ import annotations

from typing import Any, Dict, Iterable


REDACTED = "***REDACTED***"


def redact_sensitive_data(data: Dict[str, Any],
                          sensitive_keys: Iterable[str] | None = None) -> Dict[str, Any]:
    """Return a shallow-copied dict with sensitive values masked.

    - Keys are compared case-insensitively.
    - Only top-level keys are considered (snapshots are expected shallow).
    - Missing keys are ignored.
    """
    if not isinstance(data, dict):
        return {}

    default_sensitive = {
        "openai_api_key",
        "google_api_key",
        "langsmith_api_key",
        "mongodb_uri",
        "mongo_uri",
        "db_uri",
        "api_key",
        "apikey",
        "token",
        "access_token",
        "secret",
    }
    keys_to_redact = {k.lower() for k in (sensitive_keys or default_sensitive)}

    redacted: Dict[str, Any] = {}
    for k, v in data.items():
        if k.lower() in keys_to_redact:
            redacted[k] = REDACTED
        else:
            redacted[k] = v
    return redacted

