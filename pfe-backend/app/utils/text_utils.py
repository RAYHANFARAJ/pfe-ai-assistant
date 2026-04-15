import re
from typing import Optional


def normalize_text(value: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def strip_html(value: Optional[str]) -> str:
    text = value or ""
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return normalize_text(text)


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "unknown"
