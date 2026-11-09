"""Binary sensor platform for BorgWarehouse repository health."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BorgWarehouseCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors for BorgWarehouse."""
    coordinator: BorgWarehouseCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        BorgWarehouseHealthBinarySensor(coordinator, repo_id)
        for repo_id in coordinator.data
    ]
    async_add_entities(entities)


class BorgWarehouseHealthBinarySensor(CoordinatorEntity[BorgWarehouseCoordinator], BinarySensorEntity):
    """Binary sensor indicating if a repository has a problem or is unreachable."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_name = "Problem"

    def __init__(self, coordinator: BorgWarehouseCoordinator, repo_id: str) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.repo_id = repo_id

        repo_data = coordinator.data.get(repo_id, {})
        display_name = repo_data.get("alias") or repo_data.get("repositoryName") or repo_id

        self._attr_unique_id = f"{repo_id}_problem"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, repo_id)},
            name=display_name,
            manufacturer="BorgWarehouse",
            model="Borg Repository",
            configuration_url=coordinator.url,
        )

    @property
    def is_on(self) -> bool:
        """Return True if there is a problem with the repository."""
        repo = self.coordinator.data.get(self.repo_id, {})
        status = repo.get("status")

        if status is None:
            return False

        if isinstance(status, bool):
            return not status

        # String representations
        return str(status).strip().lower() not in ("healthy", "ok", "true", "active", "up")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes."""
        repo = self.coordinator.data.get(self.repo_id, {})
        return {
            "raw_status": repo.get("status"),
        }
