# morda custom geo

Custom geo repo for Xray / RemnaWave / Happ.

## Production model

This repository is split into two independent parts:

- `dist/geosite.dat` is built from the small custom sources in `src/geosite/`
- `dist/geoip.dat` is synced into this repository by workflow for desktop Happ compatibility

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

## Recommended desktop Happ routing profile

```json
{
  "Geoipurl": "https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geoip.dat",
  "Geositeurl": "https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geosite.dat",
  "DirectSites": ["geosite:MORDA-DIRECT"],
  "DirectIp": ["geoip:private"],
  "ProxySites": ["geosite:MORDA-PROXY", "geosite:MORDA-DISCORD-EXTRA"],
  "ProxyIp": ["geoip:telegram"],
  "BlockSites": ["geosite:MORDA-ADS"],
  "BlockIp": []
}
```

## Workflows

- `build-custom-geo` rebuilds only `dist/geosite.dat` from `src/geosite/`
- `sync-production-geoip` refreshes `dist/geoip.dat` inside this repository

## Source layout

- `src/geosite/` is the source of truth for the custom geosite categories
- `src/geoip/telegram-ip.txt` is kept only as reference / legacy input and is not the current production source for `dist/geoip.dat`

## Experimental / legacy

These files are kept only for reference and should not be treated as the current production path:

- `build_morda_geo_happ.py`
- `.github/workflows/build-happ-compatible-geo.yml`
