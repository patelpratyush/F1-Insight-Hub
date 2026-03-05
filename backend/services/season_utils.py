import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List


def get_current_season_year(reference: datetime | None = None) -> int:
    current = reference or datetime.now(timezone.utc)
    return current.year


def get_recent_seasons(window: int = 2, current_year: int | None = None) -> List[int]:
    season_year = current_year or get_current_season_year()
    start_year = max(2018, season_year - window + 1)
    return list(range(start_year, season_year + 1))


def _config_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "config")


def load_json_config(filename: str, default: Any = None) -> Any:
    config_path = os.path.join(_config_dir(), filename)
    try:
        with open(config_path) as file:
            return json.load(file)
    except Exception:
        return default if default is not None else {}


def load_fallback_roster() -> Dict[str, Dict[str, Any]]:
    return load_json_config("fallback_driver_roster.json", {}).get("drivers", {})


def load_driver_code_map() -> Dict[str, str]:
    return {
        code: driver_info.get("name", code)
        for code, driver_info in load_fallback_roster().items()
    }


def load_driver_numbers_map() -> Dict[str, Dict[str, Any]]:
    driver_map: Dict[str, Dict[str, Any]] = {}
    for code, driver_info in load_fallback_roster().items():
        number = str(driver_info.get("number", "")).strip()
        if not number:
            continue
        driver_map[number] = {
            "code": code,
            "name": driver_info.get("name", code),
            "team": driver_info.get("team", "Unknown"),
        }
    return driver_map


def load_driver_team_map_by_name() -> Dict[str, str]:
    return {
        driver_info.get("name", code): driver_info.get("team", "Unknown")
        for code, driver_info in load_fallback_roster().items()
    }


def load_team_name_mapping() -> Dict[str, str]:
    return load_json_config("team_name_mapping.json", {}).get("teams", {})

