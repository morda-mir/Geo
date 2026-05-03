# morda custom geo

Custom geo repo for Xray / RemnaWave / Happ.

## Production model

This repository has two production outputs:

- `dist/geosite.dat` is built from the small custom sources in `src/geosite/`
- `dist/geoip.dat` is built by mirroring the upstream production geoip file and appending custom categories from `src/geoip/`

Clients should use only this repository for both URLs:

- `https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geosite.dat`
- `https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geoip.dat`

## Production categories

- `geosite:MORDA-DIRECT`
- `geosite:MORDA-PROXY`
- `geosite:MORDA-ADS`
- `geosite:MORDA-DISCORD-EXTRA`
- `geoip:private`
- `geoip:telegram`
- `geoip:MORDA-BRAWLSTARS`
- `geoip:MORDA-ROBLOX`
- `geoip:MORDA-DISCORD`

## Recommended desktop Happ routing profile

```json
{
  "Geoipurl": "https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geoip.dat",
  "Geositeurl": "https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geosite.dat",
  "DirectSites": ["geosite:MORDA-DIRECT"],
  "DirectIp": ["geoip:private"],
  "ProxySites": ["geosite:MORDA-PROXY", "geosite:MORDA-DISCORD-EXTRA"],
  "ProxyIp": ["geoip:telegram", "geoip:MORDA-BRAWLSTARS", "geoip:MORDA-ROBLOX", "geoip:MORDA-DISCORD"],
  "BlockSites": ["geosite:MORDA-ADS"],
  "BlockIp": []
}
```

## Brawl Stars routing

Brawl Stars uses both domain-based Supercell endpoints and IP-only game server connections.

- domains are routed via `geosite:MORDA-PROXY`
- observed IP-only game server addresses are routed via `geoip:MORDA-BRAWLSTARS`

Keep Brawl Stars IP entries narrow (`/32`) and only add addresses confirmed from Happ/Xray logs.

## Roblox routing

Roblox uses both domain-based endpoints and game/server IP ranges.

- domains are routed via `geosite:MORDA-PROXY`
- known Roblox IP ranges are routed via `geoip:MORDA-ROBLOX`

## Discord routing

Discord uses domain-based endpoints and some voice/media IP ranges.

- domains are routed via `geosite:MORDA-PROXY` and `geosite:MORDA-DISCORD-EXTRA`
- known Discord voice/media IP ranges are routed via `geoip:MORDA-DISCORD`

## Workflows

- `build-custom-geo` rebuilds `dist/geosite.dat` from `src/geosite/`
- `sync-production-geoip` refreshes upstream `geoip.dat`, appends custom categories from `src/geoip/`, and writes `dist/geoip.dat`

## Source layout

- `src/geosite/` is the source of truth for the custom geosite categories
- `src/geoip/` is the source of truth for custom geoip categories appended to production `dist/geoip.dat`

## Experimental / legacy

These files are kept only for reference and should not be treated as the current production path:

- `build_morda_geo_happ.py`
- `.github/workflows/build-happ-compatible-geo.yml`
