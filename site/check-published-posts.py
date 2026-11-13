"""Fail closed when an unreviewed post could enter the public site."""

import datetime as dt
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
today = dt.datetime.now(dt.timezone.utc).date()
errors = []
pages = [root / "index.qmd", root / "archive.qmd", root / "methodology.qmd"]
pages += list((root / "projects").glob("*.qmd"))
posts = list((root / "posts").glob("*.qmd"))

for path in pages + posts:
    if path.is_symlink():
        errors.append(f"{path.name}: symlinked site sources are not allowed")
        continue
    text = path.read_text(encoding="utf-8")
    if re.search(r"(?m)^\s*(?:`{3,}|~{3,})\s*\{", text):
        errors.append(f"{path.name}: executable code cells are not allowed")
    if re.search(r"\{\{<\s*include\b", text):
        errors.append(f"{path.name}: include shortcodes are not allowed")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        errors.append(f"{path.name}: missing front matter")
        continue
    header = text[4:].split("\n---\n", 1)[0]
    if re.search(r"(?m)^(execute|engine|filters|resources):", header):
        errors.append(f"{path.name}: execution or resource overrides are not allowed")
    if path not in posts:
        continue
    allowed_keys = {"title", "description", "date", "publication-date", "draft", "categories"}
    for key in re.findall(r"(?m)^([a-zA-Z][\w-]*):", header):
        if key not in allowed_keys:
            errors.append(f"{path.name}: unsupported front matter key {key}")
    fields = {}
    for key in ("title", "date", "publication-date", "draft"):
        values = re.findall(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", header)
        if len(values) != 1:
            errors.append(f"{path.name}: exactly one {key} is required")
        else:
            fields[key] = values[0].strip("\"'")
    if not fields.get("title"):
        errors.append(f"{path.name}: title must not be empty")
    if fields.get("draft") != "false":
        errors.append(f"{path.name}: only explicitly approved non-drafts belong in posts/")
    for key in ("date", "publication-date"):
        try:
            date = dt.date.fromisoformat(fields.get(key, ""))
            if date > today:
                errors.append(f"{path.name}: {key} is in the future")
        except ValueError:
            errors.append(f"{path.name}: {key} must be an ISO date")
    if not re.search(r"https://github\.com/[^/\s)]+/[^/\s)]+/blob/[0-9a-f]{40}/[^\s)]+", text):
        errors.append(f"{path.name}: an exact analysis code revision link is required")

if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)
