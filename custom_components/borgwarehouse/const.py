"""Constants for the BorgWarehouse integration."""
from datetime import timedelta

DOMAIN = "borgwarehouse"

CONF_URL = "url"
CONF_API_KEY = "api_key"

DEFAULT_SCAN_INTERVAL = timedelta(minutes=15)
