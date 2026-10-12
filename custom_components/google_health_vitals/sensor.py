"""Sensor platform for Google Health Vitals."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import GoogleHealthVitalsConfigEntry
from .const import DOMAIN
from .coordinator import OxygenSaturationCoordinator, OxygenSaturationData

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class GoogleHealthVitalsSensorDescription(SensorEntityDescription):
    """Describes a Google Health Vitals sensor."""

    value_fn: Callable[[OxygenSaturationData], float | datetime | None]


def _sample_time(data: OxygenSaturationData) -> datetime | None:
    if data.latest is None:
        return None
    return dt_util.parse_datetime(data.latest.sample_time.physical_time)


SENSORS: tuple[GoogleHealthVitalsSensorDescription, ...] = (
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
        value_fn=_sample_time,
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
        value_fn=lambda data: (
            data.daily.lower_bound_percentage if data.daily else None
        ),
    ),
    GoogleHealthVitalsSensorDescription(
        key="spo2_sleep_maximum",
        translation_key="spo2_sleep_maximum",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: (
            data.daily.upper_bound_percentage if data.daily else None
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GoogleHealthVitalsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        GoogleHealthVitalsSensor(coordinator, entry, description)
        for description in SENSORS
    )


class GoogleHealthVitalsSensor(
    CoordinatorEntity[OxygenSaturationCoordinator], SensorEntity
):
    """A Google Health Vitals sensor."""

    _attr_has_entity_name = True
    entity_description: GoogleHealthVitalsSensorDescription

    def __init__(
        self,
        coordinator: OxygenSaturationCoordinator,
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
