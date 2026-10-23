"""Day 1, Step 3, Method A (no AI): fill a fact card from the page's JSON-LD."""

import json
from pathlib import Path

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

DATA = Path(__file__).resolve().parent.parent / "data"


class Variant(BaseModel):
    name: str | None = None  # Blue Tokai / Bose offers don't name their variant
    price: float | None  # "3799.00" (Mokobara) and 800.0 (Blue Tokai) both become a float
    in_stock: bool | None = None


class FactCard(BaseModel):
    name: str
    currency: str | None = None
    variants: list[Variant]
    shipping: str | None = Field(default=None, max_length=80)
    returns: str | None = Field(default=None, max_length=80)


def jsonld_blocks(html: str) -> list[dict]:
    """Every JSON-LD block on the page that parses. Bose ships one broken block; skip it."""
    blocks = []
    for tag in BeautifulSoup(html, "html.parser").find_all("script", type="application/ld+json"):
        try:
            blocks.append(json.loads(tag.string or ""))
        except json.JSONDecodeError:
            continue
    return blocks


def in_stock(offer: dict) -> bool | None:
    """'http://schema.org/InStock' -> True. Missing -> None (unknown, not False)."""
    availability = offer.get("availability")
    return availability.endswith("/InStock") if availability else None


def from_product(d: dict) -> FactCard:
    """schema.org Product: offers holds one Offer per variant (Blue Tokai, Bose)."""
    offers = d["offers"] if isinstance(d["offers"], list) else [d["offers"]]
    transit = offers[0].get("shippingDetails", {}).get("deliveryTime", {}).get("transitTime")
    return FactCard(
        name=d["name"],
        currency=offers[0].get("priceCurrency"),
        variants=[Variant(price=o["price"], in_stock=in_stock(o)) for o in offers],
        shipping=f"{transit['minValue']}-{transit['maxValue']} days" if transit else None,
    )


def from_product_group(d: dict) -> FactCard:
    """schema.org ProductGroup: hasVariant holds one Product per variant, each with its own offer (Mokobara)."""
    has_variants = d["hasVariant"]
    variants = []
    for product in has_variants:
        raw = product["offers"]
        offers = raw if isinstance(raw, list) else [raw]
        for o in offers:
            variants.append(Variant(
                name=product["name"].removeprefix(f"{d['name']} - "),
                price=o["price"],
                in_stock=in_stock(o)
            ))

    first = has_variants[0]["offers"]
    first = first if isinstance(first, list) else [first]
    transit = first[0].get("shippingDetails", {}).get("deliveryTime", {}).get("transitTime")

    return FactCard(
        name=d["name"],
        currency=first[0].get("priceCurrency"),
        variants=variants,
        shipping=f"{transit['minValue']}-{transit['maxValue']} days" if transit else None,
    )

def method_a(html: str) -> FactCard | None:
    for d in jsonld_blocks(html):
        if d.get("@type") == "Product":
            return from_product(d)
        if d.get("@type") == "ProductGroup":
            return from_product_group(d)
    return None  # no product JSON-LD at all (Snitch)


if __name__ == "__main__":
    for path in sorted(DATA.glob("*/*.html")):
        card = method_a(path.read_text())
        print(f"{path.parent.name}/{path.stem}"[:48], card.model_dump_json(exclude_none=True) if card else None)
