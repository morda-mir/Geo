# Current status

## Production-safe setup

Use only the URLs from this repository:

- `Geositeurl`: `https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geosite.dat`
- `Geoipurl`: `https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geoip.dat`

Working categories:

- `geosite:MORDA-DIRECT`
- `geosite:MORDA-PROXY`
- `geosite:MORDA-TT`
- `geosite:MORDA-ADS`
- `geosite:MORDA-DISCORD-EXTRA`
- `geoip:private`
- `geoip:telegram`
- `geoip:MORDA-BRAWLSTARS`
- `geoip:MORDA-ROBLOX`
- `geoip:MORDA-DISCORD`
- `geoip:MORDA-OPENAI`

## Important note

The production `dist/geoip.dat` is mirrored from the upstream production geoip file and extended with custom categories from `src/geoip/` for desktop Happ compatibility.

## Recommended desktop Happ routing profile

```json
{
  "Geoipurl": "https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geoip.dat",
  "Geositeurl": "https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geosite.dat",
  "DirectSites": ["geosite:MORDA-DIRECT"],
  "DirectIp": ["geoip:private"],
  "ProxySites": ["geosite:MORDA-PROXY", "geosite:MORDA-TT", "geosite:MORDA-DISCORD-EXTRA"],
  "ProxyIp": ["geoip:telegram", "geoip:MORDA-BRAWLSTARS", "geoip:MORDA-ROBLOX", "geoip:MORDA-DISCORD", "geoip:MORDA-OPENAI"],
  "BlockSites": ["geosite:MORDA-ADS"],
  "BlockIp": []
}
```

## How to work with geo

1. Edit domain rules in `src/geosite/*`.
2. Edit IP ranges in `src/geoip/*`.
3. Push source changes to `main`.
4. Wait for Actions to regenerate `dist/*.dat`.
5. Ask clients to refresh geo files only after workflow success.

## How to push safely

1. Do not manually edit `dist/*.dat`.
2. Avoid parallel manual pushes while Actions are committing generated `dist` files.
3. If a workflow fails on push conflict, rerun the failed workflow after latest `main` is available.
