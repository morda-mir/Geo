# morda custom geo

Custom geo repository for Xray / RemnaWave / Happ routing rules.

The repository publishes ready-to-use `geosite.dat` and `geoip.dat` files for clients that support custom geo assets.

## Production URLs

Use these URLs in Happ / Xray-compatible clients:

```text
https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geosite.dat
https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geoip.dat
```

## What this repo is for

The goal is to keep one small, predictable set of routing categories:

- direct local/RU services without proxy
- proxy-only services and apps
- lightweight ad/tracker blocking
- extra Discord domains that are useful for voice/media/client features
- selected IP-only categories for apps that do not always route cleanly by domain

## Production categories

### Geosite

These categories are built from `src/geosite/`:

- `geosite:MORDA-DIRECT`
- `geosite:MORDA-PROXY`
- `geosite:MORDA-ADS`
- `geosite:MORDA-DISCORD-EXTRA`

### GeoIP

These categories are intended for production routing in `dist/geoip.dat`:

- `geoip:private`
- `geoip:telegram`
- `geoip:MORDA-BRAWLSTARS`
- `geoip:MORDA-ROBLOX`
- `geoip:MORDA-DISCORD`
- `geoip:MORDA-OPENAI`

## Recommended desktop Happ routing profile

```json
{
  "Geoipurl": "https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geoip.dat",
  "Geositeurl": "https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geosite.dat",
  "DirectSites": ["geosite:MORDA-DIRECT"],
  "DirectIp": ["geoip:private"],
  "ProxySites": ["geosite:MORDA-PROXY", "geosite:MORDA-DISCORD-EXTRA"],
  "ProxyIp": [
    "geoip:telegram",
    "geoip:MORDA-BRAWLSTARS",
    "geoip:MORDA-ROBLOX",
    "geoip:MORDA-DISCORD",
    "geoip:MORDA-OPENAI"
  ],
  "BlockSites": ["geosite:MORDA-ADS"],
  "BlockIp": []
}
```

## Category notes

### `geosite:MORDA-DIRECT`

Broad direct list for RU/local services that often detect VPN usage or work better without proxy.

Typical groups:

- government and public services
- banks and payment systems
- marketplaces, delivery, transport, maps and local utilities
- mobile operators
- local portals and ecosystems such as Yandex, VK and Mail.ru

### `geosite:MORDA-PROXY`

Main domain-based proxy category.

Typical groups:

- Telegram domains
- WhatsApp domains
- YouTube domains and video/CDN-related endpoints
- other services that should be routed through proxy by domain

### `geosite:MORDA-ADS`

Small ad/tracker blocklist.

It is intentionally lightweight to reduce false positives and avoid breaking apps or websites.

### `geosite:MORDA-DISCORD-EXTRA`

Additional Discord-related domains for client, gateway, CDN, media, voice and community integrations.

Use it together with `geosite:MORDA-PROXY`.

## App-specific routing notes

### Brawl Stars

Brawl Stars uses both domain-based Supercell endpoints and IP-only game server connections.

- domains should be routed through `geosite:MORDA-PROXY`
- observed IP-only game server addresses should be routed through `geoip:MORDA-BRAWLSTARS`

Keep Brawl Stars IP entries narrow, preferably `/32`, and only add addresses confirmed from Happ/Xray logs.

### Roblox

Roblox uses both domain-based endpoints and game/server IP ranges.

- domains should be routed through `geosite:MORDA-PROXY`
- known Roblox IP ranges should be routed through `geoip:MORDA-ROBLOX`

### Discord

Discord uses domain-based endpoints plus voice/media IP ranges.

- domains should be routed through `geosite:MORDA-PROXY` and `geosite:MORDA-DISCORD-EXTRA`
- known Discord voice/media IP ranges should be routed through `geoip:MORDA-DISCORD`

### OpenAI / ChatGPT

ChatGPT uses domain-based endpoints and some IP-only or post-resolution realtime/API connections.

- domains should be routed through `geosite:MORDA-PROXY`
- observed ChatGPT/OpenAI IP endpoints should be routed through `geoip:MORDA-OPENAI`

Keep OpenAI IP entries narrow. Cloudflare, Google Cloud and Azure ranges are shared infrastructure, so broad IP ranges can accidentally proxy unrelated traffic.

## Source layout

```text
src/geosite/              Custom geosite source categories
dist/geosite.dat          Production geosite file for clients
dist/geoip.dat            Production geoip file for clients
```

`src/geosite/` is the source of truth for custom domain categories.

`dist/*.dat` files are the production assets consumed by clients.

## Maintenance rules

- Prefer narrow, explicit rules over broad catch-all rules.
- Keep game and OpenAI IP entries as small as possible.
- Add IP rules only after confirming them in Happ/Xray logs.
- Put domains into geosite categories whenever possible.
- Keep `MORDA-ADS` small to avoid breaking pages and apps.
- After changing sources, rebuild/update the corresponding `dist/*.dat` file before using it in clients.

## Client setup checklist

1. Set `Geoipurl` to the production `dist/geoip.dat` raw URL.
2. Set `Geositeurl` to the production `dist/geosite.dat` raw URL.
3. Add `MORDA-DIRECT` to direct site rules.
4. Add `MORDA-PROXY` and `MORDA-DISCORD-EXTRA` to proxy site rules.
5. Add required `geoip:*` categories to proxy IP rules.
6. Add `MORDA-ADS` to block site rules if ad blocking is desired.
