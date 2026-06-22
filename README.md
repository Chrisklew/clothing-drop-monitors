# Drop Monitors

Automated drop monitors for Shopify stores. Sends Discord alerts when new products drop or sold-out items restock.

## Stores Monitored

| Store | Collection | Check Interval |
|-------|-----------|----------------|
| [Antipromo](https://antipromo.com) | All products | Every 5 min |
| [Taiga Takahashi](https://taigatakahashi.com/en/collections/men) | Men's | Every 5 min |

## How it works
- Runs every 5 minutes via GitHub Actions cron
- Checks each store's Shopify `/products.json` endpoint
- Detects **new products** and **restocks** (sold out → available)
- Sends a Discord embed with product name, price, available sizes, and thumbnail

## Worst-case delay
~5 minutes after a drop goes live → Discord ping on your phone.

## Files
- `check.py` — Antipromo monitor
- `check_taiga.py` — Taiga Takahashi monitor
- `.github/workflows/monitor.yml` — Antipromo cron schedule
- `.github/workflows/monitor_taiga.yml` — Taiga Takahashi cron schedule
