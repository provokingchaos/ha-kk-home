"""Constants for the KK Home integration."""

from __future__ import annotations

DOMAIN = "kkhome"
DEFAULT_NAME = "KK Home"
PLATFORMS = ["lock", "switch", "sensor"]

CONF_USERNAME = "username"
CONF_PASSWORD = "password"

DEFAULT_BASE_URL = "https://api.kksecurityhome.com"
DEFAULT_TENANT_ID = "kawden"
DEFAULT_POLL_INTERVAL = 30

# API Endpoints
LOGIN_PATH = "/v3/user/login/get-user-by-mail"
DEVICES_PATH = "/v3/user/device/list"
DEVICE_DETAIL_PATH = "/v4/device/query-device-attr"
STATUS_PATH = "/v3/device/get-open-status"
LOCK_PATH = "/v3/device/close-device"
UNLOCK_PATH = "/v3/device/open-device"
GATEWAY_LOCK_PATH = "/v3/gateway/set-lock-close"
GATEWAY_UNLOCK_PATH = "/v3/gateway/set-lock-open"
GATEWAY_POWER_PATH = "/v3/gateway/set-gateway-power"
