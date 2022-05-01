import yaml
import os
import logging
from typing import Optional, Any, Dict, Type, TypeVar
import asyncio


DEFAULT_CONFIG_FILE = "config.default.yml"
CONFIG_FILE = "config.yml"

DEFAULT_CONFIG: Optional[Dict] = None
CONFIG: Optional[Dict] = None
LOG = logging.getLogger("configuration")


def _load_configs():
    global DEFAULT_CONFIG, CONFIG

    with open(DEFAULT_CONFIG_FILE, "r") as default_config_file:
        DEFAULT_CONFIG = yaml.safe_load(default_config_file)

    if os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as config_file:
            CONFIG = yaml.safe_load(config_file)
    else:
        LOG.warn(f"{CONFIG_FILE} not found!")


_load_configs()


def _get_config_from_object(key: str, config: Optional[Dict]) -> Optional[Any]:
    if config is None:
        return None

    current = config
    key_parts = key.split(".")
    for part in key_parts:
        if part not in current:
            return None
        current = current[part]

    return current


def _get_user_config(key: str):
    return _get_config_from_object(key, CONFIG)


def _get_default_config(key: str):
    return _get_config_from_object(key, DEFAULT_CONFIG)


T = TypeVar("T")


def get_config(key: str, expected_type: Type[T]) -> T:
    """Returns config options. YAML objects are separated by '.'."""
    config = _get_user_config(key) or _get_default_config(key)

    if config is None:
        raise KeyError(f"Config missing for {key}")

    if not isinstance(config, expected_type):
        raise TypeError(
            f"""{key} has the wrong type!
Expected {expected_type} but got {type(config)}"""
        )

    return config
