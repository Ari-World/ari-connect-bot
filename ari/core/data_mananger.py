import logging
import os
import sys
from dotenv import load_dotenv


log = logging.getLogger("ari.data_manager")

basic_config = None

# As for now data is saved via .env
# TODO: Change this into a class if possible
def load_basic_configuration():
    """Loads the basic bootstrap configuration necessary for `Config`
    to know where to store or look for data.

    .. important::
        It is necessary to call this function BEFORE getting any `Config`
        objects!
    """
    load_dotenv()

    global basic_config

    discord_api_token = os.getenv('DISCORD_API_TOKEN')
    discord_command_prefix = os.getenv('DISCORD_COMMAND_PREFIX', '!')
    mongo_db_url = os.getenv('MONGO_DB_URL')
    open_world_thanks_message = os.getenv('OPEN_WORLD_THANKS_MSG')
    
    log_guild_id = os.getenv('LOG_GUILD_ID')
    log_general_id = os.getenv('LOG_GENENRAL_ID')
    log_chat_id = os.getenv('LOG_CHAT_ID')
    log_system_id = os.getenv('LOG_SYSTEM_ID')
    log_mod_id = os.getenv('LOG_MOD_ID')
    log_player_report_id = os.getenv('LOG_PLAYER_REPORT_ID')

    caching_threshold = os.getenv('CACHE_THRESHOLD')

    general_lobby_name = os.getenv('GENERAL_LOBBY_NAME')

    if discord_api_token is None or discord_api_token == '':
        log.error("Environment variable 'DISCORD_API_TOKEN' is required!")
    
    basic_config = {
        'DISCORD_API_TOKEN': discord_api_token,
        'DISCORD_COMMAND_PREFIX': discord_command_prefix,
        'MONGO_DB_URL': mongo_db_url,
        'OPEN_WORLD_THANKS_MSG':open_world_thanks_message,
        'LOG_GUILD_ID' : log_guild_id,
        'LOG_GENENRAL_ID' : log_general_id,
        'LOG_CHAT_ID'  : log_chat_id,
        'LOG_SYSTEM_ID' : log_system_id,
        'LOG_MOD_ID' : log_mod_id,
        'LOG_PLAYER_REPORT_ID' : log_player_report_id,
        'CACHE_THRESHOLD': caching_threshold,
        'GENERAL_LOBBY_NAME' : general_lobby_name
    }

    log.info(basic_config)

def getDiscordToken():
    """ Gets the bot token
    
    Returns
    -------
    str
        token
    """
    try:
        return basic_config['DISCORD_API_TOKEN']
    except KeyError as e:
        raise RuntimeError("Bot basic config has not been loaded yet") from e

def getPrefix():
    """ Gets the desired prefix
    
    Returns
    -------
    str
        prefix
    """
    try:
        return basic_config['DISCORD_COMMAND_PREFIX']
    except KeyError as e:
        raise RuntimeError("Bot basic config has not been loaded yet") from e

def getDBUrl():
    """ Gets the Database url
    
    Returns
    -------
    str
        URL / URI
    """
    try:
        return basic_config['MONGO_DB_URL']
    except KeyError as e:
        raise RuntimeError("Bot basic config has not been loaded yet") from e
    
def getLoggingGuildID():
    try:
        return basic_config['LOG_GUILD_ID']
    except KeyError as e:
        raise RuntimeError("Bot basic config has not been loaded yet") from e

def getGeneralLogChannelID():
    try:
        return basic_config['LOG_GENENRAL_ID']
    except KeyError as e:
        raise RuntimeError("Bot basic config has not been loaded yet") from e

def getChatLogChannelID():
    try:
        return basic_config['LOG_CHAT_ID']
    except KeyError as e:
        raise RuntimeError("Bot basic config has not been loaded yet") from e

def getSystemLobChannelID():
    try:
        return basic_config['LOG_SYSTEM_ID']
    except KeyError as e:
        raise RuntimeError("Bot basic config has not been loaded yet") from e

def getModLogChannelID():
    try:
        return basic_config['LOG_MOD_ID']
    except KeyError as e:
        raise RuntimeError("Bot basic config has not been loaded yet") from e

def getPlayerReportLogChannelID():
    try:
        return basic_config['LOG_PLAYER_REPORT_ID']
    except KeyError as e:
        raise RuntimeError("Bot basic config has not been loaded yet") from e
    
def getCacheThreshold():
    try:
        return basic_config['CACHE_THRESHOLD']
    except KeyError as e:
        raise RuntimeError("Bot basic config has not been loaded yet") from e
    
def getGeneralLobby():
    try:
        return basic_config['GENERAL_LOBBY_NAME']
    except KeyError as e:
        raise RuntimeError("Bot basic config has not been loaded yet") from e