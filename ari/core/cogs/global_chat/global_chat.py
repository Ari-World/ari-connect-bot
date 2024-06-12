

from discord.ext import commands

from .global_chat_cache_manager import CacheManager
from .global_chat_commands import Global
from .global_chat_initialization import Intialization
from .global_chat_moderation import Moderation
from .global_chat_repository import Repository
from .global_chat_listeners import EventListeners

# TODO: Initialization module
# TODO: Commands module
# TODO: Moderation

import logging

log = logging.getLogger("globalchat.main")

class GlobalChat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.init = Intialization(bot)
        self.repos = Repository(bot,self.init, bot.db)
        self.cache_manager = CacheManager()

    async def cog_load(self):
        log.info("Preparing bot commands")
        await self.pre_load_cog()
        
        log.info("Initializing data from database")
        await self.init.load_data(
            self.repos.guild_repository, 
            self.repos.lobby_repository, 
            self.repos.muted_repository, 
            self.repos.malicious_urls_repository, 
            self.repos.malicious_words_repository, 
            self.repos.moderator_repository)
        
        log.info("Preparing messages for each lobbies")
        self.cache_manager.createCache(self.init.server_lobbies)

        log.info("Open world is ready")

    async def pre_load_cog(self):
        await self.bot.add_cog(Global(self.bot, self.init, self.repos))
        await self.bot.add_cog(Moderation(self.bot, self.repos, self.init,self.cache_manager))
        await self.bot.add_cog(EventListeners(self.bot, self.init, self.cache_manager))