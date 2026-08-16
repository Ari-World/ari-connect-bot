import logging
import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

log = logging.getLogger("ari.config")


@dataclass(frozen=True)
class AppConfig:
    discord_api_token: Optional[str]
    discord_command_prefix: str
    mongo_db_url: Optional[str]
    mongo_db_cluster: Optional[str]
    log_guild_id: Optional[str]
    log_general_id: Optional[str]
    log_chat_id: Optional[str]
    log_system_id: Optional[str]
    log_mod_id: Optional[str]
    log_player_report_id: Optional[str]
    cache_threshold: Optional[str]
    general_lobby_name: Optional[str]
    enable_rich_logging: bool


_config: Optional[AppConfig] = None


def load_config() -> AppConfig:
    """Loads configuration from the environment.

    Must be called before `get_config()`. Safe to call more than once
    (e.g. in tests) — each call re-reads the environment.
    """
    global _config

    load_dotenv()

    discord_api_token = os.getenv("DISCORD_API_TOKEN")
    if not discord_api_token:
        log.error("Environment variable 'DISCORD_API_TOKEN' is required!")

    _config = AppConfig(
        discord_api_token=discord_api_token,
        discord_command_prefix=os.getenv("DISCORD_COMMAND_PREFIX", "!"),
        mongo_db_url=os.getenv("MONGO_DB_URL"),
        mongo_db_cluster=os.getenv("MONGO_DB_CLUSTER"),
        log_guild_id=os.getenv("LOG_GUILD_ID"),
        log_general_id=os.getenv("LOG_GENENRAL_ID"),
        log_chat_id=os.getenv("LOG_CHAT_ID"),
        log_system_id=os.getenv("LOG_SYSTEM_ID"),
        log_mod_id=os.getenv("LOG_MOD_ID"),
        log_player_report_id=os.getenv("LOG_PLAYER_REPORT_ID"),
        cache_threshold=os.getenv("CACHE_THRESHOLD"),
        general_lobby_name=os.getenv("GENERAL_LOBBY_NAME"),
        enable_rich_logging=os.getenv("ENABLE_RICH_LOGGING", "true").lower() not in ("0", "false", "no"),
    )
    log.info(_config)
    return _config


def get_config() -> AppConfig:
    """Returns the loaded config. Raises if `load_config()` hasn't run yet."""
    if _config is None:
        raise RuntimeError("Config has not been loaded yet — call load_config() first")
    return _config
