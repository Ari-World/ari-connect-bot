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


from . import presenters
from .config import get_config

log = logging.getLogger("ari")

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
        bot.inv_url = invite_url

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
        embed = presenters.build_guild_welcome_embed(guild, bot.user.name, len(bot.guilds))
        await channel.send(embed=embed)
        log.info(f'Bot has been added to a new server {guild.name}\n\n Added by {guild.owner.global_name } ({guild.owner.id})')

        config = get_config()
        admin_guild = bot.get_guild(int(config.log_guild_id))
        admin_channel = admin_guild.get_channel(int(config.log_general_id))
        await admin_channel.send(embed=presenters.build_guild_join_admin_notice_embed(guild))
        await ariStatus(bot)

