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
- `geosite:MORDA-TT`

`src/geosite/MORDA-TT` is also merged into `MORDA-PROXY` by the Happ-compatible build script, but it can still be used explicitly in client proxy rules.

### GeoIP

The production `dist/geoip.dat` is built from the large upstream geoip base plus custom categories from `src/geoip/`.

These categories are intended for production routing:

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
  "ProxySites": ["geosite:MORDA-PROXY", "geosite:MORDA-TT", "geosite:MORDA-DISCORD-EXTRA"],
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
- Twitch video/HLS endpoints that should stay direct

### `geosite:MORDA-PROXY`

Main domain-based proxy category.

Typical groups:

- Telegram domains
- WhatsApp domains
- YouTube domains and video/CDN-related endpoints
- short-video / ByteDance domains
- `geosite:MORDA-TT` as a dedicated TikTok/ByteDance category
- OpenAI / ChatGPT / Codex domains
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

### OpenAI / ChatGPT / Codex

ChatGPT and Codex use domain-based endpoints plus some IP-only or post-resolution realtime/API connections.

- domains should be routed through `geosite:MORDA-PROXY`
- observed OpenAI IP endpoints should be routed through `geoip:MORDA-OPENAI`
- keep exactly one source file for the category: `src/geoip/morda-openai.txt`

Keep OpenAI IP entries narrow. Cloudflare, Google Cloud and Azure ranges are shared infrastructure, so broad IP ranges can accidentally proxy unrelated traffic.

### Telegram

Telegram routing uses both:

- `geosite:MORDA-PROXY` for Telegram domains
- `geoip:telegram` from the large production geoip base for Telegram IP ranges

Do not add a custom Telegram IP file unless logs prove the production `geoip:telegram` category is missing or incomplete.

## Source layout

```text
src/geosite/              Custom geosite source categories
src/geoip/                Custom geoip source categories
scripts/                  Build helper scripts
dist/geosite.dat          Production geosite file for clients
dist/geoip.dat            Production geoip file for clients
```

`src/geosite/` and `src/geoip/` are the source of truth.

`dist/*.dat` files are generated production assets consumed by clients.

## Build and push workflow

### Which files to edit

- Domain rules: `src/geosite/*`
- IP rules: `src/geoip/*`
- Build logic only when needed: `build_morda_geo_happ.py` and `scripts/*`
- Do not edit `dist/*.dat` manually.

### Correct rebuild model

Only one workflow should write production `dist/*.dat` files:

```text
.github/workflows/build-happ-compatible-geo.yml
```

It builds both files together:

```text
src/geosite/* + src/geoip/* + production geoip upstream
→ dist/geosite.dat + dist/geoip.dat
```

Do not re-add separate workflows that write only `dist/geosite.dat` or only `dist/geoip.dat`. Parallel workflows can overwrite each other's generated files and create mismatched production assets.

### Safe push checklist

1. Commit only source/docs/script changes. Do not commit manual `dist/*.dat` edits.
2. Before touching `src/geoip/`, check that one category is not defined by two files. Example: keep only `src/geoip/morda-openai.txt` for `MORDA-OPENAI`.
3. Push/merge to `main`.
4. Wait for `build-happ-compatible-geo` to finish.
5. Confirm the latest generated commit is `build: refresh Happ-compatible dat files [skip ci]`.
6. Check file sizes before telling clients to refresh:
   - `dist/geoip.dat` should stay large, around 19-20 MB.
   - `dist/geosite.dat` is small, around tens of KB.
7. Only then ask clients to refresh geo files in Happ.

### Emergency sanity checks

After a rebuild, verify:

- `geoip.dat` still contains `TELEGRAM`.
- `geoip.dat` contains only one `MORDA-OPENAI` category.
- `geosite.dat` contains expected custom categories such as `MORDA-DIRECT` and `MORDA-PROXY`.
- Happ logs show OpenAI/Codex IPs routed through `proxy`, and local/private IPs routed through `direct`.

## Maintenance rules

- Prefer narrow, explicit rules over broad catch-all rules.
- Keep game and OpenAI IP entries as small as possible.
- Add IP rules only after confirming them in Happ/Xray logs.
- Put domains into geosite categories whenever possible.
- Keep `MORDA-ADS` small to avoid breaking pages and apps.
- Do not create duplicate category source files in `src/geoip/`.
- After changing sources, wait for Actions to regenerate `dist/*.dat` before using it in clients.

## Client setup checklist

1. Set `Geoipurl` to the production `dist/geoip.dat` raw URL.
2. Set `Geositeurl` to the production `dist/geosite.dat` raw URL.
3. Add `MORDA-DIRECT` to direct site rules.
4. Add `MORDA-PROXY` and `MORDA-DISCORD-EXTRA` to proxy site rules.
5. Add required `geoip:*` categories to proxy IP rules.
6. Add `MORDA-ADS` to block site rules if ad blocking is desired.
