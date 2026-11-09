"""DataUpdateCoordinator for BorgWarehouse."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_API_KEY, CONF_URL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class BorgWarehouseCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Coordinator to fetch BorgWarehouse repository stats."""

    def __init__(self, hass: HomeAssistant, entry_data: dict[str, Any]) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.url = entry_data[CONF_URL].rstrip("/")
        self.api_key = entry_data[CONF_API_KEY]
        self.session = async_get_clientsession(hass)

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch repository data from BorgWarehouse."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        endpoint = f"{self.url}/api/v1/repositories"

        try:
            async with self.session.get(endpoint, headers=headers, timeout=15) as resp:
                if resp.status in (401, 403):
                    raise UpdateFailed("Authentication failed: Invalid or expired API token.")
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP error {resp.status} while fetching repositories from BorgWarehouse.")

                data = await resp.json()

                if isinstance(data, dict):
                    repo_list = data.get("repoList") or data.get("repositories") or data.get("data") or []
                elif isinstance(data, list):
                    repo_list = data
                else:
                    repo_list = []

                repositories: dict[str, dict[str, Any]] = {}
                for repo in repo_list:
                    repo_id = str(repo.get("repositoryName") or repo.get("id") or repo.get("name") or "")
                    if repo_id:
                        repositories[repo_id] = repo

                return repositories
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Failed to communicate with BorgWarehouse: {err}") from err
