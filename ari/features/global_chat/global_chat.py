

from discord.ext import commands

from .services.cache_manager import CacheManager
from .cogs.commands import Chat
from .persistence.state import GlobalChatState
from .cogs.moderation_commands import Moderation
from .persistence.repository import Repository
from .cogs.listeners import EventListeners
from .cogs.settings_commands import Config
from .services.audit_log_service import AuditLogService
from .services.lobby_service import LobbyService
from .services.guild_connection_service import GuildConnectionService
from .services.relay_service import RelayService
from .services.moderation_service import ModerationService
from core._driver._mongo import StaticDatabase

import logging

log = logging.getLogger("globalchat.main")

class GlobalChatManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.init = GlobalChatState(bot)
        self.repos = Repository()
        self.cache_manager = CacheManager()
        self.audit_log = AuditLogService(bot, self.init)
        self.lobby_service = LobbyService(self.init, self.repos)
        self.guild_connection_service = GuildConnectionService(bot, self.init, self.repos)
        self.relay_service = RelayService(bot, self.init, self.cache_manager)
        self.moderation_service = ModerationService(self.init, self.repos)

    async def cog_load(self):
        log.info("Preparing bot commands")
        await self.pre_load_cog()

        log.info("Initializing data from database")
        await self.init.load_data(
            self.repos.lobby_repository,
            self.repos.guild_repository,
            self.repos.lobby_config_repository,
            self.repos.muted_repository,
            self.repos.malicious_urls_repository,
            self.repos.malicious_words_repository,
            self.repos.moderator_repository)


        log.info("Open world is ready")

    async def pre_load_cog(self):

        # Global chat commands
        await self.bot.add_cog(Chat(self.bot, self.init, self.repos, self.audit_log, self.lobby_service, self.guild_connection_service))
        
        # Lobby moderation commands
        await self.bot.add_cog(Moderation(
            self.bot, self.init, self.repos, self.cache_manager,
            self.moderation_service, self.lobby_service, self.relay_service, self.audit_log))

        # Global chat setting
        await self.bot.add_cog(Config(self.bot, self.init))
        
        # Global chat, message processing to all lobbies
        await self.bot.add_cog(EventListeners(self.bot, self.init, self.relay_service, self.lobby_service))

