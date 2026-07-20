"""
Combined Drop Monitor (Fly.io version)
Polls both stores in a loop every 10 seconds.
"""

import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────────
POLL_INTERVAL = 10

STORES = [
    {
        "name": "Antipromo",
        "url": "https://antipromo.com/products.json",
        "product_base": "https://antipromo.com/products",
        "webhook_env": "ANTIPROMO_DISCORD_WEBHOOK",
        "state_file": Path("state_antipromo.json"),
        "currency": "$",
        "paginate": False,
    },
    {
        "name": "Taiga Takahashi",
        "url": "https://taigatakahashi.com/en/collections/men/products.json?limit=250",
        "product_base": "https://taigatakahashi.com/en/products",
        "webhook_env": "TAIGA_DISCORD_WEBHOOK",
        "state_file": Path("state_taiga.json"),
        "currency": "¥",
        "paginate": True,
    },
]


def load_state(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {"known_products": {}}


def save_state(state: dict, path: Path):
    path.write_text(json.dumps(state, indent=2))


def fetch_products(url: str, paginate: bool) -> list[dict]:
    all_products = []
    page = 1
    while True:
        fetch_url = f"{url}&page={page}" if paginate and "?" in url else f"{url}?page={page}" if paginate else url
        req = urllib.request.Request(fetch_url, headers={"User-Agent": "DropMonitor/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            products = json.loads(resp.read().decode()).get("products", [])
        if not products:
            break
        all_products.extend(products)
        if not paginate:
            break
        page += 1
    return all_products


def send_discord(webhook: str, embed: dict):
    payload = json.dumps({"embeds": [embed]}).encode()
    req = urllib.request.Request(
        webhook,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "DropMonitor/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except urllib.error.HTTPError as e:
        print(f"  [!] Discord error: {e.code} {e.reason}")


def format_price(price: str, currency: str) -> str:
    if currency == "¥":
        return f"¥{int(price):,}"
    return f"${price}"


def notify_new(product: dict, webhook: str, base_url: str, currency: str, store_name: str):
    available = [v for v in product["variants"] if v["available"]]
    sizes = ", ".join(v["title"] for v in available) or "SOLD OUT"
    price = product["variants"][0]["price"] if product["variants"] else "?"
    image = product["images"][0]["src"] if product["images"] else None

    embed = {
        "title": f"\U0001f6a8 NEW DROP: {product['title']}",
        "url": f"{base_url}/{product['handle']}",
        "color": 0xFF0000,
        "fields": [
            {"name": "Price", "value": format_price(price, currency), "inline": True},
            {"name": "Type", "value": product.get("product_type", "N/A"), "inline": True},
            {"name": "Available Sizes", "value": sizes, "inline": False},
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": f"{store_name} Monitor"},
    }
    if image:
        embed["thumbnail"] = {"url": image}
    send_discord(webhook, embed)


def notify_restock(product: dict, variants: list, webhook: str, base_url: str, currency: str, store_name: str):
    sizes = ", ".join(v["title"] for v in variants)
    price = variants[0]["price"]
    image = product["images"][0]["src"] if product["images"] else None

    embed = {
        "title": f"\U0001f504 RESTOCK: {product['title']}",
        "url": f"{base_url}/{product['handle']}",
        "color": 0x00FF00,
        "fields": [
            {"name": "Price", "value": format_price(price, currency), "inline": True},
            {"name": "Restocked Sizes", "value": sizes, "inline": False},
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": f"{store_name} Monitor"},
    }
    if image:
        embed["thumbnail"] = {"url": image}
    send_discord(webhook, embed)


def check_store(store: dict):
    webhook = os.environ.get(store["webhook_env"])
    if not webhook:
        print(f"  [!] {store['name']}: No webhook set ({store['webhook_env']})")
        return

    state = load_state(store["state_file"])
    known = state["known_products"]
    products = fetch_products(store["url"], store["paginate"])
    first_run = not known

    for product in products:
        pid = str(product["id"])
        current = {str(v["id"]): v["available"] for v in product["variants"]}

        if pid not in known:
            if not first_run:
                print(f"  [NEW] {store['name']}: {product['title']}")
                notify_new(product, webhook, store["product_base"], store["currency"], store["name"])
            known[pid] = current
        else:
            restocked = [
                v for v in product["variants"]
                if v["available"] and not known[pid].get(str(v["id"]), False)
            ]
            if restocked:
                print(f"  [RESTOCK] {store['name']}: {product['title']}")
                notify_restock(product, restocked, webhook, store["product_base"], store["currency"], store["name"])
            known[pid] = current

    state["known_products"] = known
    save_state(state, store["state_file"])


def main():
    print("=" * 50)
    print("  DROP MONITOR")
    print(f"  Stores: {', '.join(s['name'] for s in STORES)}")
    print(f"  Polling every {POLL_INTERVAL}s")
    print("=" * 50)

    # Seed all stores on first run
    for store in STORES:
        if not store["state_file"].exists():
            print(f"\n[*] Seeding {store['name']}...")
            try:
                products = fetch_products(store["url"], store["paginate"])
                state = {"known_products": {
                    str(p["id"]): {str(v["id"]): v["available"] for v in p["variants"]}
                    for p in products
                }}
                save_state(state, store["state_file"])
                print(f"    Tracking {len(state['known_products'])} products")
            except Exception as e:
                print(f"    [!] Failed: {e}")

    print("\n[*] Monitoring for drops...\n")

    while True:
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] Checking...")
        for store in STORES:
            try:
                check_store(store)
            except Exception as e:
                print(f"  [!] {store['name']} error: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
