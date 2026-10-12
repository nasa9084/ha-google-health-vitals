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
from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfTime
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
BREATHS_PER_MINUTE = "breaths/min"


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


def _sleep_stat(stage: str) -> Callable[[Any], float | None]:
    def value_fn(data: Any) -> float | None:
        stats = getattr(data.sleep, stage, None) if data.sleep else None
        return stats.breaths_per_minute if stats else None

    return value_fn


RESPIRATORY_RATE_SENSORS: tuple[GoogleHealthVitalsSensorDescription, ...] = (
    GoogleHealthVitalsSensorDescription(
        key="respiratory_rate",
        translation_key="respiratory_rate",
        native_unit_of_measurement=BREATHS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.daily.breaths_per_minute if data.daily else None,
    ),
    GoogleHealthVitalsSensorDescription(
        key="respiratory_rate_sleep",
        translation_key="respiratory_rate_sleep",
        native_unit_of_measurement=BREATHS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_sleep_stat("full_sleep_stats"),
    ),
    GoogleHealthVitalsSensorDescription(
        key="respiratory_rate_rem_sleep",
        translation_key="respiratory_rate_rem_sleep",
        native_unit_of_measurement=BREATHS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_sleep_stat("rem_sleep_stats"),
    ),
    GoogleHealthVitalsSensorDescription(
        key="respiratory_rate_deep_sleep",
        translation_key="respiratory_rate_deep_sleep",
        native_unit_of_measurement=BREATHS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_sleep_stat("deep_sleep_stats"),
    ),
    GoogleHealthVitalsSensorDescription(
        key="respiratory_rate_light_sleep",
        translation_key="respiratory_rate_light_sleep",
        native_unit_of_measurement=BREATHS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_sleep_stat("light_sleep_stats"),
    ),
    GoogleHealthVitalsSensorDescription(
        key="respiratory_rate_sample_time",
        translation_key="respiratory_rate_sample_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: _timestamp(
            data.sleep.sample_time if data.sleep else None
        ),
    ),
)

SLEEP_SKIN_TEMPERATURE_SENSORS: tuple[GoogleHealthVitalsSensorDescription, ...] = (
    GoogleHealthVitalsSensorDescription(
        key="sleep_skin_temperature",
        translation_key="sleep_skin_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.nightly_temperature_celsius if data else None,
    ),
    GoogleHealthVitalsSensorDescription(
        key="sleep_skin_temperature_baseline",
        translation_key="sleep_skin_temperature_baseline",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.baseline_temperature_celsius if data else None,
    ),
    GoogleHealthVitalsSensorDescription(
        key="sleep_skin_temperature_deviation",
        translation_key="sleep_skin_temperature_deviation",
        device_class=SensorDeviceClass.TEMPERATURE_DELTA,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: (
            data.nightly_temperature_celsius - data.baseline_temperature_celsius
            if data and data.baseline_temperature_celsius is not None
            else None
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
            (data.respiratory_rate, RESPIRATORY_RATE_SENSORS),
            (data.sleep_skin_temperature, SLEEP_SKIN_TEMPERATURE_SENSORS),
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
