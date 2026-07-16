"""Shared helpers for scripts/services that ask Claude to generate one
output entry per item in a batch (vocab flashcards, grammar prompts,
filler openers...). Two problems this fixes centrally, after the third
script broke the same way:

1. A fixed max_tokens constant doesn't scale with batch size, so a batch
   large enough eventually gets truncated (anthropic_client.py now raises
   a clear AIServiceError for this instead of returning a bogus empty
   dict, but that alone just turns a KeyError into a different crash).
2. There was no recovery — one bad batch failed the whole run. Now a
   truncated batch is automatically retried as two smaller half-batches,
   recursively down to MIN_BATCH_SIZE, so a single oversized batch
   degrades to more (cheaper, safer) calls instead of failing outright.
"""

from collections.abc import Callable
from typing import Any

from app.services.anthropic_client import AIServiceError

MIN_BATCH_SIZE = 5


def tokens_for_batch(item_count: int, per_item: int = 200, overhead: int = 500, cap: int = 8000) -> int:
    """A generous, proportional token budget for a batch of `item_count`
    entries. `per_item` should reflect roughly how verbose each output
    entry is (short word/translation/example triples fit comfortably in
    150-200 tokens each; longer generated sentences may need more).
    """
    return min(cap, item_count * per_item + overhead)


def generate_with_retry(
    batch: list[Any], generate_fn: Callable[[list[Any]], dict], label: str = "batch"
) -> dict | None:
    """Calls generate_fn(batch) — expected to internally call
    structured_completion with max_tokens=tokens_for_batch(len(batch)).
    If Claude's response was truncated, the batch is split in half and
    each half is retried (recursively), then the two partial results are
    merged. Returns None (after printing a clear message) if even a
    MIN_BATCH_SIZE batch still fails — callers should treat that as "this
    batch produced nothing", never as a KeyError.
    """
    try:
        return generate_fn(batch)
    except AIServiceError as exc:
        if len(batch) <= MIN_BATCH_SIZE:
            print(f"  ERROR  {label}: respuesta incompleta incluso con lote minimo de {len(batch)}: {exc}")
            return None

        mid = len(batch) // 2
        print(
            f"  AVISO  {label}: respuesta incompleta con lote de {len(batch)} "
            f"({exc}) — reintentando en dos lotes de ~{mid}"
        )
        first = generate_with_retry(batch[:mid], generate_fn, label)
        second = generate_with_retry(batch[mid:], generate_fn, label)
        return _merge(first, second)


def _merge(a: dict | None, b: dict | None) -> dict | None:
    if a is None:
        return b
    if b is None:
        return a
    merged = dict(a)
    for key, value in b.items():
        if isinstance(value, list) and isinstance(merged.get(key), list):
            merged[key] = merged[key] + value
        else:
            merged[key] = value
    return merged
