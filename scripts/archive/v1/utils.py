# scripts/utils.py
# Common utility functions for the Zola-mac project

import re

def slugify(text: str) -> str:
    if not text:
        return "post"
    s = text.strip().lower()
    s = re.sub(r"[^\w\s\-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s[:80] or "post"