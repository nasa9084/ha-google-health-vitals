# Google Health Vitals

A Home Assistant custom integration that exposes vitals from the
[Google Health API](https://developers.google.com/health) which the built-in
`google_health` integration does not provide (SpO2 first; HRV, respiratory rate
and sleep skin temperature are planned).

It is built on [`google-health-api`](https://github.com/allenporter/python-google-health-api)
and is meant to be upstreamed to Home Assistant core in small pieces.

## Entities

| Entity | Source data type | Notes |
| --- | --- | --- |
| Blood oxygen | `oxygen-saturation` | Latest sample (%) |
| Blood oxygen sample time | `oxygen-saturation` | Timestamp of the latest sample; useful to alert on stale sync |
| Blood oxygen sleep average / minimum / maximum | `daily-oxygen-saturation` | Latest daily summary, calculated during sleep |

## Installation (HACS)

1. HACS → Custom repositories → add this repository as an *Integration*.
2. Install **Google Health Vitals** and restart Home Assistant.
3. Add Application Credentials (a Google OAuth *Web application* client; the same
   client as the built-in `google_health` integration can be reused) and add the integration.

The integration requests only the Google Health profile read scope and the
measurements read scope only.

## Status

Early development.

## License

MIT
