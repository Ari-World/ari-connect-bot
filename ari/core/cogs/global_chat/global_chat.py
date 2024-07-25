

from discord.ext import commands

from .global_chat_cache_manager import CacheManager
from .global_chat_commands import Chat
from .global_chat_initialization import Intialization
from .global_chat_moderation import Moderation
from .global_chat_repository import Repository
from .global_chat_listeners import EventListeners
from .global_chat_settings import Config
from ..._driver._mongo import StaticDatabase

# TODO: Initialization module
# TODO: Commands module
# TODO: Moderation

import logging

log = logging.getLogger("globalchat.main")

class GlobalChatManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.init = Intialization(bot)
        self.repos = Repository()
        self.cache_manager = CacheManager()

    async def cog_load(self):
        log.info("Preparing bot commands")
        await self.pre_load_cog()
        
        log.info("Initializing data from database")
        await self.init.load_data(
            self.repos.lobby_repository,
            self.repos.guild_repository)
            # self.repos.lobby_repository, 
            # self.repos.muted_repository, 
            # self.repos.malicious_urls_repository, 
            # self.repos.malicious_words_repository, 
            # self.repos.moderator_repository
        
        log.info("Open world is ready")

    async def pre_load_cog(self):

        # Global chat commands
        await self.bot.add_cog(Chat(self.bot, self.init, self.repos))
        
        # Lobby moderation commands
        # await self.bot.add_cog(Moderation(self.bot, self.repos, self.init,self.cache_manager))

        # Global chat setting
        await self.bot.add_cog(Config(self.bot, self.init))
        
        # Global chat, message processing to all lobbies
        await self.bot.add_cog(EventListeners(self.bot, self.init, self.cache_manager))

