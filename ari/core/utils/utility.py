import uuid

from enum import Enum

import discord

def generate_uuid():

    uid = uuid.uuid4()
    lobby_code = uid.hex[:8]
    return lobby_code

class Color(Enum):
    PRIMARY = 0xFFC0CB
    
    def to_discord_color(self) -> discord.Color:
        return discord.Color(self.value)