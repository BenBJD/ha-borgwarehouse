"""Config flow for BorgWarehouse integration."""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_API_KEY, CONF_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL, default="https://"): str,
        vol.Required(CONF_API_KEY): str,
    }
)


class BorgWarehouseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BorgWarehouse."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input[CONF_URL].strip().rstrip("/")
            api_key = user_input[CONF_API_KEY].strip()

            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                errors["base"] = "invalid_url"
            else:
                session = async_get_clientsession(self.hass)
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "application/json",
                }
                test_endpoint = f"{url}/api/v1/repositories"

                try:
                    async with session.get(test_endpoint, headers=headers, timeout=10) as resp:
                        if resp.status == 200:
                            await self.async_set_unique_id(url.lower())
                            self._abort_if_unique_id_configured()

                            title = f"BorgWarehouse ({parsed.netloc})"
                            return self.async_create_entry(
                                title=title,
                                data={CONF_URL: url, CONF_API_KEY: api_key},
                            )
                        elif resp.status in (401, 403):
                            errors["base"] = "invalid_auth"
                        else:
                            errors["base"] = "cannot_connect"
                except Exception as err:
                    _LOGGER.warning("Could not connect to BorgWarehouse: %s", err)
                    errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
