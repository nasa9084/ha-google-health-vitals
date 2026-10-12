"""Coordinator for Google Health Vitals."""

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import TYPE_CHECKING, override

from google_health_api import GoogleHealthApi
from google_health_api.exceptions import (
    GoogleHealthApiError,
    HealthApiForbiddenException,
    HealthAuthException,
)
from google_health_api.model import DailyOxygenSaturation, OxygenSaturation

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

if TYPE_CHECKING:
    from . import GoogleHealthVitalsConfigEntry

_LOGGER = logging.getLogger(__name__)

POLLING_INTERVAL = timedelta(minutes=15)


@dataclass
class OxygenSaturationData:
    """Latest SpO2 readings."""

    latest: OxygenSaturation | None = None
    daily: DailyOxygenSaturation | None = None


class OxygenSaturationCoordinator(DataUpdateCoordinator[OxygenSaturationData]):
    """Fetch the latest SpO2 sample and the latest daily (sleep) summary."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: GoogleHealthVitalsConfigEntry,
        api_client: GoogleHealthApi,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_oxygen_saturation",
            update_interval=POLLING_INTERVAL,
            config_entry=entry,
        )
        self.api = api_client

    @override
    async def _async_update_data(self) -> OxygenSaturationData:
        try:
            # Data points are returned newest first, so one item is the latest.
            latest = await self.api.oxygen_saturation.list(page_size=1)
            daily = await self.api.daily_oxygen_saturation.list(page_size=1)
        except (HealthAuthException, HealthApiForbiddenException) as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="auth_error"
            ) from err
        except GoogleHealthApiError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN, translation_key="communication_error"
            ) from err

        return OxygenSaturationData(
            latest=latest.data_points[0].data if latest.data_points else None,
            daily=daily.data_points[0].data if daily.data_points else None,
        )
