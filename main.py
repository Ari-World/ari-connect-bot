import os
import random
from typing import *
import discord
from discord import Intents
from plugins import config
from discord.ext import commands
from discord import app_commands
from plugins.db import db
from plugins.lobby_repository import LobbyRepository
from plugins.malurl_repository import MaliciousURLRepository
from plugins.malword_repository import MaliciousWordsRepository
from plugins.muted_repository import MutedRepository

class Ari(commands.Bot):
  def __init__(self, *args, **kwargs):
    self.config = config.load_config()
    self.token = self.config['DISCORD_API_TOKEN']
    self.db = db
    super().__init__(command_prefix= self.config['DISCORD_COMMAND_PREFIX'], intents=Intents.all())
    self.synced = False
    self.repositoryInitialize(self.db)

  def startBot(self):
    self.run(self.token)
    
  async def on_ready(self):
    await self.wait_until_ready()
    if not self.synced:
       await self.tree.sync()
       self.synced = True
    guild_count = len(self.guilds)
    member_count = sum(len(guild.members) for guild in self.guilds)

    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name=f"over {guild_count} Guilds with {member_count} Members!"
    )
    await self.change_presence(
        status=discord.Status.online,
        activity=activity
    )
    print("Ari Toram is Online")
  
  async def on_guild_join(self,guild):
    print(f'Bot has been added to a new server {guild.name}')
    guild = self.get_guild(939025934483357766)
    target_log = guild.get_channel(1230069779071762473)
    target_channel = guild.system_channel  # Use the system channel for the guild
    if target_channel is not None:  # Ensure there's a system channel
        await target_channel.send(f"💖 **Thank you for inviting {self.user.name}!!**\n\n__**A brief intro**__\nHey Everyone! My main purpose is creating an Inter Guild / Server Connectivity to bring the world closer together!\nHope you'll find my application useful! Thankyouuu~\n\nType `a!about` to know more about me and my usage!\n\n**__Servers Connected__**\n{len(self.guilds)}\n\n")
    else:
        print("System channel not found. Unable to send welcome message.")
    await target_log.send(embed=discord.Embed(description=f'Bot has been added to a new server {guild.name}'))

  async def on_command_error(self,ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        msg = '**Command on cooldown** Retry after **{:.2f}s**'.format(
            error.retry_after)
        await ctx.send(msg)
    elif not isinstance(error, Exception):
        await ctx.send(error)
    else:
       await ctx.send(error)

  async def setup_hook(self):
    
    async def load_cogs(directory):
        await self.load_extension("cogs.open_world_server")

        for filename in os.listdir(directory):
            if filename.endswith('.py') and not filename.startswith('__') and not filename.startswith('open_world_server'):
                cog_name = f'cogs.{filename[:-3]}'
                print(cog_name)
                await self.load_extension(cog_name)
            
   
    await load_cogs("./cogs")
  
  def repositoryInitialize(self,db):
    self.muted_repository = MutedRepository(db)
    self.lobby_repository = LobbyRepository(db)
    self.malicious_urls = MaliciousURLRepository(db)
    self.malicious_words = MaliciousWordsRepository(db)
if __name__ == "__main__":
  bot = Ari()
  bot.startBot()
