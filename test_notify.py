"""Send a test notification to both Discord webhooks."""
import json
import os
import urllib.request
import urllib.error

def send_test(webhook_env, store_name):
    webhook = os.environ.get(webhook_env, "")
    if not webhook:
        print(f"Missing {webhook_env}")
        return

    # Debug: show URL shape without exposing the token
    print(f"{store_name}: URL length={len(webhook)}, starts_with_https={webhook.startswith('https://')}, has_whitespace={webhook != webhook.strip()}")

    webhook = webhook.strip()
    embed = {
        "title": f"\u2705 TEST: {store_name} Monitor is working!",
        "description": "This is a test notification. You'll get alerts like this when new drops or restocks happen.",
        "color": 0x5865F2,
    }
    payload = json.dumps({"embeds": [embed]}).encode()
    req = urllib.request.Request(webhook, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10):
            print(f"{store_name}: sent!")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"{store_name}: HTTP {e.code} - {body}")

send_test("ANTIPROMO_DISCORD_WEBHOOK", "Antipromo")
send_test("TAIGA_DISCORD_WEBHOOK", "Taiga Takahashi")
