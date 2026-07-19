"""
Antipromo.com Drop Monitor (GitHub Actions version)
Runs once per invocation, checks for new drops/restocks, exits.
State is persisted via GitHub Actions cache.
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────────
STORE_URL = "https://antipromo.com/products.json"
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1528304434289971241/OCQ2z2VoxOUfC3qjyqj9sinW4t4pDPL9pEzwn_iyB0F9XLkNANVzL9fsnPFiFf4yGTRD"
STATE_FILE = Path("state.json")


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"known_products": {}}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def fetch_products() -> list[dict]:
    req = urllib.request.Request(STORE_URL, headers={"User-Agent": "AntipromoMonitor/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode()).get("products", [])


def send_discord(embed: dict):
    payload = json.dumps({"embeds": [embed]}).encode()
    req = urllib.request.Request(
        DISCORD_WEBHOOK,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except urllib.error.HTTPError as e:
        print(f"Discord error: {e.code} {e.reason}")


def notify_new_product(product: dict):
    available_variants = [v for v in product["variants"] if v["available"]]
    sizes = ", ".join(v["title"] for v in available_variants) or "SOLD OUT"
    price = product["variants"][0]["price"] if product["variants"] else "?"
    image_url = product["images"][0]["src"] if product["images"] else None

    embed = {
        "title": f"\U0001f6a8 NEW DROP: {product['title']}",
        "url": f"https://antipromo.com/products/{product['handle']}",
        "color": 0xFF0000,
        "fields": [
            {"name": "Price", "value": f"${price}", "inline": True},
            {"name": "Type", "value": product.get("product_type", "N/A"), "inline": True},
            {"name": "Available Sizes", "value": sizes, "inline": False},
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "Antipromo Monitor"},
    }
    if image_url:
        embed["thumbnail"] = {"url": image_url}
    send_discord(embed)


def notify_restock(product: dict, restocked_variants: list[dict]):
    sizes = ", ".join(v["title"] for v in restocked_variants)
    price = restocked_variants[0]["price"]
    image_url = product["images"][0]["src"] if product["images"] else None

    embed = {
        "title": f"\U0001f504 RESTOCK: {product['title']}",
        "url": f"https://antipromo.com/products/{product['handle']}",
        "color": 0x00FF00,
        "fields": [
            {"name": "Price", "value": f"${price}", "inline": True},
            {"name": "Restocked Sizes", "value": sizes, "inline": False},
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "Antipromo Monitor"},
    }
    if image_url:
        embed["thumbnail"] = {"url": image_url}
    send_discord(embed)


def main():
    state = load_state()
    known = state["known_products"]
    products = fetch_products()
    first_run = not known

    for product in products:
        pid = str(product["id"])
        current_availability = {str(v["id"]): v["available"] for v in product["variants"]}

        if pid not in known:
            if not first_run:
                print(f"NEW: {product['title']}")
                notify_new_product(product)
            else:
                print(f"Seeded: {product['title']}")
            known[pid] = current_availability
        else:
            restocked = [
                v for v in product["variants"]
                if v["available"] and not known[pid].get(str(v["id"]), False)
            ]
            if restocked:
                print(f"RESTOCK: {product['title']}")
                notify_restock(product, restocked)
            known[pid] = current_availability

    state["known_products"] = known
    save_state(state)
    print(f"Done. Tracking {len(known)} products.")


if __name__ == "__main__":
    main()
