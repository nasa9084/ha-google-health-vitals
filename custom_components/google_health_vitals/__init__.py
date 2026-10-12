"""The Google Health Vitals integration."""

import asyncio
from dataclasses import dataclass

from google_health_api import GoogleHealthApi
from google_health_api.const import HealthApiScope

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_config_entry_implementation,
)

from . import api
from .const import DOMAIN
from .coordinator import (
    HeartRateVariabilityCoordinator,
    OxygenSaturationCoordinator,
    RespiratoryRateCoordinator,
)

_PLATFORMS: list[Platform] = [Platform.SENSOR]


@dataclass
class GoogleHealthVitalsData:
    """Coordinators of a Google Health Vitals config entry."""

    oxygen_saturation: OxygenSaturationCoordinator
    heart_rate_variability: HeartRateVariabilityCoordinator
    respiratory_rate: RespiratoryRateCoordinator


type GoogleHealthVitalsConfigEntry = ConfigEntry[GoogleHealthVitalsData]


async def async_setup_entry(
    hass: HomeAssistant, entry: GoogleHealthVitalsConfigEntry
) -> bool:
    """Set up Google Health Vitals from a config entry."""
    implementation = await async_get_config_entry_implementation(hass, entry)
    session = OAuth2Session(hass, entry, implementation)

    scopes = session.token.get("scope", "").split()
    if HealthApiScope.MEASUREMENTS_READ not in scopes:
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN, translation_key="missing_scope"
        )

    auth = api.AsyncConfigEntryAuth(
        aiohttp_client.async_get_clientsession(hass), session
    )
    api_client = GoogleHealthApi(auth)
    data = GoogleHealthVitalsData(
        oxygen_saturation=OxygenSaturationCoordinator(hass, entry, api_client),
        heart_rate_variability=HeartRateVariabilityCoordinator(hass, entry, api_client),
        respiratory_rate=RespiratoryRateCoordinator(hass, entry, api_client),
    )
    await asyncio.gather(
        data.oxygen_saturation.async_config_entry_first_refresh(),
        data.heart_rate_variability.async_config_entry_first_refresh(),
        data.respiratory_rate.async_config_entry_first_refresh(),
    )
    entry.runtime_data = data

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: GoogleHealthVitalsConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
