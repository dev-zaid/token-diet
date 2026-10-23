"""Day 1, Step 4, Method B (AI): the local model reads the page text and fills a FactCard."""

import sys

import httpx

from count_tokens import MODEL, OLLAMA, html_to_text
from method_a import DATA, FactCard

# TODO(human): the model's instructions. What to extract, and what to do when a fact isn't on the page.
SYSTEM = """Fill the product card from the page text. Rules:
1. name: Only products name, no size, color or variant information. This goes straight to the variant data. Example: "Cropped Tshirt - Loose Fit - Blue" -> "Cropped Tshirt"
2. variants: Variant name must only contain the additional variant name and not the Product or Product Group Name again. Example: \"Classic Mug - Ocean Blue\" → \"Ocean Blue\".
3. price: the price next to the currency icon, as a plain number. Example: ₹ 1,250 -> 1250. State the selling price not the MRP. Example: ₹1,250 ₹1,999 -> 1250
4. currency: Use currency as a code. Example: Indian Ruppee -> INR, US Dollars -> USD
5. shipping: delivery time or cost only, under 10 words
6. returns: return window only, under 10 words

If a fact is not in the text, leave the field null
"""


def method_b(html: str) -> tuple[FactCard | None, int, int]:
    """Send clean text to the local model; get back a FactCard (None if it ran away) plus (input, output) token counts."""
    r = httpx.post(
        f"{OLLAMA}/api/chat",
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": html_to_text(html)},  # plain text, never raw HTML
            ],
            "format": FactCard.model_json_schema(),  # the model can only write JSON in this shape
            "think": False,  # no hidden reasoning: fewer output tokens, faster
            "stream": False,
            "options": {"temperature": 0, "num_predict": 2048},  # same page in, same card out; stop a runaway at 2048 tokens
        },
        timeout=300,  # ~10 s to read the page, plus writing time; long variant lists take longer
    )
    r.raise_for_status()
    body = r.json()
    # "length" = hit num_predict mid-JSON: no card, but the tokens were still spent
    card = FactCard.model_validate_json(body["message"]["content"]) if body["done_reason"] == "stop" else None
    return card, body["prompt_eval_count"], body["eval_count"]


if __name__ == "__main__":
    pattern = sys.argv[1] if len(sys.argv) > 1 else "*/*"  # e.g. "mokobara.com/the-memo*" for one page
    for path in sorted(DATA.glob(f"{pattern}.html")):  # .html only: the .json next to it is the answer key
        card, tokens_in, tokens_out = method_b(path.read_text())
        print(f"{path.parent.name}/{path.stem}"[:48], tokens_in, tokens_out, card.model_dump_json(exclude_none=True) if card else None)
