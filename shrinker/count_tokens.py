"""Day 1, Step 2: how many tokens is a product page? Raw HTML vs plain text."""

from pathlib import Path

import httpx
import tiktoken
from bs4 import BeautifulSoup

DATA = Path(__file__).resolve().parent.parent / "data"
ENC = tiktoken.get_encoding("o200k_base")  # GPT-4o's tokenizer: an estimate, not our model's
OLLAMA = "http://localhost:11434"
MODEL = "spark-local"  # 4.1B, Q8_0, num_ctx 32768 (see `ollama show spark-local`)


def html_to_text(html: str) -> str:
    """Roughly what a shopper sees: no tags, scripts or styles."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "template"]):
        tag.decompose()  # drop the tag and everything inside it
    return soup.get_text(" ", strip=True)  # " " keeps words from gluing together


def count(text: str) -> int:
    # disallowed_special=(): a page may literally contain "<|endoftext|>"; count it as text
    return len(ENC.encode(text, disallowed_special=()))


def model_tokens(text: str) -> int:
    """Input tokens the local model reports for this text (Ollama's prompt_eval_count)."""
    r = httpx.post(f"{OLLAMA}/api/generate", json={"model": MODEL, "prompt": text, "raw": True, "stream": False, "options": {"num_predict": 1}}, timeout=120)
    r.raise_for_status()
    return r.json()["prompt_eval_count"]


if __name__ == "__main__":
    rows = []
    for path in sorted(DATA.glob("*/*.html")):
        html = path.read_text()
        text = html_to_text(html)
        rows.append((f"{path.parent.name}/{path.stem}"[:48], len(html), count(html), len(text), count(text), model_tokens(text)))

    print(f"{'page':<48} {'html tok':>9} {'text tok':>9} {'saved':>6} {'html c/t':>9} {'text c/t':>9} {'model tok':>9} {'tik error':>9}")
    for name, hc, ht, tc, tt, mt in rows:
        print(f"{name:<48} {ht:>9,} {tt:>9,} {1 - tt / ht:>6.1%} {hc / ht:>9.1f} {tc / tt:>9.1f} {mt:>9,} {(tt-mt)/mt:>7.1%}")
    ht, tt, mt = sum(r[2] for r in rows), sum(r[4] for r in rows), sum(r[5] for r in rows)
    print(f"{'TOTAL (20 pages)':<48} {ht:>9,} {tt:>9,} {1 - tt / ht:>6.1%} {'':>9} {'':>9} {mt:>9,} {(tt-mt)/mt:>+7.1%}")
