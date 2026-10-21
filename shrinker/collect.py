"""Day 1, Step 1: save product pages + their JSON answer keys under data/<store>/."""

import time
from pathlib import Path

import httpx

DATA = Path(__file__).resolve().parent.parent / "data"
STORES = ["mokobara.com", "www.boseindia.com", "snitch.co.in", "bluetokaicoffee.com"]
PER_STORE = 5


def save_product(client: httpx.Client, store: str, handle: str) -> None:
    """Save <handle>.html (what the agent reads) and <handle>.json (the answer key)."""
    out = DATA / store
    html_path, json_path = out / f"{handle}.html", out / f"{handle}.json"
    if html_path.exists() and json_path.exists():
        return  # fetch once, never again
    out.mkdir(parents=True, exist_ok=True)
    url = f"https://{store}/products/{handle}"
    for path, u in ((html_path, url), (json_path, url + ".json")):
        r = client.get(u)
        r.raise_for_status()
        path.write_text(r.text)
        time.sleep(1)  # be polite: one request per second


def is_junk(product: dict) -> bool:
    """True if this listing is not a real shoppable product."""
    handle = product.get("handle", "").lower()
    title = product.get("title", "").lower()
    kind = product.get("product_type", "").lower()
    if handle.startswith("content-"):
        return True  # CMS / lookbook pages stuffed into the catalog
    if handle.endswith("-copy"):
        return True  # admin's duplicate listing
    if "gift-card" in handle or "gift card" in title or "gift card" in kind:
        return True
    return False


def list_handles(client: httpx.Client, store: str, n: int) -> list[str]:
    """Return n product handles from the store's /products.json listing."""
    url = f"https://{store}/products.json?limit=250"
    r = client.get(url)
    r.raise_for_status()
    handles = []
    products = sorted(r.json()["products"], key=lambda p: len(p["variants"]) > 1, reverse=True)
    seen = set()
    for item in products:
        if is_junk(item):
            continue
        title = item["title"].strip().lower()
        if title in seen:
            continue
        seen.add(title)
        handles.append(item["handle"])
        if len(handles) >= n:
            break
    print(f"found {len(handles)} handles for {store}")
    print(handles)
    return handles


if __name__ == "__main__":
    with httpx.Client(headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True, timeout=20) as client:
        for store in STORES:
            for handle in list_handles(client, store, PER_STORE):
                save_product(client, store, handle)
                print("saved", store, handle)
