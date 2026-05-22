import re
from typing import List

MAX_TOKENS_PER_CHUNK = 3000
CHARACTERS_PER_TOKEN = 4
MAX_CHARS_PER_CHUNK = MAX_TOKENS_PER_CHUNK * CHARACTERS_PER_TOKEN


def _split_into_sentences(paragraph: str) -> List[str]:
    tokens = re.split(r"(?<=[\.\!\?؟])\s+", paragraph.strip())
    return [sentence.strip() for sentence in tokens if sentence.strip()]


def chunk_text(text: str) -> List[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_length = 0

    def flush_chunk() -> None:
        nonlocal current_chunk, current_length
        if current_chunk:
            chunks.append("\n\n".join(current_chunk).strip())
            current_chunk = []
            current_length = 0

    for paragraph in paragraphs:
        paragraph_length = len(paragraph)
        if current_length + paragraph_length <= MAX_CHARS_PER_CHUNK:
            current_chunk.append(paragraph)
            current_length += paragraph_length
            continue

        if paragraph_length <= MAX_CHARS_PER_CHUNK:
            flush_chunk()
            current_chunk.append(paragraph)
            current_length = paragraph_length
            continue

        sentences = _split_into_sentences(paragraph)
        for sentence in sentences:
            sentence_length = len(sentence)
            if current_length + sentence_length <= MAX_CHARS_PER_CHUNK:
                current_chunk.append(sentence)
                current_length += sentence_length
                continue

            flush_chunk()
            if sentence_length <= MAX_CHARS_PER_CHUNK:
                current_chunk.append(sentence)
                current_length = sentence_length
            else:
                for i in range(0, len(sentence), MAX_CHARS_PER_CHUNK):
                    part = sentence[i : i + MAX_CHARS_PER_CHUNK].strip()
                    if part:
                        chunks.append(part)
                current_chunk = []
                current_length = 0

    flush_chunk()
    return chunks
