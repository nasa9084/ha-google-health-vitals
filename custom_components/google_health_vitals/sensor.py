"""Sensor platform for Google Health Vitals."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from google_health_api.model.health_metric import ObservationSampleTime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import GoogleHealthVitalsConfigEntry
from .const import DOMAIN
from .coordinator import GoogleHealthVitalsCoordinator

PARALLEL_UPDATES = 0

BEATS_PER_MINUTE = "bpm"


@dataclass(frozen=True, kw_only=True)
class GoogleHealthVitalsSensorDescription(SensorEntityDescription):
    """Describes a Google Health Vitals sensor."""

    value_fn: Callable[[Any], float | datetime | None]


def _timestamp(sample_time: ObservationSampleTime | None) -> datetime | None:
    if sample_time is None:
        return None
    return dt_util.parse_datetime(sample_time.physical_time)


OXYGEN_SATURATION_SENSORS: tuple[GoogleHealthVitalsSensorDescription, ...] = (
    GoogleHealthVitalsSensorDescription(
        key="spo2",
        translation_key="spo2",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.latest.percentage if data.latest else None,
    ),
    GoogleHealthVitalsSensorDescription(
        key="spo2_sample_time",
        translation_key="spo2_sample_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: _timestamp(
            data.latest.sample_time if data.latest else None
        ),
    ),
    GoogleHealthVitalsSensorDescription(
        key="spo2_sleep_average",
        translation_key="spo2_sleep_average",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.daily.average_percentage if data.daily else None,
    ),
    GoogleHealthVitalsSensorDescription(
        key="spo2_sleep_minimum",
        translation_key="spo2_sleep_minimum",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.daily.lower_bound_percentage if data.daily else None,
    ),
    GoogleHealthVitalsSensorDescription(
        key="spo2_sleep_maximum",
        translation_key="spo2_sleep_maximum",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.daily.upper_bound_percentage if data.daily else None,
    ),
)

HEART_RATE_VARIABILITY_SENSORS: tuple[GoogleHealthVitalsSensorDescription, ...] = (
    GoogleHealthVitalsSensorDescription(
        key="hrv",
        translation_key="hrv",
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: (
            data.latest.root_mean_square_of_successive_differences_milliseconds
            if data.latest
            else None
        ),
    ),
    GoogleHealthVitalsSensorDescription(
        key="hrv_sample_time",
        translation_key="hrv_sample_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: _timestamp(
            data.latest.sample_time if data.latest else None
        ),
    ),
    GoogleHealthVitalsSensorDescription(
        key="hrv_sleep_average",
        translation_key="hrv_sleep_average",
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: (
            data.daily.average_heart_rate_variability_milliseconds
            if data.daily
            else None
        ),
    ),
    GoogleHealthVitalsSensorDescription(
        key="hrv_deep_sleep",
        translation_key="hrv_deep_sleep",
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: (
            data.daily.deep_sleep_root_mean_square_of_successive_differences_milliseconds
            if data.daily
            else None
        ),
    ),
    GoogleHealthVitalsSensorDescription(
        key="non_rem_heart_rate",
        translation_key="non_rem_heart_rate",
        native_unit_of_measurement=BEATS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (
            data.daily.non_rem_heart_rate_beats_per_minute if data.daily else None
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GoogleHealthVitalsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensors."""
    data = entry.runtime_data
    async_add_entities(
        GoogleHealthVitalsSensor(coordinator, entry, description)
        for coordinator, descriptions in (
            (data.oxygen_saturation, OXYGEN_SATURATION_SENSORS),
            (data.heart_rate_variability, HEART_RATE_VARIABILITY_SENSORS),
        )
        for description in descriptions
    )


class GoogleHealthVitalsSensor(
    CoordinatorEntity[GoogleHealthVitalsCoordinator[Any]], SensorEntity
):
    """A Google Health Vitals sensor."""

    _attr_has_entity_name = True
    entity_description: GoogleHealthVitalsSensorDescription

    def __init__(
        self,
        coordinator: GoogleHealthVitalsCoordinator[Any],
        entry: GoogleHealthVitalsConfigEntry,
        description: GoogleHealthVitalsSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Google",
            name=entry.title,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    @override
    def native_value(self) -> float | datetime | None:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)
