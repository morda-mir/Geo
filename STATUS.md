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

## Important note

The production `dist/geoip.dat` is mirrored into this repository for desktop Happ compatibility.
It is not the same thing as the legacy custom geoip experiments in this repo.

## Recommended desktop Happ routing profile

```json
{
  "Geoipurl": "https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geoip.dat",
  "Geositeurl": "https://raw.githubusercontent.com/morda-mir/Geo/main/dist/geosite.dat",
  "DirectSites": [],
  "DirectIp": ["geoip:private"],
  "ProxySites": ["geosite:MORDA-PROXY", "geosite:MORDA-DISCORD-EXTRA"],
  "ProxyIp": ["geoip:telegram"],
  "BlockSites": ["geosite:MORDA-ADS"],
  "BlockIp": []
}
```
