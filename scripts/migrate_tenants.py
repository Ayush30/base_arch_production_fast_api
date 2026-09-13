"""Use the single marketplace migration chain instead of per-seller migrations."""

if __name__ == "__main__":
    raise SystemExit(
        "Use `uv run alembic upgrade head` for the shared marketplace schema. "
        "See docs/DEPLOYMENT.md."
    )
