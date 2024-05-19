import logging
import os
import sys
from dotenv import load_dotenv


log = logging.getLogger("ari.data_manager")

basic_config = None

# As for now data is saved via .env
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

    if discord_api_token is None or discord_api_token == '':
        log.error("Environment variable 'DISCORD_API_TOKEN' is required!")
    
    basic_config = {
        'DISCORD_API_TOKEN': discord_api_token,
        'DISCORD_COMMAND_PREFIX': discord_command_prefix,
        'MONGO_DB_URL': mongo_db_url
    }

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