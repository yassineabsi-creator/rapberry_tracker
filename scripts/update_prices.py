#!/usr/bin/env python3
"""Read Raspberry Pi 5 prices directly from shop product pages and write prices.json."""
import json, datetime, sys
import requests
from bs4 import BeautifulSoup

# (model, shop name, product page URL). Add one line per shop page you want to track.
SHOPS = [
    ("8GB", "BerryBase", "https://www.berrybase.at/en/raspberry-pi-5-8gb-ram"),
    ("8GB", "PiShop.us", "https://www.pishop.us/product/raspberry-pi-5-8gb/"),
]
TO_EUR = {"EUR": 1.0, "USD": 0.93, "GBP": 1.15}   # rough rates, only used for sorting
MODELS = ["2GB", "4GB", "8GB", "16GB"]
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
           "Accept-Language": "en,de;q=0.8"}

def walk(node):
    if isinstance(node, list):
        for i in node: yield from walk(i)
    elif isinstance(node, dict):
        yield node
        for v in node.values(): yield from walk(v)

def num(x):
    try: return float(str(x).replace(",", "."))
    except ValueError: return None

def get_price(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    best = None
    for tag in soup.find_all("script", type="application/ld+json"):
        try: data = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError): continue
        for d in walk(data):
            if d.get("@type") in ("Offer", "AggregateOffer"):
                if "OutOfStock" in str(d.get("availability", "")): continue
                p = num(d.get("price") or d.get("lowPrice") or "")
                if p and p > 20 and (best is None or p < best[0]):
                    best = (p, d.get("priceCurrency", "EUR"))
    if best: return best
    # fallback: meta tags used by many shops
    for prop in ("product:price:amount", "og:price:amount"):
        m = soup.find("meta", attrs={"property": prop})
        if m and num(m.get("content")):
            cur = soup.find("meta", attrs={"property": prop.replace("amount", "currency")})
            return num(m["content"]), (cur["content"] if cur else "EUR")
    m = soup.find(attrs={"itemprop": "price"})
    if m and num(m.get("content") or m.get_text()):
        return num(m.get("content") or m.get_text()), "EUR"
    return None

def main():
    try: old = json.load(open("prices.json"))
    except (OSError, ValueError): old = {"models": {}}
    out = {"updated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes"), "models": {}}
    for model in MODELS:
        offers = []
        for m, shop, url in SHOPS:
            if m != model: continue
            try:
                got = get_price(url)
                if got: offers.append({"shop": shop, "price": got[0], "currency": got[1], "url": url, "source": url})
                else: print(f"{model} {shop}: no price found", file=sys.stderr)
            except Exception as e:
                print(f"{model} {shop}: failed: {e}", file=sys.stderr)
        if offers:
            offers.sort(key=lambda o: o["price"] * TO_EUR.get(o["currency"], 1))
            out["models"][model] = {"offers": offers, "fresh": True}
        else:
            prev = old.get("models", {}).get(model, {"offers": []})
            prev["fresh"] = False
            out["models"][model] = prev
    json.dump(out, open("prices.json", "w"), indent=1, ensure_ascii=False)
    print("done")

if __name__ == "__main__":
    main()

