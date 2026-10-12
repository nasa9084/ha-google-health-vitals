"""Coordinators for Google Health Vitals."""

from collections.abc import Sequence
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
    DataPoint,
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
PAGE_SIZE = 20
FITBIT_PLATFORM = "FITBIT"


def _latest_from_fitbit[_T](data_points: Sequence[DataPoint[_T]] | None) -> _T | None:
    """Return the newest data point recorded by a Fitbit device.

    The API lists points from every connected source (for example Apple Health)
    in one stream. Other sources report different quantities, such as SDNN
    instead of RMSSD for HRV, so mixing them makes the series inconsistent.
    """
    for point in data_points or ():
        if point.data_source and point.data_source.platform == FITBIT_PLATFORM:
            return point.data
    return None


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
            data = await self._async_fetch_data()
        except (HealthAuthException, HealthApiForbiddenException) as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="auth_error"
            ) from err
        except GoogleHealthApiError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN, translation_key="communication_error"
            ) from err
        _LOGGER.debug("Fetched %s: %s", self.name, data)
        return data

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
        latest = await self.api.oxygen_saturation.list(page_size=PAGE_SIZE)
        daily = await self.api.daily_oxygen_saturation.list(page_size=PAGE_SIZE)
        return OxygenSaturationData(
            latest=_latest_from_fitbit(latest.data_points),
            daily=_latest_from_fitbit(daily.data_points),
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
        latest = await self.api.heart_rate_variability.list(page_size=PAGE_SIZE)
        daily = await self.api.daily_heart_rate_variability.list(page_size=PAGE_SIZE)
        return HeartRateVariabilityData(
            latest=_latest_from_fitbit(latest.data_points),
            daily=_latest_from_fitbit(daily.data_points),
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
        daily = await self.api.daily_respiratory_rate.list(page_size=PAGE_SIZE)
        sleep = await self.api.respiratory_rate_sleep_summary.list(page_size=PAGE_SIZE)
        return RespiratoryRateData(
            daily=_latest_from_fitbit(daily.data_points),
            sleep=_latest_from_fitbit(sleep.data_points),
        )
