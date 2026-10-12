# Google Health Vitals

A Home Assistant custom integration that exposes vitals from the
[Google Health API](https://developers.google.com/health) which the built-in
`google_health` integration does not provide (heart rate, SpO2, HRV, respiratory rate and
sleep skin temperature).

It is built on [`google-health-api`](https://github.com/allenporter/python-google-health-api)
and is meant to be upstreamed to Home Assistant core in small pieces.

## Entities

| Entity | Source data type | Notes |
| --- | --- | --- |
| Blood oxygen | `oxygen-saturation` | Latest sample (%) |
| Blood oxygen sample time | `oxygen-saturation` | Timestamp of the latest sample; useful to alert on stale sync |
| Blood oxygen sleep average / minimum / maximum | `daily-oxygen-saturation` | Latest daily summary, calculated during sleep |
| Heart rate variability | `heart-rate-variability` | Latest sample, RMSSD (ms) |
| Heart rate variability sample time | `heart-rate-variability` | Timestamp of the latest sample |
| Heart rate variability sleep average / deep sleep | `daily-heart-rate-variability` | Latest daily summary (ms) |
| Non-REM heart rate | `daily-heart-rate-variability` | Latest daily summary (bpm) |
| Heart rate | `heart-rate` | Latest heart rate sample (bpm) |
| Heart rate sample time | `heart-rate` | Timestamp of the latest sample |
| Respiratory rate | `daily-respiratory-rate` | Latest daily average (breaths/min) |
| Respiratory rate during sleep / REM / deep / light | `respiratory-rate-sleep-summary` | Latest sleep summary (breaths/min) |
| Respiratory rate sample time | `respiratory-rate-sleep-summary` | Timestamp of the latest sleep summary |
| Sleep skin temperature | `daily-sleep-temperature-derivations` | Latest nightly skin temperature (°C) |
| Sleep skin temperature baseline | `daily-sleep-temperature-derivations` | Personal baseline (°C), when available |
| Sleep skin temperature deviation | `daily-sleep-temperature-derivations` | Nightly value minus baseline (°C) |

## Data sources

The Google Health API lists data from every connected source (for example Apple
Health) in a single stream, and the sources report different quantities (Apple
reports SDNN for HRV, Fitbit reports RMSSD). To keep each sensor consistent, only
data recorded by a Fitbit device is used. Values from other sources are ignored.

## Installation (HACS)

1. HACS → Custom repositories → add this repository as an *Integration*.
2. Install **Google Health Vitals** and restart Home Assistant.
3. Add Application Credentials (a Google OAuth *Web application* client; the same
   client as the built-in `google_health` integration can be reused) and add the integration.

The integration requests only the Google Health profile, measurements and sleep read
scopes. If you set it up before sleep skin temperature was added, Home Assistant asks you
to re-authenticate once to grant the sleep scope.

## Status

Early development.

## License

MIT
