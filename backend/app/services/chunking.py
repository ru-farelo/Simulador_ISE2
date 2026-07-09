import re


def chunk_paragraphs(text: str, min_chars: int = 200, max_chars: int = 900) -> list[str]:
    """Split text into paragraph-based chunks, merging short paragraphs and
    splitting oversized ones on sentence boundaries — never a fixed
    character-count slice, so a chunk always ends at a natural boundary.
    """
    raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: list[str] = []
    buffer = ""
    for para in raw_paragraphs:
        if len(para) > max_chars:
            if buffer:
                chunks.append(buffer)
                buffer = ""
            chunks.extend(_split_long_paragraph(para, max_chars))
            continue

        candidate = f"{buffer}\n\n{para}" if buffer else para
        if len(candidate) <= max_chars:
            buffer = candidate
        else:
            if buffer:
                chunks.append(buffer)
            buffer = para
    if buffer:
        chunks.append(buffer)

    merged: list[str] = []
    for chunk in chunks:
        if merged and len(chunk) < min_chars:
            merged[-1] = f"{merged[-1]}\n\n{chunk}"
        else:
            merged.append(chunk)
    return merged


def _split_long_paragraph(paragraph: str, max_chars: int) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    chunks, buffer = [], ""
    for sentence in sentences:
        candidate = f"{buffer} {sentence}".strip()
        if len(candidate) <= max_chars:
            buffer = candidate
        else:
            if buffer:
                chunks.append(buffer)
            buffer = sentence
    if buffer:
        chunks.append(buffer)
    return chunks
