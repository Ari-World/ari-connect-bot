import asyncio
import datetime
import logging
import os
import random
import sys
from typing import *
import discord
from discord import Intents
from plugins import config
from discord.ext import commands
from discord import app_commands

from .core_commands import Core
from .dev_commands import Dev
from ._events import init_events
from ._global_checks import init_global_checks
from .cog_manager import CogManager

from plugins.lobby_repository import LobbyRepository
from plugins.malurl_repository import MaliciousURLRepository
from plugins.malword_repository import MaliciousWordsRepository
from plugins.muted_repository import MutedRepository
from core._cli import ExitCodes

log = logging.getLogger("ari")

class _NoOwnerSet(RuntimeError):
    """Raised when there is no owner set for the instance that is trying to start."""

# TODO: Handles Data in .env files a.k.a datamanager
# TODO: Handles Database a.k.a mongodbManager
# TODO: Global Chat fix with new Structure
# TODO: Handles Globbal Config and Guild Config
# TODO: Create cog for webhook / or a module for webhook
class Ari(commands.Bot):
    
    def __init__(self, *args, **kwargs):
        self._shutdown_mode = ExitCodes.CRITICAL
        super().__init__(command_prefix= kwargs["prefix"], intents=Intents.all())
        self.synced = False
        self._uptime = None
        self._cog_mngr = CogManager()


    async def start(self, token):
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
        await self.add_cog(Core(self))
        await self.add_cog(Dev())
        log.info("Loading cogs")
        try:
            cogs_specs = await self._cog_mngr.find_cogs()
            for spec in cogs_specs:
                try:
                    await asyncio.wait_for(self.load_extension(spec.name), 30)
                    log.info(f"Added {spec.name}")
                except asyncio.TimeoutError:
                    log.exception("Failed to load package %s (timeout)", spec.name)
                except Exception as e:
                    log.exception("Failed to load package %s", spec.name, exc_info=e)
        except RuntimeError as e:
            log.error("Error finding core cogs: %s", e)

    # TODO: Create a MongoDriver mangager
    def repositoryInitialize(self,db):
        self.muted_repository = MutedRepository(db)
        self.lobby_repository = LobbyRepository(db)
        self.malicious_urls = MaliciousURLRepository(db)
        self.malicious_words = MaliciousWordsRepository(db)
    
    async def close(self):
        await super().close()

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
    
  # async def on_guild_join(self,guild):
  #     log.info(f'Bot has been added to a new server {guild.name}')
  #     guildx = self.get_guild(939025934483357766)
  #     target_log = guildx.get_channel(1230069779071762473)
  #     target_channel = guild.system_channel  # Use the system channel for the guild
  #     if target_channel is not None:  # Ensure there's a system channel
  #         await target_channel.send(f"💖 **Thank you for inviting {self.user.name}!!**\n\n__**A brief intro**__\nHey Everyone! My main purpose is creating an Inter Guild / Server Connectivity to bring the world closer together!\nHope you'll find my application useful! Thankyouuu~\n\nType `a!about` to know more about me and my usage!\n\n**__Servers Connected__**\n{len(self.guilds)}\n\n")
  #     else:
  #         log.warning("System channel not found. Unable to send welcome message.")
  #     await target_log.send(embed=discord.Embed(description=f'Bot has been added to a new server {guild.name}'))

  # async def on_command_error(self,ctx, error):
  #     if isinstance(error, commands.CommandOnCooldown):
  #         msg = '**Command on cooldown** Retry after **{:.2f}s**'.format(
  #             error.retry_after)
  #         await ctx.send(msg)
  #     elif not isinstance(error, Exception):
  #         await ctx.send(error)
  #     else:
  #       await ctx.send(error)


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
  