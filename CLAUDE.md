# Token Diet for Shopping Agents

A small Python project that makes a shopping agent use fewer tokens without making worse choices.

- **Page Shrinker (Day 1):** product page → small fact card (name, price, variants, stock, shipping, returns)
- **Tool Picker (Day 2):** send only the ~5 tools that fit each message, instead of ~30
- **Test (Day 3):** run the same shopping tasks with and without both layers; report tokens, cost, tasks done right

Full plan doc: https://claude.ai/artifact/4mvB2XdfjFGa25H75qTrBz (steps are summarized below).

## Who you're working with

Zaid is a backend engineer (Go, TypeScript, Python, Postgres) learning AI engineering by building this.
Learning comes first, a finished project second. He must understand every line we commit.

## How to work (pair mode)

For every step:

1. Explain the idea in plain words, about 5 lines. Define any new term in one line.
2. Write ONE small piece (one function, ~30 lines max). Say why each part exists.
3. Leave the next similar piece for Zaid as `TODO(human)`. Say what to write and what to weigh.
4. Review his code plainly. Then ask him to explain it back in one line.

Move to the next step only when he can explain the last one.

Rules:

- Never work ahead of the current step. Don't scaffold future days.
- Before adding a library, say in one line what it does and why we need it.
- Run the code after each step and show the output. Explain anything surprising.
- Keep answers short and precise. No long paragraphs.
- If he asks "why", answer before doing anything else.
- After each step, append 2 lines to `docs/learning-log.md`: what we built, and the key idea. This feeds the README and LinkedIn post later.
- At the end of each day, ask that day's checkpoint questions. Let him answer before you do.
- After each step, update the "Current status" line at the bottom of this file.

## Stack

- Python 3.11+, uv for packages and the environment
- LLM: local Ollama model `spark-local` (4.1B, Q8_0, num_ctx 32768), called through Ollama's native API at `http://localhost:11434` with `httpx`. No API key or cost; "cost" = tokens × a reference API price. Never send raw HTML (it doesn't fit the context).
- Embeddings: `sentence-transformers`, run locally (no API cost)
- Others: `httpx`, `beautifulsoup4`, `extruct`, `pydantic`, `tiktoken`, `numpy`
- Fetch each store page once and save it under `data/`. Never re-fetch in loops.

## Repo layout

```
token-diet/
  data/       saved pages + answer keys
  shrinker/   Day 1
  picker/     Day 2
  agent/      Day 3 mini agent
  evals/      test sets + results
  docs/learning-log.md
```

## The plan

### Day 1 — Page Shrinker

1. Collect 20 product pages from 3–4 public Shopify stores. Save the HTML and `/products/<handle>.json` (the answer key).
2. Count tokens: raw HTML vs plain text. Compare with the local model's reported usage (`tiktoken` is only an estimate).
3. Method A, no AI: read the JSON-LD product data in the page.
4. Method B, AI: clean text → local model fills a Pydantic card.
5. Score each method against the answer key: tokens, cost, accuracy.

Checkpoint: Why count tokens, not characters? When is no-AI enough? What breaks without an answer key?

### Day 2 — Tool Picker

1. Write ~30 commerce tool definitions: Zaid's 7 harness tools (`search_products`, `get_product`, `add_to_cart`, `update_quantity`, `view_cart`, `ask_shopper`, `finish`) plus order status, cancel order, returns, coupons, shipping quote, size guide and similar. Fake responses are fine.
2. Count the tokens of all definitions sent together.
3. Write 40 test messages, each labelled with the right tool. Include tricky pairs ("cancel my order" vs "place my order").
4. Embed tool descriptions locally; pick the top-k tools per message.
5. Score: is the right tool in the top 3 / 5 / 8? Tokens saved?
6. Improve descriptions, add sample phrases, always include `view_cart` and `ask_shopper`. Score again.

Checkpoint: What does an embedding capture and miss? Why did opposite tools get confused, and what fixed it? What's the trade-off of a larger k?

### Day 3 — Test together and publish

1. Mini agent (~80 lines): local model tool calling plus a fake store built from Day 1 data.
2. Write 10–15 shopping tasks, each with a known correct final cart.
3. Run each task twice per setup. No diet: all tools + page text. Diet: picked tools + fact cards.
4. Compare tokens per task, cost per task, and correct carts.
5. README with results and what didn't work; LinkedIn post draft.

Fairness: the no-diet setup gets plain page text, not raw HTML.

Checkpoint: Why test the full agent? What would make the comparison unfair? What's one thing that didn't work, and why?

## Current status

Day 1, Step 2 — done. Raw HTML 3.38M → plain text 30K tokens (tiktoken); spark-local counts 37.8K (tiktoken −20%). ~8 s/page locally. Bose + Snitch are JS-rendered edge cases (kept). Next: Day 1, Step 3 (Method A: JSON-LD, no AI).
