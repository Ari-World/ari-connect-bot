import os
import sys
from dotenv import load_dotenv

load_dotenv()

def load_config():
    discord_api_token = os.getenv('DISCORD_API_TOKEN')
    discord_command_prefix = os.getenv('DISCORD_COMMAND_PREFIX', '!')

    # music_max_duration_mins = int(os.getenv('MUSIC_MAX_DURATION_MINS', '20'))
    # music_queue_per_page = int(os.getenv('MUSIC_QUEUE_PER_PAGE', '10'))

    if discord_api_token is None or discord_api_token == '':
        raise ValueError("Environment variable 'DISCORD_API_TOKEN' is required!")
    
    return {
        'DISCORD_API_TOKEN': discord_api_token,
        'DISCORD_COMMAND_PREFIX': discord_command_prefix,

    }