#!/usr/bin/env python3
"""Fetch price-comparison pages for the Raspberry Pi 5 and write prices.json.
Run daily by GitHub Actions. Add more pages to SOURCES to widen the search."""
import json, datetime, re, sys
import requests
from bs4 import BeautifulSoup

# model -> list of comparison pages (each lists many shops). Add more URLs freely.
SOURCES = {
    "4GB": ["https://geizhals.eu/raspberry-pi-5-modell-b-a3029965.html",
            "https://www.guenstiger.de/Produkt/Raspberry_Pi/5_Modell_B_4GB.html"],
    "8GB": ["https://geizhals.eu/raspberry-pi-5-modell-b-a3029981.html",
            "https://www.guenstiger.de/Produkt/Raspberry_Pi/5_Modell_B_8GB.html"],
    "2GB": [], "16GB": [],
}
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

def fetch(url):
    """Return list of {shop, price, currency, url} found on one comparison page."""
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    found = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try: data = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError): continue
        for d in walk(data):
            if d.get("@type") in ("Offer", "AggregateOffer"):
                seller = d.get("seller")
                shop = seller.get("name") if isinstance(seller, dict) else None
                for key in ("price", "lowPrice"):
                    p = num(d.get(key)) if d.get(key) is not None else None
                    if p and p > 20:
                        found.append({"shop": shop or "Lowest listed offer", "price": p,
                                      "currency": d.get("priceCurrency", "EUR"),
                                      "url": d.get("url") or url, "source": url})
    return found

def main():
    try: old = json.load(open("prices.json"))
    except (OSError, ValueError): old = {"models": {}}
    out = {"updated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes"), "models": {}}
    for model, urls in SOURCES.items():
        offers = []
        for u in urls:
            try: offers += fetch(u)
            except Exception as e: print(f"{model}: {u} failed: {e}", file=sys.stderr)
        if offers:
            offers.sort(key=lambda o: o["price"])
            seen, uniq = set(), []
            for o in offers:
                k = (o["shop"], o["price"])
                if k not in seen: seen.add(k); uniq.append(o)
            out["models"][model] = {"offers": uniq[:12], "sources": urls, "fresh": True}
        else:  # keep yesterday's data rather than show nothing
            prev = old.get("models", {}).get(model, {"offers": [], "sources": urls})
            prev["fresh"] = False
            out["models"][model] = prev
    json.dump(out, open("prices.json", "w"), indent=1, ensure_ascii=False)
    print("done")

if __name__ == "__main__":
    main()
