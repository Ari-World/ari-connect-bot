import datetime
import logging
import sys
from typing import *
from discord import Intents

from discord.ext import commands

from .cogs.utils.utils_cog import Utils
from .cogs.info.info_cogs import Info
from ._events import init_events
from .cog_manager import CogManager
from .cogs.global_chat.global_chat import GlobalChatManager

from core._cli import ExitCodes
log = logging.getLogger("ari")

class _NoOwnerSet(RuntimeError):
    """Raised when there is no owner set for the instance that is trying to start."""

class Ari(commands.Bot):
    
    def __init__(self, *args, **kwargs):
        self._shutdown_mode = ExitCodes.CRITICAL
        super().__init__(command_prefix= kwargs["prefix"], intents=Intents.all())
        self.synced = False
        self.token = False
        self._uptime = None
        self._cog_mngr = CogManager()
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

    async def setup_hook(self) -> None:
            await self._pre_connect()

    async def _pre_connect(self) -> None:
        """
        This should only be run once, prior to connecting to Discord gateway.
        """
        
        log.info("Preparing Global chat feature")
        await self.add_cog(GlobalChatManager(self))
        log.info("Preparing Utility Commands")
        await self.add_cog(Utils(self))
        log.info("Preparing Info Commands")
        await self.add_cog(Info(self))

    
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

  # async def on_ready(self):
  #     await self.wait_until_ready()
  #    
  #     guild_count = len(self.guilds)
  #     member_count = sum(len(guild.members) for guild in self.guilds)

  #     activity = discord.Activity(
  #         type=discord.ActivityType.watching,
  #         name=f"over {guild_count} Guilds with {member_count} Members!"
  #     )
  #     await self.change_presence(
  #         status=discord.Status.online,
  #         activity=activity
  #     )
  #     log.info("Ari Toram is Online")
    
      # Add Cogs here
      
  # async def setup_hook(self):
    
  #   async def load_cogs(directory):
  #       await self.load_extension("cogs.open_world_server")

  #       for filename in os.listdir(directory):
  #           if filename.endswith('.py') and not filename.startswith('__') and not filename.startswith('open_world_server'):
  #               cog_name = f'cogs.{filename[:-3]}'
  #               print(cog_name)
  #               await self.load_extension(cog_name)
            
   
  #   await load_cogs("../cogs")
  