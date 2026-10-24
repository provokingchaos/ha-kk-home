"""Async API client for KK Home with RSA encryption and auto-relogin."""

from __future__ import annotations

import asyncio
from base64 import b64decode, b64encode, urlsafe_b64decode
import json
import logging
import time
from typing import Any

import aiohttp
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    DEFAULT_BASE_URL,
    DEFAULT_TENANT_ID,
    DEVICES_PATH,
    GATEWAY_LOCK_PATH,
    GATEWAY_POWER_PATH,
    GATEWAY_UNLOCK_PATH,
    LOCK_PATH,
    LOGIN_PATH,
    UNLOCK_PATH,
)

_LOGGER = logging.getLogger(__name__)

_APP_PRIVATE_KEY = b64decode(
    "MIICXgIBAAKBgQC7M6FvIfDuzM3/QHcYKz5LcPcBm3829kb2UCH/GJThmMjiPqWQzN7Zzh666lSnWIB1mPa6xLQMRUsd/eNH68fWTYcrqnBXunVgkf56ppD9QZTf4y8IbEAetWiyGDp/4rVG3nsPKXYQTFgN59gzZ++qdtAehsGaC+dce96cNcvowQIDAQABAoGAXDGtS6IXmkPbH96LyKdjYpwbyfreyB66DAyi8ZMVn5UzOdlIiOucxP+yOrO1RUVc3o2a1ZiSY4is2fRzvrPsElMVQaX/wxCF73dqeJvZ8w2Y5izaR04DO5Q3GReVAupXjS0aGuWVzik+w+oTzGxKr9JE5ZFT/de94dULxRzMvAECQQDiSikSfTYv7fHhknfOVhgSJ4lKsgj48x5Bb3MONIJl1yRnYVm8NnXzg7Zga7CurhyLTqaZl6Wz0QiepIFy0sHxAkEA08euJNXW0sMT+Qc3XXXiHITBDjCBHRyjX0xsIf3pcRwBPhgG90jGGuyKOJYNZhu8U/mV9CGd9JBVrlq73RHD0QJBAKs1swejJslyvWyO9ghuiT3LHgwe0b0RrNWTbjjUL8i/03JIbK2DgxCgme8v63jukPgxpMlWvG9le6EUFED9BvECQQCVEgInlYoQcxZ0/TpghCDz+BI4XbYUetsYsp+O0b7nSlIplhoZKFWiEAw/RogJ7s4CwjVmUd9wjcRx5RZFx0JxAkEA0g9KjPzq+duwEnqADu6ls0fzTD8rpkYzukxlNSAFdHMVLnXoRlbmAqS3VcnNkcDJOkYTWXLxPuMGbf4YT0f3BA=="
)
_SERVICE_PUBLIC_KEY = b64decode(
    "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDAhvfVLGrJ/M3xpUnT1xlN30E1UESxhAmGmFyTx3p3vpxF4zMYpUjwHckCvg/zvZwhNTgsm3CNT7LAdE8lCl2YK4BoUZ6IYbbXSOa02/brASX4kjpOPbTcaDfYud2CFWQba95d5dlf3Jf9Z3eTPwNK7YQ0LDDWMOQ6LxoGqcLciQIDAQAB"
)
_ENCRYPT_DATA_HEADER = "encrypt_data"
_AUTH_REFRESH_SKEW_SECONDS = 300
_APP_VERSION = "3.5.0"
_PHONE_NAME = "iPhone19,3"
_USER_AGENT = "KKHome/3.5.0 (iPhone; iOS 27.0.1; Scale/3.00)"


class KKHomeApiError(Exception):
    """Raised when the KK Home API returns an error."""


class KKHomeAuthError(KKHomeApiError):
    """Raised when authentication fails."""


