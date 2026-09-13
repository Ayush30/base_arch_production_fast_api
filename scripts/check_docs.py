"""Check folder coverage and local Markdown links without external network access."""

import re
from urllib.parse import unquote

from generate_docs import EXCLUDED, ROOT, maintained_files


def main() -> None:
    failures = []
    files = maintained_files()
    for directory in {p.parent for p in files}:
        if directory.name not in EXCLUDED and not (directory / "README.md").exists():
            failures.append(f"Missing folder README: {directory.relative_to(ROOT)}")
    for path in files:
        if path.suffix != ".md":
            continue
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if target.startswith(("http:", "https:", "mailto:", "#")):
                continue
            target = unquote(target.split("#", 1)[0].strip("<>"))
            if not (path.parent / target).exists():
                failures.append(f"Broken link in {path.relative_to(ROOT)}: {target}")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"Documentation checks passed: {sum(p.suffix == '.md' for p in files)} Markdown files")


if __name__ == "__main__":
    main()
