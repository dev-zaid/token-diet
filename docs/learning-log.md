# Learning log

- **Day 1.1 built:** `shrinker/collect.py` saves 20 product pages + their `/products/<handle>.json` answer keys (5 each from Mokobara, Bose India, Snitch, Blue Tokai).
- **Day 1.1 key idea:** a test set is only as good as its picks: fetch a big pool, drop junk and repeated titles, prefer multi-variant products, or "20 pages" quietly test the same thing several times.
- **Day 1.2 built:** `shrinker/count_tokens.py` counts tokens for all 20 pages: raw HTML 3.38M → plain text 30K (−99%), then asks the local model (`spark-local` via Ollama) for its real count: 37.8K.
- **Day 1.2 key idea:** a token count belongs to one tokenizer; tiktoken undercounted our model by ~20%, which is fine for A-vs-B comparisons but wrong for cost or context-window math. Also: JS-rendered pages (Bose, Snitch) have almost no plain text.
- **Day 1.3 built:** `shrinker/method_a.py` (Method A, no AI) reads the page's JSON-LD into a pydantic `FactCard`: Mokobara complete (named variants matching the answer key, price, stock), Blue Tokai prices but no variant names, Bose 1 of 6–7 variants + shipping, Snitch nothing.
- **Day 1.3 key idea:** structured data is free and exact, but how much of it exists is the store's choice: same code, four stores, four levels of completeness. Missing means `None` (unknown), never `False`.
