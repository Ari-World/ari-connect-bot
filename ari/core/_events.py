from datetime import datetime, timezone
import logging
import sys
from discord.ext import commands
import discord
from ._cli import ExitCodes


import rich
from rich import box
from rich.table import Table
from rich.columns import Columns
from rich.panel import Panel
from rich.text import Text


from . import i18n
from .i18n import Translator

log = logging.getLogger("ari")

_ = Translator(__name__, __file__)

INTRO = r"""

                _    _____                            _   
     /\        (_)  / ____|                          | |  
    /  \   _ __ _  | |     ___  _ __  _ __   ___  ___| |_ 
   / /\ \ | '__| | | |    / _ \| '_ \| '_ \ / _ \/ __| __|
  / ____ \| |  | | | |___| (_) | | | | | | |  __/ (__| |_ 
 /_/    \_\_|  |_|  \_____\___/|_| |_|_| |_|\___|\___|\__|
                                                          
                                                          
"""


def init_events(bot):

    @bot.event
    async def on_connect():
        if bot._uptime is None:
            log.info("Connected to Discord. Getting ready...")

    @bot.event
    async def on_ready():
        try:
            
            await _on_ready()
            await bot.wait_until_ready()
            if not bot.synced:
                await bot.tree.sync()
                bot.synced = True
                await ariStatus(bot)
        except Exception as exc:
            log.critical("The bot failed to get ready!", exc_info=exc)
            sys.exit(ExitCodes.CRITICAL)

    async def ariStatus(bot):
        guild_count = len(bot.guilds)
        member_count = sum(len(guild.members) for guild in bot.guilds)

        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"over {guild_count} Guilds with {member_count} Members!"
        )
        await bot.change_presence(
            status=discord.Status.online,
            activity=activity
        )
        log.info("Ari Toram is Online")
    async def _on_ready():
        if bot._uptime is not None:
            return
        
        bot._uptime = datetime.now(timezone.utc)
        
        guilds = len(bot.guilds)
        users = len(set([m for m in bot.get_all_members()]))

        
        invite_url = discord.utils.oauth_url(bot.application_id, scopes=("bot",))
        dpy_version = discord.__version__

        
        table_general_info = Table(show_edge=False, show_header=False, box=box.MINIMAL)
        table_general_info.add_row("Prefix: a!")
        table_general_info.add_row("Discord.py version", dpy_version)

        table_counts = Table(show_edge=False, show_header=False, box=box.MINIMAL)

        table_counts.add_row("Servers", str(guilds))
        if bot.intents.members:  # Lets avoid 0 Unique Users
            table_counts.add_row("Unique Users", str(users))

        rich_console = rich.get_console()

        rich_console.print(INTRO, style="red", markup=False, highlight=False)
        if guilds:
            rich_console.print(
                Columns(
                    [Panel(table_general_info, title=bot.user.display_name), Panel(table_counts)],
                    equal=True,
                    align="center",
                )
            )
        else:
            rich_console.print(Columns([Panel(table_general_info, title=bot.user.display_name)]))

        
        rich_console.print(
            "Loaded {} cogs with {} commands".format(len(bot.cogs), len(bot.commands))
        )

        

        if invite_url:
            rich_console.print(f"\nInvite URL: {Text(invite_url, style=f'link {invite_url}')}")
            # We generally shouldn't care if the client supports it or not as Rich deals with it.

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            msg = '**Command on cooldown** Retry after **{:.2f}s**'.format(
                error.retry_after)
            await ctx.send(msg)
        elif not isinstance(error, Exception):
            await ctx.send(error)
        else:
            await ctx.send(error)

    @bot.event
    async def on_guild_join(guild : discord.Guild):
        channel = guild.text_channels[0]
        embed = discord.Embed(
            title=guild.name, 
            description=f"💖 **Thank you for inviting {bot.user.name}!!**\n\n__**A brief intro**__\nHey Everyone! My main purpose is creating an Inter Guild / Server Connectivity to bring the world closer together!\nHope you'll find my application useful! Thankyouuu~\n\nType `a!about` to know more about me and my usage!\n\n**__Servers Connected__**\n{len(bot.guilds)}\n\n")
        await channel.send(embed=embed)
        log.info(f'Bot has been added to a new server {guild.name}\n\n Added by {guild.owner.global_name } ({guild.owner.id})')
        guildx = bot.get_guild(939025934483357766)
        target_log = guildx.get_channel(1230069779071762473)
        # target_channel = guild.system_channel  # Use the system channel for the guild
        # if target_channel is not None:  # Ensure there's a system channel
        #     await target_channel.send()
        # else:
        #     log.warning("System channel not found. Unable to send welcome message.")
        await target_log.send(embed=discord.Embed(description=f'Bot has been added to a new server {guild.name}\n\n Added by {guild.owner.global_name } ({guild.owner.id})'))
        await ariStatus(bot)

