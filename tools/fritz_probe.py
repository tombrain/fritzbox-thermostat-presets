"""Probe script: read and set comfort/eco temperatures of FRITZ!DECT thermostats.

Uses the official FRITZ! Smart Home REST API (FRITZ!OS 8.20+):
https://fritz.support/resources/SmarthomeRestApiFRITZOS82.html

Usage:
    python tools/fritz_probe.py --user myuser                      # list thermostats
    python tools/fritz_probe.py --user myuser --get "<UID>"        # full unit configuration as JSON
    python tools/fritz_probe.py --user myuser --uid "<UID>" --comfort 21.5 --eco 18

The password is read from the FRITZ_PASSWORD environment variable or prompted for.
Reading needs the 'Smart Home' user right, changing the configuration needs
'FRITZ!Box Einstellungen' (boxadmin) or 'apps'. Only the Python standard library is used.
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

INVALID_SID = "0000000000000000"


def http_get(url: str) -> str:
    with urllib.request.urlopen(url, timeout=10) as resp:
        return resp.read().decode("utf-8")


def http_post(url: str, data: dict[str, str]) -> str:
    body = urllib.parse.urlencode(data).encode()
    with urllib.request.urlopen(url, data=body, timeout=10) as resp:
        return resp.read().decode("utf-8")


def solve_pbkdf2_challenge(challenge: str, password: str) -> str:
    # Format: 2$<iter1>$<salt1>$<iter2>$<salt2>
    _, iter1, salt1, iter2, salt2 = challenge.split("$")
    hash1 = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt1), int(iter1))
    hash2 = hashlib.pbkdf2_hmac("sha256", hash1, bytes.fromhex(salt2), int(iter2))
    return f"{salt2}${hash2.hex()}"


def login(host: str, user: str, password: str) -> str:
    url = f"http://{host}/login_sid.lua?version=2"
    challenge = ET.fromstring(http_get(url)).findtext("Challenge", "")
    if not challenge.startswith("2$"):
        sys.exit(f"Unexpected challenge format (FRITZ!OS too old?): {challenge}")

    response = solve_pbkdf2_challenge(challenge, password)
    sid = ET.fromstring(http_post(url, {"username": user, "response": response})).findtext("SID")
    if not sid or sid == INVALID_SID:
        sys.exit("Login failed - check user, password and the user's 'Smart Home' permission.")
    return sid


def logout(host: str, sid: str) -> None:
    http_get(f"http://{host}/login_sid.lua?version=2&logout=1&sid={sid}")


def api(host: str, sid: str, method: str, path: str, payload: dict | None = None):
    url = f"http://{host}/api/v0/smarthome/{path}"
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"AVM-SID {sid}")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            text = resp.read().decode("utf-8")
    except urllib.error.HTTPError as err:
        sys.exit(f"{method} {path} failed: HTTP {err.code}\n{err.read().decode('utf-8', 'replace')}")
    return json.loads(text) if text else None


def unit_path(section: str, uid: str) -> str:
    return f"{section}/units/{urllib.parse.quote(uid)}"


def format_temp(temp: dict | None) -> str:
    if not temp:
        return "-"
    if temp.get("mode") == "temperature":
        return f"{temp['celsius']:.1f} °C"
    return temp.get("mode", "?").upper()


def list_thermostats(host: str, sid: str) -> None:
    found = False
    for unit in api(host, sid, "GET", "overview/units"):
        thermostat = unit.get("interfaces", {}).get("thermostatInterface")
        if thermostat is None:
            continue
        found = True
        print(f"{unit.get('name')}  (UID: {unit.get('UID')})")
        print(f"  Soll:     {format_temp(thermostat.get('setPointTemperature'))}")
        print(f"  Komfort:  {format_temp(thermostat.get('comfortTemperature'))}")
        print(f"  Eco:      {format_temp(thermostat.get('reducedTemperature'))}")
        print()

    if not found:
        print("No thermostats found.")


def set_temperatures(host: str, sid: str, uid: str, comfort: float | None, eco: float | None) -> None:
    thermostat = {}
    if comfort is not None:
        thermostat["comfortTemperature"] = {"mode": "temperature", "celsius": comfort}
    if eco is not None:
        thermostat["reducedTemperature"] = {"mode": "temperature", "celsius": eco}

    api(host, sid, "PUT", unit_path("configuration", uid), {"interfaces": {"thermostatInterface": thermostat}})

    result = api(host, sid, "GET", unit_path("overview", uid))["interfaces"]["thermostatInterface"]
    print(f"Komfort:  {format_temp(result.get('comfortTemperature'))}")
    print(f"Eco:      {format_temp(result.get('reducedTemperature'))}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", default="fritz.box")
    parser.add_argument("--user", required=True)
    parser.add_argument("--get", metavar="UID", help="print the full configuration of one unit as JSON")
    parser.add_argument("--uid", help="unit to change (use with --comfort/--eco)")
    parser.add_argument("--comfort", type=float, help="new comfort temperature in °C (0.5 steps)")
    parser.add_argument("--eco", type=float, help="new eco temperature in °C (0.5 steps)")
    args = parser.parse_args()

    if (args.comfort is not None or args.eco is not None) and not args.uid:
        parser.error("--comfort/--eco require --uid")

    password = os.environ.get("FRITZ_PASSWORD") or getpass.getpass("FRITZ!Box password: ")
    sid = login(args.host, args.user, password)
    try:
        if args.get:
            print(
                json.dumps(
                    api(args.host, sid, "GET", unit_path("configuration", args.get)), indent=2, ensure_ascii=False
                )
            )
        elif args.uid:
            set_temperatures(args.host, sid, args.uid, args.comfort, args.eco)
        else:
            list_thermostats(args.host, sid)
    finally:
        logout(args.host, sid)


if __name__ == "__main__":
    main()
