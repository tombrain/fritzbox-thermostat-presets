"""Minimal async client for the FRITZ! Smart Home REST API (FRITZ!OS 8.20+)."""

from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any
from urllib.parse import quote
import xml.etree.ElementTree as ET

import aiohttp

INVALID_SID = "0000000000000000"
TIMEOUT = aiohttp.ClientTimeout(total=10)


class FritzError(Exception):
    """Base error."""


class FritzConnectionError(FritzError):
    """FRITZ!Box not reachable or unexpected response."""


class FritzAuthError(FritzError):
    """Login failed or missing user rights."""


def _solve_pbkdf2_challenge(challenge: str, password: str) -> str:
    # Format: 2$<iter1>$<salt1>$<iter2>$<salt2>
    _, iter1, salt1, iter2, salt2 = challenge.split("$")
    hash1 = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt1), int(iter1))
    hash2 = hashlib.pbkdf2_hmac("sha256", hash1, bytes.fromhex(salt2), int(iter2))
    return f"{salt2}${hash2.hex()}"


class FritzSmartHomeApi:
    """Talks to the FRITZ!Box via login_sid.lua and /api/v0/smarthome."""

    def __init__(self, session: aiohttp.ClientSession, host: str, username: str, password: str) -> None:
        self._session = session
        self._base_url = f"http://{host}"
        self._username = username
        self._password = password
        self._sid: str | None = None

    async def login(self) -> None:
        url = f"{self._base_url}/login_sid.lua?version=2"
        try:
            async with self._session.get(url, timeout=TIMEOUT) as resp:
                challenge = ET.fromstring(await resp.text()).findtext("Challenge", "")
            if not challenge.startswith("2$"):
                raise FritzConnectionError(f"Unsupported login challenge: {challenge}")

            # PBKDF2 is CPU heavy, keep it off the event loop
            response = await asyncio.get_running_loop().run_in_executor(
                None, _solve_pbkdf2_challenge, challenge, self._password
            )
            data = {"username": self._username, "response": response}
            async with self._session.post(url, data=data, timeout=TIMEOUT) as resp:
                sid = ET.fromstring(await resp.text()).findtext("SID")
        except (aiohttp.ClientError, TimeoutError, ET.ParseError) as err:
            raise FritzConnectionError(str(err)) from err

        if not sid or sid == INVALID_SID:
            raise FritzAuthError("Invalid username or password")
        self._sid = sid

    async def _request(self, method: str, path: str, payload: dict | None = None, retry: bool = True) -> Any:
        if self._sid is None:
            await self.login()

        url = f"{self._base_url}/api/v0/smarthome/{path}"
        headers = {"Authorization": f"AVM-SID {self._sid}"}
        try:
            async with self._session.request(method, url, json=payload, headers=headers, timeout=TIMEOUT) as resp:
                if resp.status in (401, 403):
                    # SID expired or user lacks rights: log in again once
                    self._sid = None
                    if retry:
                        return await self._request(method, path, payload, retry=False)
                    raise FritzAuthError(f"Access denied for {method} {path} (check user rights)")
                if resp.status >= 400:
                    raise FritzConnectionError(f"{method} {path} failed: HTTP {resp.status} {await resp.text()}")
                text = await resp.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise FritzConnectionError(str(err)) from err

        return json.loads(text) if text else None

    async def get_thermostats(self) -> dict[str, dict[str, Any]]:
        """Return all thermostat units keyed by UID."""
        units = await self._request("GET", "overview/units")
        return {unit["UID"]: unit for unit in units or [] if "thermostatInterface" in unit.get("interfaces", {})}

    async def set_temperature(self, uid: str, key: str, celsius: float) -> None:
        """Set comfortTemperature or reducedTemperature of a thermostat unit."""
        payload = {"interfaces": {"thermostatInterface": {key: {"mode": "temperature", "celsius": celsius}}}}
        await self._request("PUT", f"configuration/units/{quote(uid)}", payload)
