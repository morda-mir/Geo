# Current status

## Production setup

Use only these production URLs in Happ / Xray-compatible clients:

```text
Geositeurl: https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geosite.dat
Geoipurl:   https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geoip.dat
```

## Current production build

There is one production workflow:

```text
.github/workflows/build-happ-compatible-geo.yml
```

It runs the main builder:

```text
python3 build_morda_geo_happ.py
```

The builder creates both generated files:

```text
src/geosite/*
→ dist/geosite.dat

large upstream geoip.dat + src/geoip/*
→ dist/geoip.dat
```

Do not restore old split builders or split workflows. The removed legacy files were:

```text
build_morda_geo.py
scripts/build.py
.github/workflows/build.yml
.github/workflows/sync-production-geoip.yml
```

## Working categories

### Geosite

```text
geosite:MORDA-DIRECT
geosite:MORDA-PROXY
geosite:MORDA-TT
geosite:MORDA-ADS
geosite:MORDA-DISCORD-EXTRA
```

### GeoIP

```text
geoip:private
geoip:telegram
geoip:MORDA-BRAWLSTARS
geoip:MORDA-ROBLOX
geoip:MORDA-DISCORD
geoip:MORDA-OPENAI
```

`geoip:telegram` comes from the large production geoip base.

`geoip:MORDA-OPENAI` must have exactly one source file:

```text
src/geoip/morda-openai.txt
```

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

## Safe work process

1. Edit domain rules only in `src/geosite/*`.
2. Edit IP rules only in `src/geoip/*`.
3. Do not manually edit `dist/*.dat`.
4. Push or commit changes to `main`.
5. Wait for `build-happ-compatible-geo` to finish.
6. Confirm the generated commit exists:

```text
build: refresh Happ-compatible dat files [skip ci]
```

7. Confirm file sizes:

```text
dist/geoip.dat   around 19-20 MB
dist/geosite.dat around tens of KB
```

8. Refresh geo files in Happ only after the workflow succeeded.

## Emergency checks after a rebuild

Check these before trusting a new build:

```text
geoip.dat contains TELEGRAM
geoip.dat contains only one MORDA-OPENAI category
geosite.dat contains MORDA-DIRECT and MORDA-PROXY
OpenAI/Codex logs route through proxy
private/local IPs route through direct
```

## Current maintenance notes

- Keep OpenAI IP rules narrow and only add addresses confirmed in Happ/Xray logs.
- Do not add broad Cloudflare, Google Cloud, Azure or AWS ranges without strong evidence.
- Do not add a custom Telegram IP file unless the production `geoip:telegram` category is proven missing or incomplete.
- Do not add duplicate source files for the same `src/geoip` category.
- Do not re-add legacy one-file builders or parallel workflows.