class KKHomeApiClient:
    """Cloud API client for KK Home."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize the client."""
        self._hass = hass
        self._session = async_get_clientsession(hass)
        self._username: str = config.get(CONF_USERNAME, "")
        self._password: str = config.get(CONF_PASSWORD, "")
        self._token: str | None = config.get("token")
        self._token_expires_at: int | None = self._decode_token_expiration(self._token)
        self._private_key = serialization.load_der_private_key(_APP_PRIVATE_KEY, password=None)
        self._public_key = serialization.load_der_public_key(_SERVICE_PUBLIC_KEY)
        self._auth_lock = asyncio.Lock()

    def _get_headers(self, include_token: bool = True) -> dict[str, str]:
        """Build standard KK Home headers."""
        headers = {
            "Host": "api.kksecurityhome.com",
            "Accept": "*/*",
            "k-language": "en_US",
            "k-signv": "1.0.0",
            "k-tenant": DEFAULT_TENANT_ID,
            "k-version": _APP_VERSION,
            "phoneName": _PHONE_NAME,
            "User-Agent": _USER_AGENT,
        }
        if include_token and self._token:
            headers["token"] = self._token
        return headers

    async def async_authenticate(self) -> str:
        """Authenticate using email and password with RSA encryption."""
        async with self._auth_lock:
            if self._token and not self._token_needs_refresh():
                return self._token

            if not self._username or not self._password:
                raise KKHomeAuthError("Username and password are required.")

            payload = {"mail": self._username, "password": self._password}
            encrypted_body = self._encrypt_payload(payload)

            data = await self._request(
                LOGIN_PATH,
                json_body=encrypted_body,
                extra_headers={_ENCRYPT_DATA_HEADER: _ENCRYPT_DATA_HEADER},
                allow_unauthenticated=True,
            )

            token = self._find_token(data)
            if not token:
                raise KKHomeAuthError("Login succeeded, but no token was found in response.")

            self._token = token
            self._token_expires_at = self._decode_token_expiration(token)
            _LOGGER.debug("Successfully authenticated KK Home user %s", self._username)
            return token

    async def async_get_devices(self) -> dict[str, dict[str, Any]]:
        """Fetch and parse both gateways and locks."""
        await self.async_authenticate()
        raw_data = await self._request(DEVICES_PATH)
        devices_list = self._extract_devices_list(raw_data)
        return self._parse_devices(devices_list)

    async def async_set_lock(self, lock_info: dict[str, Any], lock: bool) -> None:
        """Lock or unlock a device using the encrypted gateway command path."""
        esn = lock_info.get("id")
        master_sn = lock_info.get("master_sn")

        _LOGGER.debug(
            "KK Home gateway encrypted lock command for ESN: %s, master_sn: %s, action: %s",
            esn,
            master_sn,
            "LOCK" if lock else "UNLOCK",
        )

        gw_path = GATEWAY_LOCK_PATH if lock else GATEWAY_UNLOCK_PATH
        payload: dict[str, Any] = {"esn": esn}
        if master_sn:
            payload["masterSn"] = master_sn

        response = await self._request(
            gw_path,
            json_body=self._encrypt_payload(payload),
            extra_headers={_ENCRYPT_DATA_HEADER: _ENCRYPT_DATA_HEADER},
        )
        _LOGGER.debug("Gateway encrypted lock command response: %s", response)

    async def async_set_gateway_power(self, gw_id: str, power_on: bool) -> None:
        """Turn gateway power switch on or off."""
        payload = {
            "esn": gw_id,
            "powerStatus": 1 if power_on else 0,
        }
        await self._request(
            GATEWAY_POWER_PATH,
            json_body=self._sign_payload(payload),
        )

    async def _request(
        self,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
        allow_unauthenticated: bool = False,
        retry_on_auth_failure: bool = True,
    ) -> Any:
        """Execute an HTTP POST request with automatic raw-byte decoding, RSA decryption, and relogin."""
        if not allow_unauthenticated and self._token_needs_refresh():
            await self.async_authenticate()

        url = f"{DEFAULT_BASE_URL}{path}"
        headers = self._get_headers(include_token=not allow_unauthenticated)
        if extra_headers:
            headers.update(extra_headers)

        if json_body is not None:
            headers["Content-Type"] = "application/json"
        else:
            headers["Content-Length"] = "0"

        try:
            async with self._session.post(
                url,
                headers=headers,
                json=json_body,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as response:
                body_bytes = await response.read()
                text = body_bytes.decode("utf-8", errors="replace")
                status_code = response.status
        except aiohttp.ClientError as err:
            raise KKHomeApiError(f"Network error communicating with {url}: {err}") from err

        try:
            parsed: Any = json.loads(text) if text else {}
        except json.JSONDecodeError as err:
            raise KKHomeApiError(f"Invalid JSON from {url}: {text}") from err

        # Decrypt response if wrapped in encryptData
        if isinstance(parsed, dict) and "encryptData" in parsed and isinstance(parsed["encryptData"], str):
            try:
                parsed = self._decrypt_response(parsed["encryptData"])
            except Exception as err:
                raise KKHomeApiError(f"Failed to decrypt response from {url}: {err}") from err

        # Check for HTTP 401/403 or API token expiration codes
        if status_code in (401, 403) or (
            isinstance(parsed, dict) and self._response_needs_reauthentication(parsed)
        ):
            if not allow_unauthenticated and retry_on_auth_failure:
                _LOGGER.info("KK Home token expired; re-authenticating automatically.")
                self._token = None
                await self.async_authenticate()
                return await self._request(
                    path,
                    json_body=json_body,
                    extra_headers=extra_headers,
                    allow_unauthenticated=allow_unauthenticated,
                    retry_on_auth_failure=False,
                )
            msg = parsed.get("msg") if isinstance(parsed, dict) else text
            raise KKHomeAuthError(f"Authentication failed: {msg}")

        if status_code >= 400:
            raise KKHomeApiError(f"HTTP {status_code} from {url}: {text}")

        if isinstance(parsed, dict):
            code = parsed.get("code")
            if code is not None and code not in (0, 200, "0", "200"):
                msg = parsed.get("msg") or parsed.get("message") or f"Code {code}"
                if allow_unauthenticated:
                    raise KKHomeAuthError(f"Login rejected ({code}): {msg}")
                raise KKHomeApiError(f"API error ({code}): {msg}")

            if "data" in parsed:
                return parsed["data"]

        return parsed

    def _parse_devices(self, raw_devices: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Parse raw device list into gateways and locks without losing subDevice live data."""
        parsed_data: dict[str, dict[str, Any]] = {
            "gateways": {},
            "locks": {},
        }

        # Pass 1: Parse top-level standalone LOCK entries (contains userNumberId and bleMac)
        for device in raw_devices:
            esn = str(device.get("wifiSN") or device.get("esn") or device.get("_id") or "")
            if not esn:
                continue
            dev_type = str(device.get("deviceType", "")).upper()
            if dev_type != "GATEWAY" and "subDevices" not in device:
                parsed_data["locks"][esn] = {
                    "id": esn,
                    "master_sn": device.get("masterSn"),
                    "user_number_id": device.get("userNumberId") if device.get("userNumberId") is not None else 0,
                    "name": device.get("lockNickname") or device.get("name") or "KK Lock",
                    "open_status": device.get("openStatus"),
                    "battery": self._extract_battery(device.get("power") or device.get("battery")),
                    "firmware": device.get("lockFirmwareVersion"),
                    "online": str(device.get("online", "1")) == "1",
                    "rssi": device.get("rssi"),
                    "raw": device,
                }

        # Pass 2: Parse GATEWAY entries and overlay live subDevices state (true battery & openStatus)
        for device in raw_devices:
            esn = str(device.get("wifiSN") or device.get("esn") or device.get("_id") or "")
            if not esn:
                continue
            dev_type = str(device.get("deviceType", "")).upper()
            if dev_type == "GATEWAY" or "subDevices" in device:
                parsed_data["gateways"][esn] = {
                    "id": esn,
                    "name": device.get("lockNickname") or device.get("name") or "KK Wi-Fi Bridge",
                    "power_status": device.get("gwPowerStatus"),
                    "led_status": device.get("gwLedStatus"),
                    "power": device.get("power"),
                    "ip": device.get("ip"),
                    "wifi_signal": device.get("wifiSignal"),
                    "online": str(device.get("online", "1")) == "1",
                    "raw": device,
                }

                for sub in device.get("subDevices", []):
                    if not isinstance(sub, dict):
                        continue
                    sub_esn = str(sub.get("wifiSN") or sub.get("esn") or sub.get("mac") or "")
                    if not sub_esn:
                        continue
                    existing = parsed_data["locks"].get(sub_esn, {})
                    user_num = sub.get("userNumberId")
                    if user_num is None:
                        user_num = existing.get("user_number_id")
                    if user_num is None:
                        user_num = device.get("userNumberId", 0)

                    sub_battery = self._extract_battery(sub.get("power") or sub.get("battery"))
                    merged_raw = {**existing.get("raw", {}), **sub}

                    parsed_data["locks"][sub_esn] = {
                        "id": sub_esn,
                        "master_sn": esn,
                        "user_number_id": user_num,
                        "name": sub.get("lockNickname") or existing.get("name") or "KK Lock",
                        "open_status": sub.get("openStatus", existing.get("open_status")),
                        "battery": sub_battery if sub_battery is not None else existing.get("battery"),
                        "firmware": sub.get("lockFirmwareVersion") or existing.get("firmware"),
                        "online": str(sub.get("online", "1")) == "1",
                        "rssi": sub.get("rssi") or existing.get("rssi"),
                        "raw": merged_raw,
                    }

        return parsed_data

    @staticmethod
    def _extract_battery(val: Any) -> int | None:
        """Extract valid 0-100 battery percentage (ignores 200 placeholder on top-level lock)."""
        if isinstance(val, bool) or val is None:
            return None
        parsed: int | None = None
        if isinstance(val, (int, float)):
            parsed = int(val)
        elif isinstance(val, str) and val.strip().isdigit():
            parsed = int(val.strip())
        if parsed is not None and 0 <= parsed <= 100:
            return parsed
        return None

    def _extract_devices_list(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for key in ("records", "rows", "list", "devices", "deviceList", "items", "data"):
                val = payload.get(key)
                if isinstance(val, list):
                    return [item for item in val if isinstance(item, dict)]
        return []

    def _sign_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Sign payload using the app's RSA private key and SHA256."""
        signed_payload = dict(payload)
        signed_payload["reqTime"] = str(int(time.time() * 1000))
        sorted_json = json.dumps(signed_payload, sort_keys=True, separators=(",", ":"))
        signature = self._private_key.sign(
            sorted_json.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        signed_payload["sign"] = b64encode(signature).decode("utf-8")
        return signed_payload

    def _encrypt_payload(self, payload: dict[str, Any]) -> dict[str, str]:
        """Sign and RSA-chunk-encrypt payload into encryptData."""
        signed_payload = self._sign_payload(payload)
        json_payload = json.dumps(signed_payload, separators=(",", ":"))
        payload_bytes = json_payload.encode("utf-8")
        block_size = (self._public_key.key_size // 8) - 11
        encrypted_chunks: list[bytes] = []
        for offset in range(0, len(payload_bytes), block_size):
            encrypted_chunks.append(
                self._public_key.encrypt(
                    payload_bytes[offset : offset + block_size],
                    padding.PKCS1v15(),
                )
            )
        return {"encryptData": b64encode(b"".join(encrypted_chunks)).decode("utf-8")}

    def _decrypt_response(self, encrypted_data: str) -> Any:
        """Decrypt RSA-chunked encryptData response from server."""
        encrypted_bytes = b64decode(encrypted_data)
        block_size = self._private_key.key_size // 8
        decrypted_chunks: list[bytes] = []
        for offset in range(0, len(encrypted_bytes), block_size):
            decrypted_chunks.append(
                self._private_key.decrypt(
                    encrypted_bytes[offset : offset + block_size],
                    padding.PKCS1v15(),
                )
            )
        decrypted_text = b"".join(decrypted_chunks).decode("utf-8")
        return json.loads(decrypted_text)

    def _find_token(self, payload: Any) -> str | None:
        if isinstance(payload, str):
            return payload
        if isinstance(payload, dict):
            for key in ("token", "accessToken", "access_token", "bearerToken"):
                value = payload.get(key)
                if isinstance(value, str) and value:
                    return value
            for value in payload.values():
                token = self._find_token(value)
                if token:
                    return token
        return None

    def _token_needs_refresh(self) -> bool:
        if not self._token:
            return True
        if self._token_expires_at is None:
            return False
        return time.time() >= (self._token_expires_at - _AUTH_REFRESH_SKEW_SECONDS)

    def _decode_token_expiration(self, token: str | None) -> int | None:
        if not token or token.count(".") < 2:
            return None
        try:
            payload_part = token.split(".", 2)[1]
            padded = payload_part + "=" * (-len(payload_part) % 4)
            decoded = urlsafe_b64decode(padded.encode("utf-8"))
            claims = json.loads(decoded.decode("utf-8"))
            exp = claims.get("exp")
            return int(exp) if exp is not None else None
        except Exception:
            return None

    def _response_needs_reauthentication(self, payload: dict[str, Any]) -> bool:
        code = str(payload.get("code", "")).strip()
        if code in {"401", "403", "444"}:
            return True
        message = " ".join(
            str(payload.get(k, "")) for k in ("msg", "message", "error")
        ).lower()
        return any(
            m in message
            for m in ("not logged in", "login expired", "token expired", "invalid token", "unauthorized")
        )
