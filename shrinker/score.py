"""Day 1, Step 5: score each method's FactCard against the answer key."""

import json
from pathlib import Path

from count_tokens import count, html_to_text
from method_a import DATA, FactCard, method_a
from method_b import method_b

PRICE_IN, PRICE_OUT = 0.15, 0.60  # USD per 1M tokens: an assumed cheap-API reference price (ours runs free, locally)


def load_key(html_path: Path) -> dict:
    """The answer key saved next to the page: /products/<handle>.json."""
    return json.loads(html_path.with_suffix(".json").read_text())["product"]


def price_score(card: FactCard | None, key: dict) -> float:
    """Share of the store's variants whose price is on the card. Names ignored, so one
    right price covers every variant at that price."""
    if card is None:
        return 0.0  # no card = nothing right
    card_prices = {v.price for v in card.variants if v.price is not None}
    hits = sum(float(v["price"]) in card_prices for v in key["variants"])  # key prices are strings: "3799.00"
    return hits / len(key["variants"])


def variant_score(card: FactCard | None, key: dict) -> float:
    """Share of the store's variants whose name is on the card."""
    if card is None:
        return 0.0

    card_variants = {v.name.strip().casefold() for v in card.variants if v.name is not None}
    hits = sum(v["title"].strip().casefold() in card_variants for v in key["variants"])

    return hits / len(key["variants"])


def cost(tokens_in: int, tokens_out: int) -> float:
    """What these tokens would cost through a paid API, in USD."""
    return (tokens_in * PRICE_IN + tokens_out * PRICE_OUT) / 1_000_000


def card_tokens(card: FactCard) -> int:
    """Tokens an agent reads for this card (vs. the plain page text without the diet)."""
    return count(card.model_dump_json(exclude_none=True))


if __name__ == "__main__":
    rows = []
    print(f"{'page':<40} {'A price':>8} {'A var':>6} {'B price':>8} {'B var':>6} {'B in':>7} {'B out':>6} {'text':>6} {'A read':>6} {'B read':>6}")
    for path in sorted(DATA.glob("*/*.html")):
        html, key = path.read_text(), load_key(path)
        a = method_a(html)
        b, b_in, b_out = method_b(html)  # ~10 s per page: the whole run takes ~3 min
        text = count(html_to_text(html))  # what the agent reads with no diet
        a_read = card_tokens(a) if a else text  # no card -> the agent falls back to the page text
        b_read = card_tokens(b) if b else text
        row = (price_score(a, key), variant_score(a, key), price_score(b, key), variant_score(b, key), b_in, b_out, text, a_read, b_read)
        rows.append(row)
        print(f"{path.parent.name}/{path.stem}"[:40].ljust(40), "{:>8.0%} {:>6.0%} {:>8.0%} {:>6.0%} {:>7,} {:>6,} {:>6,} {:>6,} {:>6,}".format(*row))
    a_p, a_v, b_p, b_v, b_in, b_out, text, a_read, b_read = zip(*rows)
    n = len(rows)
    print(f"{'MEAN / TOTAL':<40} {sum(a_p) / n:>8.0%} {sum(a_v) / n:>6.0%} {sum(b_p) / n:>8.0%} {sum(b_v) / n:>6.0%} {sum(b_in):>7,} {sum(b_out):>6,} {sum(text):>6,} {sum(a_read):>6,} {sum(b_read):>6,}")
    print(f"Make the cards: Method B ${cost(sum(b_in), sum(b_out)) / n * 1000:.2f} per 1,000 pages. Method A $0.")
    print(f"Agent reads: page text {sum(text):,} -> A cards {sum(a_read):,} ({1 - sum(a_read) / sum(text):.0%} less), B cards {sum(b_read):,} ({1 - sum(b_read) / sum(text):.0%} less)")
