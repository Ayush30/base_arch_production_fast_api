from __future__ import annotations


class HealthMsg:
    """Message keys for health endpoints."""

    OK = "health.ok"
    UNAVAILABLE = "health.unavailable"
    DETAIL_DB = "health.detail_db"


class SecurityMsg:
    """Message keys for generic security / token errors."""

    TOKEN_INVALID = "security.token_invalid"
    TENANT_MISSING = "security.tenant_missing"
    TOKEN_CLAIMS_MALFORMED = "security.token_claims_malformed"


class ExampleMsg:
    """Message keys for the reference example domain."""

    NOT_FOUND = "example.not_found"
    VERSION_MISMATCH = "example.version_mismatch"
