#!/usr/bin/env python3
"""Read Raspberry Pi 5 prices directly from shop product pages and write prices.json."""
import json, datetime, sys
import requests
from bs4 import BeautifulSoup

# (model, shop, product page URL [, VAT multiplier for shops that show prices without VAT])
# Lines ending in "# ?" are links I have not seen myself; the log shows if they fail.
SHOPS = [
    # ---- 8GB ----
    ("8GB", "BerryBase (DE)", "https://www.berrybase.de/en/raspberry-pi-5-8gb-ram"),
    ("8GB", "BerryBase (AT)", "https://www.berrybase.at/en/raspberry-pi-5-8gb-ram"),
    ("8GB", "Welectron (DE)", "https://www.welectron.com/Raspberry-Pi-5-8-GB"),
    ("8GB", "Tinytronics (NL)", "https://www.tinytronics.nl/en/development-boards/single-board-computers/raspberry-pi-5-8gb"),
    ("8GB", "Kiwi Electronics (NL)", "https://www.kiwi-electronics.com/en/raspberry-pi-5-8gb-11580", 1.21),
    ("8GB", "Galaxus (DE)", "https://www.galaxus.de/en/s1/product/raspberry-pi-new-5-8gb-single-board-computer-kits-38955607"),
    ("8GB", "Galaxus (AT)", "https://galaxus.at/en/s1/product/raspberry-pi-new-5-8gb-development-boards-kits-38955607"),
    ("8GB", "Galaxus (NL)", "https://galaxus.nl/en/s1/product/raspberry-pi-new-5-8gb-development-boards-kits-38955607"),
    ("8GB", "Galaxus (IT)", "https://www.galaxus.it/en/s1/product/raspberry-pi-new-5-8gb-single-board-computer-kits-38955607"),
    ("8GB", "Semaf (AT)", "https://electronics.semaf.at/Raspberry-Pi-5-8GB_1"),
    ("8GB", "Office Partner (DE)", "https://www.office-partner.de/raspberry-pi-modell-5-8gb-n2008301863"),
    ("8GB", "Conrad", "https://www.conrad.com/en/p/raspberry-pi-sc1112-raspberry-pi-5-b-8-gb-4-x-2-4-ghz-2980040.html"),
    ("8GB", "PiShop.us (US)", "https://www.pishop.us/product/raspberry-pi-5-8gb/"),
    ("8GB", "Kubii (FR)", "https://www.kubii.com/en/nano-computers/4106-1831-raspberry-pi-5-3272496315938.html"),  # ?
    ("8GB", "Electrokit (SE)", "https://www.electrokit.com/en/raspberry-pi-5-/8gb"),  # ?
    ("8GB", "OpenCircuit (NL)", "https://opencircuit.shop/product/raspberry-pi-5-8gb-2"),  # ?
    ("8GB", "RaspberryStore (NL)", "https://www.raspberrystore.nl/PrestaShop/nl/raspberry-pi-5/508-raspberry-pi-5-8gb-5056561803326.html"),  # ?
    ("8GB", "Melopero (IT)", "https://www.melopero.com/en/shop/boards/pi5/raspberry-pi-5-8gb/"),  # ?
    ("8GB", "Botland (PL/EU)", "https://botland.store/raspberry-pi-5-modules-and-kits/23905-raspberry-pi-5-8gb-5056561803326.html"),  # ?
    ("8GB", "OKdo (UK/EU)", "https://www.okdo.com/p/raspberry-pi-5-8gb/"),  # ?
    ("8GB", "Adafruit (US)", "https://www.adafruit.com/product/5813"),  # ?
    ("8GB", "SparkFun (US)", "https://www.sparkfun.com/raspberry-pi-5-8gb.html"),  # ?
    ("8GB", "CanaKit (US/CA)", "https://www.canakit.com/raspberry-pi-5-8gb.html"),  # ?
    # ---- 4GB ----
    ("4GB", "Kiwi Electronics (NL)", "https://www.kiwi-electronics.com/en/brand-raspberry-pi/raspberry-pi-5-4gb-11579", 1.21),
    ("4GB", "Galaxus (DE)", "https://www.galaxus.de/en/s1/product/raspberry-pi-new-5-4gb-development-boards-kits-38955609"),
    ("4GB", "Galaxus (AT)", "https://www.galaxus.at/en/s1/product/raspberry-pi-new-5-4gb-single-board-computer-kits-38955609"),
    ("4GB", "Galaxus (BE)", "https://www.galaxus.be/en/s1/product/raspberry-pi-new-5-4gb-development-boards-kits-38955609"),
    ("4GB", "Semaf (AT)", "https://electronics.semaf.at/Raspberry-Pi-5-4GB_1"),
    ("4GB", "Botland", "https://botland.store/raspberry-pi-5-modules-and-kits/23904-raspberry-pi-5-4gb--5056561803319.html"),
    ("4GB", "Raspberrypi.dk (DK)", "https://raspberrypi.dk/en/?p=196259"),
    ("4GB", "Audiophonics (FR)", "https://www.audiophonics.fr/fr/single-board-computers-et-hats/raspberry-pi-5-4gb-micro-hdmi-ethernet-gigabit-wifi-bluetooth-50-4x-usb-24ghz-p-18332.html"),
    ("4GB", "BerryBase (DE)", "https://www.berrybase.de/en/raspberry-pi-5-4gb-ram"),  # ?
    ("4GB", "Welectron (DE)", "https://www.welectron.com/Raspberry-Pi-5-4-GB"),  # ?
    ("4GB", "Tinytronics (NL)", "https://www.tinytronics.nl/en/development-boards/single-board-computers/raspberry-pi-5-4gb"),  # ?
    ("4GB", "RaspberryStore (NL)", "https://www.raspberrystore.nl/PrestaShop/en/Raspberry_pi_5/507-raspberry-pi-5-4gb-5056561803319.html"),  # ?
    ("4GB", "Melopero (IT)", "https://www.melopero.com/en/shop/boards/pi5/raspberry-pi-5-4gb/"),  # ?
    ("4GB", "PiShop.us (US)", "https://www.pishop.us/product/raspberry-pi-5-4gb/"),  # ?
    ("4GB", "SparkFun (US)", "https://www.sparkfun.com/raspberry-pi-5-4gb.html"),  # ?
    # ---- 2GB ----
    ("2GB", "Audiophonics (FR)", "https://www.audiophonics.fr/fr/raspberry-pi-et-modules-pour-rpi/raspberry-pi-5-2gb-p-19810.html"),
    ("2GB", "BerryBase (DE)", "https://www.berrybase.de/en/raspberry-pi-5-2gb-ram"),  # ?
    ("2GB", "Welectron (DE)", "https://www.welectron.com/Raspberry-Pi-5-2-GB"),  # ?
    ("2GB", "Tinytronics (NL)", "https://www.tinytronics.nl/en/development-boards/single-board-computers/raspberry-pi-5-2gb"),  # ?
    # ---- 16GB ----
    ("16GB", "BerryBase (DE)", "https://www.berrybase.de/en/raspberry-pi-5-16gb-ram"),  # ?
    ("16GB", "Melopero (IT)", "https://www.melopero.com/en/shop/boards/pi5/raspberry-pi-5-16gb/"),  # ?
    ("16GB", "Welectron (DE)", "https://www.welectron.com/Raspberry-Pi-5-16-GB"),  # ?
    ("16GB", "Tinytronics (NL)", "https://www.tinytronics.nl/en/development-boards/single-board-computers/raspberry-pi-5-16gb"),  # ?
    ("16GB", "PiShop.us (US)", "https://www.pishop.us/product/raspberry-pi-5-16gb/"),  # ?
]
TO_EUR = {"EUR": 1.0, "USD": 0.93, "GBP": 1.15, "SEK": 0.087, "DKK": 0.134, "PLN": 0.23, "CHF": 1.05, "CAD": 0.68}
RANGE = {"2GB": (50, 140), "4GB": (80, 220), "8GB": (120, 320), "16GB": (200, 600)}  # plausible EUR prices
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
        for m, shop, url, *extra in SHOPS:
            if m != model: continue
            try:
                got = get_price(url)
                if not got:
                    print(f"{model} {shop}: no price found", file=sys.stderr); continue
                price = round(got[0] * (extra[0] if extra else 1), 2)
                lo, hi = RANGE[model]
                if lo <= price * TO_EUR.get(got[1], 1) <= hi:
                    offers.append({"shop": shop, "price": price, "currency": got[1], "url": url, "source": url})
                else:
                    print(f"{model} {shop}: price {price} {got[1]} outside expected range, skipped", file=sys.stderr)
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

