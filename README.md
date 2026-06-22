# Antipromo Drop Monitor

Watches [antipromo.com](https://antipromo.com) for new product drops and restocks.  
Sends Discord alerts when something goes live.

## How it works
- Runs every 5 minutes via GitHub Actions cron
- Checks the Shopify `/products.json` endpoint
- Detects new products and restocks (sold out → available)
- Sends a Discord embed with product name, price, sizes, and thumbnail

## Setup

1. Create a **public** GitHub repo (free unlimited Actions minutes)
2. Push this folder to it:
   ```
   cd C:\Users\christlew\antipromo-monitor
   git init
   git add .
   git commit -m "antipromo monitor"
   gh repo create antipromo-monitor --public --source . --push
   ```
3. That's it. The workflow runs every 5 minutes automatically.

You can also trigger it manually from the Actions tab → "Run workflow".

## Worst-case delay
~5 minutes after a drop goes live → Discord ping on your phone.

## Files
- `check.py` — the monitor script (runs once per invocation)
- `.github/workflows/monitor.yml` — GitHub Actions cron schedule
