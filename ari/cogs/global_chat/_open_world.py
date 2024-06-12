
import logging
import signal
import discord
import asyncio

import re

import aiohttp
from discord.ext import commands
from discord import ButtonStyle, Embed, Webhook

from enum import Enum

# All code is moved into one cog due to adding cogs probelem.
# Issue is posted in  github

log = logging.getLogger("openworld.cog") 

class MessageTypes(Enum):
    REPLY = "REPLY"
    DELETE = "DELETE"
    UPDATE = "UPDATE"
    SEND = "SEND"

class OpenWorldServer(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.server_lobbies = None
        self.deleteMessageThreshold = 600
        self.cacheMessages = []
        self.bypass_delete_listener = set()
        self.mute_task = {}
        self.openworldThanksMessage = ("Thanks for connecting to the Open World Server! \n\n"+
         "**Remember to:** \n" +
         "> Be respectful and considerate. \n" +
         "> Protect your privacy. \n" +
         "> Follow our community guidelines.\n" +
         "> No NSFW or Lewd content\n"+
         "> Keep the chats Family Friendly and Clean\n\n"
         "If you see anyone breaking the rules, use ` /report ` and our global mods will take care of it!\n\n"
         "- Once the message is sent, it cannot delete be deleted from other servers. Please be mindful of what you send")

    # ======================================================================================
    # Bot Commands
    # ======================================================================================


    # ======================================================================================
    # Fuctions used for the commands
    # ======================================================================================

    
                
    # ======================================================================================
    # Moderation
    # ======================================================================================
    def ValidateUser(self,user_id):
        for modData in self.moderator:
                if modData["level"] == "1" or  modData["level"] == "2" or  modData["level"] == "3":
                    for mod in modData["mods"]:
                        if mod["user_id"] == str(user_id):
                            return True                    
        return False
    

        
async def setup(bot:commands.Bot):
    await bot.add_cog(OpenWorldServer(bot))
