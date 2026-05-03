# Current status

## Production-safe setup

Use only the URLs from this repository:

- `Geositeurl`: `https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geosite.dat`
- `Geoipurl`: `https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geoip.dat`

Working categories:

- `geosite:MORDA-PROXY`
- `geosite:MORDA-ADS`
- `geosite:MORDA-DISCORD-EXTRA`
- `geoip:private`
- `geoip:telegram`
- `geoip:MORDA-BRAWLSTARS`

## Important note

The production `dist/geoip.dat` is mirrored from the upstream production geoip file and extended with custom categories from `src/geoip/` for desktop Happ compatibility.

## Recommended desktop Happ routing profile

```json
{
  "Geoipurl": "https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geoip.dat",
  "Geositeurl": "https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geosite.dat",
  "DirectSites": ["geosite:MORDA-DIRECT"],
  "DirectIp": ["geoip:private"],
  "ProxySites": ["geosite:MORDA-PROXY", "geosite:MORDA-DISCORD-EXTRA"],
  "ProxyIp": ["geoip:telegram", "geoip:MORDA-BRAWLSTARS"],
  "BlockSites": ["geosite:MORDA-ADS"],
  "BlockIp": []
}
```
