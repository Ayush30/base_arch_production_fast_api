"""The marketplace uses ownership isolation, not seller-specific PostgreSQL schemas."""

if __name__ == "__main__":
    raise SystemExit(
        "Tenant provisioning is disabled for this marketplace. "
        "Sellers register via /auth/register and are approved by an admin. "
        "See docs/DEPLOYMENT.md."
    )
