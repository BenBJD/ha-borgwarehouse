"""Sensor platform for BorgWarehouse integration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import BorgWarehouseCoordinator


@dataclass(frozen=True, kw_only=True)
class BorgWarehouseSensorEntityDescription(SensorEntityDescription):
    """Describes a BorgWarehouse sensor entity."""

    value_fn: Callable[[dict[str, Any]], Any]


def _parse_timestamp(raw_value: Any) -> datetime | None:
    """Parse string or epoch timestamp into a UTC datetime."""
    if not raw_value:
        return None
    if isinstance(raw_value, datetime):
        return raw_value
    try:
        # Check if Unix timestamp (int or float)
        if isinstance(raw_value, (int, float)):
            return dt_util.utc_from_timestamp(raw_value)
        if isinstance(raw_value, str) and raw_value.replace(".", "", 1).isdigit():
            return dt_util.utc_from_timestamp(float(raw_value))
        return dt_util.parse_datetime(str(raw_value))
    except Exception:
        return None


def _get_storage_used_bytes(repo: dict[str, Any]) -> int | None:
    """Extract storage used in bytes (BorgWarehouse reports storageUsed in KB)."""
    val = (
        repo.get("storageUsed")
        or repo.get("storage_used")
        or repo.get("size")
        or repo.get("total_size")
    )
    if val is not None:
        try:
            # BorgWarehouse storageUsed is in Kilobytes (from du -k)
            return int(float(val) * 1024)
        except (ValueError, TypeError):
            pass
    return None


def _get_quota_bytes(repo: dict[str, Any]) -> int | None:
    """Extract storage quota normalized to bytes (BorgWarehouse reports storageSize in GB)."""
    raw = (
        repo.get("storageSize")
        or repo.get("quota")
        or repo.get("storageQuota")
        or repo.get("quotaSize")
        or repo.get("maxStorage")
    )
    if raw is None:
        return None
    try:
        val = float(raw)
        if val <= 0:
            return None
        # In BorgWarehouse, storageSize is configured in GB
        if val < 1_000_000:
            return int(val * (1024**3))
        return int(val)
    except (ValueError, TypeError):
        return None


def _calc_usage_percent(repo: dict[str, Any]) -> float | None:
    """Calculate percentage of storage used."""
    storage_used = _get_storage_used_bytes(repo)
    quota = _get_quota_bytes(repo)

    if storage_used is not None and quota and quota > 0:
        return round((storage_used / quota) * 100, 2)
    return None


def _get_last_backup(repo: dict[str, Any]) -> datetime | None:
    """Extract and parse the last backup timestamp (BorgWarehouse field: lastSave)."""
    candidates = [
        repo.get("lastSave"),
        repo.get("lastBackup"),
        repo.get("last_backup"),
        repo.get("latestBackup"),
        repo.get("lastArchive"),
        repo.get("updatedAt"),
    ]
    for candidate in candidates:
        if candidate is not None:
            parsed = _parse_timestamp(candidate)
            if parsed:
                return parsed
    return None


SENSOR_DESCRIPTIONS: tuple[BorgWarehouseSensorEntityDescription, ...] = (
    BorgWarehouseSensorEntityDescription(
        key="storage_used",
        name="Storage used",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_get_storage_used_bytes,
    ),
    BorgWarehouseSensorEntityDescription(
        key="quota",
        name="Quota",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        value_fn=_get_quota_bytes,
    ),
    BorgWarehouseSensorEntityDescription(
        key="usage_percent",
        name="Storage usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_calc_usage_percent,
    ),
    BorgWarehouseSensorEntityDescription(
        key="last_backup",
        name="Last backup",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_get_last_backup,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BorgWarehouse sensors based on a config entry."""
    coordinator: BorgWarehouseCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BorgWarehouseSensor] = []
    for repo_id in coordinator.data:
        for description in SENSOR_DESCRIPTIONS:
            entities.append(BorgWarehouseSensor(coordinator, repo_id, description))

    async_add_entities(entities)


class BorgWarehouseSensor(CoordinatorEntity[BorgWarehouseCoordinator], SensorEntity):
    """Sensor representing a BorgWarehouse repository attribute."""

    _attr_has_entity_name = True
    entity_description: BorgWarehouseSensorEntityDescription

    def __init__(
        self,
        coordinator: BorgWarehouseCoordinator,
        repo_id: str,
        description: BorgWarehouseSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.repo_id = repo_id
        self.entity_description = description

        repo_data = coordinator.data.get(repo_id, {})
        display_name = repo_data.get("alias") or repo_data.get("repositoryName") or repo_id

        self._attr_unique_id = f"{repo_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, repo_id)},
            name=display_name,
            manufacturer="BorgWarehouse",
            model="Borg Repository",
            configuration_url=coordinator.url,
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        repo = self.coordinator.data.get(self.repo_id, {})
        return self.entity_description.value_fn(repo)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return optional additional repository attributes."""
        repo = self.coordinator.data.get(self.repo_id, {})
        attrs: dict[str, Any] = {}
        if self.entity_description.key == "storage_used":
            if "appendOnlyMode" in repo:
                attrs["append_only_mode"] = repo["appendOnlyMode"]
            if "alert" in repo:
                attrs["alert_threshold_seconds"] = repo["alert"]
            if "repositoryName" in repo:
                attrs["repository_name"] = repo["repositoryName"]
            if "comment" in repo and repo["comment"]:
                attrs["comment"] = repo["comment"]
        return attrs
