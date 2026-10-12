"""Coordinators for Google Health Vitals."""

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
from google_health_api.model import (
    DailyHeartRateVariability,
    DailyOxygenSaturation,
    DailyRespiratoryRate,
    HeartRateVariability,
    OxygenSaturation,
    RespiratoryRateSleepSummary,
)

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

if TYPE_CHECKING:
    from . import GoogleHealthVitalsConfigEntry

_LOGGER = logging.getLogger(__name__)

POLLING_INTERVAL = timedelta(minutes=15)


class GoogleHealthVitalsCoordinator[_DataT](DataUpdateCoordinator[_DataT]):
    """Base coordinator for Google Health Vitals."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: GoogleHealthVitalsConfigEntry,
        api_client: GoogleHealthApi,
        name: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{name}",
            update_interval=POLLING_INTERVAL,
            config_entry=entry,
        )
        self.api = api_client

    @override
    async def _async_update_data(self) -> _DataT:
        try:
            return await self._async_fetch_data()
        except (HealthAuthException, HealthApiForbiddenException) as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="auth_error"
            ) from err
        except GoogleHealthApiError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN, translation_key="communication_error"
            ) from err

    async def _async_fetch_data(self) -> _DataT:
        """Fetch data from the API."""
        raise NotImplementedError


@dataclass
class OxygenSaturationData:
    """Latest SpO2 readings."""

    latest: OxygenSaturation | None = None
    daily: DailyOxygenSaturation | None = None


class OxygenSaturationCoordinator(GoogleHealthVitalsCoordinator[OxygenSaturationData]):
    """Fetch the latest SpO2 sample and the latest daily (sleep) summary."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: GoogleHealthVitalsConfigEntry,
        api_client: GoogleHealthApi,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, entry, api_client, "oxygen_saturation")

    @override
    async def _async_fetch_data(self) -> OxygenSaturationData:
        # Data points are returned newest first, so one item is the latest.
        latest = await self.api.oxygen_saturation.list(page_size=1)
        daily = await self.api.daily_oxygen_saturation.list(page_size=1)
        return OxygenSaturationData(
            latest=latest.data_points[0].data if latest.data_points else None,
            daily=daily.data_points[0].data if daily.data_points else None,
        )


@dataclass
class HeartRateVariabilityData:
    """Latest heart rate variability readings."""

    latest: HeartRateVariability | None = None
    daily: DailyHeartRateVariability | None = None


class HeartRateVariabilityCoordinator(
    GoogleHealthVitalsCoordinator[HeartRateVariabilityData]
):
    """Fetch the latest HRV sample and the latest daily (sleep) summary."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: GoogleHealthVitalsConfigEntry,
        api_client: GoogleHealthApi,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, entry, api_client, "heart_rate_variability")

    @override
    async def _async_fetch_data(self) -> HeartRateVariabilityData:
        latest = await self.api.heart_rate_variability.list(page_size=1)
        daily = await self.api.daily_heart_rate_variability.list(page_size=1)
        return HeartRateVariabilityData(
            latest=latest.data_points[0].data if latest.data_points else None,
            daily=daily.data_points[0].data if daily.data_points else None,
        )


@dataclass
class RespiratoryRateData:
    """Latest respiratory rate readings."""

    daily: DailyRespiratoryRate | None = None
    sleep: RespiratoryRateSleepSummary | None = None


class RespiratoryRateCoordinator(GoogleHealthVitalsCoordinator[RespiratoryRateData]):
    """Fetch the latest daily respiratory rate and sleep summary."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: GoogleHealthVitalsConfigEntry,
        api_client: GoogleHealthApi,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, entry, api_client, "respiratory_rate")

    @override
    async def _async_fetch_data(self) -> RespiratoryRateData:
        daily = await self.api.daily_respiratory_rate.list(page_size=1)
        sleep = await self.api.respiratory_rate_sleep_summary.list(page_size=1)
        return RespiratoryRateData(
            daily=daily.data_points[0].data if daily.data_points else None,
            sleep=sleep.data_points[0].data if sleep.data_points else None,
        )
