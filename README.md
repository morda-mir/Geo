# morda custom geo

Custom geo repository for Xray / RemnaWave / Happ routing rules.

This repository publishes ready-to-use `geosite.dat` and `geoip.dat` files for clients that support custom geo assets.

## Production URLs

Use these URLs in Happ / Xray-compatible clients:

```text
https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geosite.dat
https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geoip.dat
https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geosite.dat.sha256
https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geoip.dat.sha256
https://raw.githubusercontent.com/morda-mir/Geo/main/dist/incy-routing-v2.json
```

## What this repo is for

The goal is to keep one predictable routing set:

- direct local/RU services without proxy
- proxy-only services and apps
- lightweight ad/tracker blocking
- extra Discord domains for voice/media/client features
- selected IP-only categories for apps that do not always route cleanly by domain

## Production categories

### Geosite

These categories are built from `src/geosite/`:

- `geosite:MORDA-DIRECT`
- `geosite:MORDA-PROXY`
- `geosite:MORDA-ADS`
- `geosite:MORDA-DISCORD-EXTRA`
- `geosite:MORDA-TT`

`MORDA-TT` is also merged into `MORDA-PROXY` by the Happ-compatible build script, but it can still be included explicitly in client proxy rules.

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

## Source layout

```text
src/geosite/                    Custom geosite source categories
src/geoip/                      Custom geoip source categories
build_morda_geo_happ.py         Main production builder
scripts/append_custom_geoip.py   Helper that appends src/geoip/* to the large geoip base
dist/geosite.dat                Generated production geosite file
dist/geoip.dat                  Generated production geoip file
dist/geosite.dat.sha256         SHA-256 used by INCY update checks
dist/geoip.dat.sha256           SHA-256 used by INCY update checks
dist/incy-routing.json          Current production INCY profile
dist/incy-routing-v2.json       Isolated profile for the new production stack
.github/workflows/build-happ-compatible-geo.yml
                                 The only workflow that should write dist/*.dat
```

`src/geosite/` and `src/geoip/` are the source of truth.

`dist/*.dat` files are generated production assets consumed by clients. Do not edit them manually.

## Current build model

There is one production workflow:

```text
.github/workflows/build-happ-compatible-geo.yml
```

It runs:

```text
python3 build_morda_geo_happ.py
```

The builder does this:

```text
src/geosite/*
→ dist/geosite.dat

large upstream geoip.dat + src/geoip/*
→ dist/geoip.dat

dist/*.dat
→ dist/*.dat.sha256
```

When either generated `.dat` file changes, the builder also refreshes
`LastUpdated` in both INCY routing profiles.

The `geoip.dat` file must stay large, around 19-20 MB. If it becomes a tiny KB-sized file, the build is wrong.

Do not re-add separate workflows that write only `dist/geosite.dat` or only `dist/geoip.dat`. Parallel workflows can overwrite each other's generated files and create mismatched production assets.

## Which files to edit

### Normal rule changes

Edit only source files:

```text
src/geosite/*
src/geoip/*
```

After a commit to `main`, GitHub Actions rebuilds the generated `dist/*.dat` files.

### Build logic changes

Edit these only when changing the build mechanism itself:

```text
build_morda_geo_happ.py
scripts/append_custom_geoip.py
.github/workflows/build-happ-compatible-geo.yml
```

Current workflow triggers automatically for:

```text
src/geosite/**
src/geoip/**
build_morda_geo_happ.py
.github/workflows/build-happ-compatible-geo.yml
```

If only `scripts/append_custom_geoip.py` is changed, run `build-happ-compatible-geo` manually from GitHub Actions, unless `scripts/**` is added to the workflow trigger first.

## Safe push checklist

1. Commit only source/docs/script changes. Do not commit manual `dist/*.dat` edits.
2. Before touching `src/geoip/`, check that one category is not defined by two files.
3. Keep exactly one source file for OpenAI IP rules: `src/geoip/morda-openai.txt`.
4. Push/merge to `main`.
5. Wait for `build-happ-compatible-geo` to finish.
6. Confirm the generated commit exists: `build: refresh Happ-compatible dat files [skip ci]`.
7. Check file sizes before telling clients to refresh:
   - `dist/geoip.dat` should stay around 19-20 MB.
   - `dist/geosite.dat` should stay small, around tens of KB.
8. Only then refresh geo files in Happ.

## Emergency sanity checks

After a rebuild, verify:

- `geoip.dat` still contains `TELEGRAM`.
- `geoip.dat` contains only one `MORDA-OPENAI` category.
- `geosite.dat` contains expected custom categories such as `MORDA-DIRECT` and `MORDA-PROXY`.
- Happ logs show OpenAI/Codex IPs routed through `proxy`.
- Local/private IPs stay routed through `direct`.

## Category notes

### `geosite:MORDA-DIRECT`

Direct list for RU/local services that often detect VPN usage or work better without proxy.

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
- OpenAI / ChatGPT / Codex domains
- other services that should be routed through proxy by domain

### `geosite:MORDA-ADS`

Small ad/tracker blocklist. It is intentionally lightweight to reduce false positives.

### `geosite:MORDA-DISCORD-EXTRA`

Additional Discord-related domains for client, gateway, CDN, media, voice and community integrations. Use it together with `geosite:MORDA-PROXY`.

### `geoip:MORDA-OPENAI`

OpenAI IP rules live only in:

```text
src/geoip/morda-openai.txt
```

Keep entries narrow. Cloudflare, Google Cloud and Azure IPs are shared infrastructure, so broad ranges can accidentally proxy unrelated traffic.

### `geoip:telegram`

Telegram IP routing comes from the large production geoip base. Do not add a custom Telegram IP file unless logs prove the production `geoip:telegram` category is missing or incomplete.

## Maintenance rules

- Prefer narrow, explicit rules over broad catch-all rules.
- Add IP rules only after confirming them in Happ/Xray logs.
- Put domains into geosite categories whenever possible.
- Keep `MORDA-ADS` small to avoid breaking pages and apps.
- Do not create duplicate category source files in `src/geoip/`.
- Do not restore legacy builders such as `build_morda_geo.py` or `scripts/build.py`.
- Wait for Actions to regenerate `dist/*.dat` before using new files in clients.
