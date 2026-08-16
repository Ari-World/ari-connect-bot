import datetime
import logging
import sys
from typing import *
from discord import Intents

from discord.ext import commands

from .commands.utils_cog import Utils
from .commands.info_cog import Info
from ._events import init_events
from ._driver._mongo import StaticDatabase
from features.global_chat.global_chat import GlobalChatManager
from integrations.registry import is_trusted_bot, load_integrations

from core._cli import ExitCodes
log = logging.getLogger("ari")

# Explicit feature registry — add a feature here to have it loaded at
# startup. No filesystem scanning/auto-discovery on purpose: this list is
# the single place a maintainer looks to see everything the bot loads.
FEATURES = [GlobalChatManager, Utils, Info]

# Only the privileged intents the bot actually reads from are requested
# here (not Intents.all()) — Discord's intent-verification review checks
# usage against what's requested, and Presence isn't used anywhere.
def _build_intents() -> Intents:
    intents = Intents.default()
    intents.message_content = True  # relay engine reads message.content
    intents.members = True  # member counts (stats, uptime banner)
    return intents


class Ari(commands.Bot):

    def __init__(self, *args, **kwargs):
        self._shutdown_mode = ExitCodes.CRITICAL
        super().__init__(command_prefix= kwargs["prefix"], intents=_build_intents())
        self.synced = False
        self.token = False
        self._uptime = None
        self.db = StaticDatabase
        self.inv_url = None
        self.remove_command('help')
        
    async def start(self, token):
        self.token = token
        await self._pre_login()
        await self.login(token)
        await self.connect()
    
    async def _pre_login(self) -> None:
        """
        This should only be run once, prior to logging in to Discord REST API.
        """
        init_events(self)
        # Must run after config.load_config() (called in __main__.main()
        # before Ari is even constructed) — each integration reads its own
        # env var, which isn't populated until .env has been loaded.
        load_integrations()

    async def process_commands(self, message) -> None:
        """Normally Discord ignores every message from another bot account.

        Trusted bot-to-bot integrations (see ari/integrations/) are the
        deliberate exception — add a new one there, not here.
        """
        if message.author.bot and not is_trusted_bot(message.author.id):
            return

        ctx = await self.get_context(message)
        await self.invoke(ctx)

    async def setup_hook(self) -> None:
            await self._pre_connect()

    async def _pre_connect(self) -> None:
        """
        This should only be run once, prior to connecting to Discord gateway.
        """
        for feature_cls in FEATURES:
            log.info("Preparing %s", feature_cls.__name__)
            await self.add_cog(feature_cls(self))


    async def close(self):
        await super().close()
        await self.db.close_db_connection()


    async def shutdown( self, *,restart: bool = False):
        """Gracefully quit.

        The program will exit with code :code:`0` by default.

        Parameters
        ----------
        restart : bool
            If :code:`True`, the program will exit with code :code:`26`. If the
            launcher sees this, it will attempt to restart the bot.

        """
        if not restart:
            self._shutdown_mode = ExitCodes.SHUTDOWN
        else:
            self._shutdown_mode = ExitCodes.RESTART

        await self.close()
        sys.exit(self._shutdown_mode)


    @property
    def uptime(self) -> datetime:
        """Allow access to the value, but we don't want cog creators setting it"""
        return self._uptime

    @uptime.setter
    def uptime(self, value) -> NoReturn:
        raise RuntimeError(
            "Hey, we're cool with sharing info about the uptime, but don't try and assign to it please."
        )