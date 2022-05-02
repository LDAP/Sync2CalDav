import yaml
import os
import logging
from typing import Optional, Any, Dict, Type, TypeVar


DEFAULT_CONFIG_FILE = "config.default.yml"
CONFIG_FILE_PATHS = [
    "config.yml",
    ".config/config.yml",
    f"{os.getcwd()}/config.yml",
    f"{os.getcwd()}/.config/config.yml",
]

DEFAULT_CONFIG: Optional[Dict] = None
CONFIG: Optional[Dict] = None
LOG = logging.getLogger(__name__)


def _load_configs():
    global DEFAULT_CONFIG, CONFIG

    with open(DEFAULT_CONFIG_FILE, "r") as default_config_file:
        DEFAULT_CONFIG = yaml.safe_load(default_config_file)

    for config_file_path in CONFIG_FILE_PATHS:
        LOG.info(f"Search config file in {config_file_path}")
        if os.path.isfile(config_file_path):
            with open(config_file_path, "r") as config_file:
                CONFIG = yaml.safe_load(config_file)
                LOG.info("Found config file")
                break
    else:
        LOG.warn(f"config file not found in {CONFIG_FILE_PATHS}!")


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
