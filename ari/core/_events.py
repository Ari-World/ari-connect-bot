from datetime import datetime, timezone
import logging
import sys

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
            if not bot.synced:
                await bot.tree.sync()
                bot.synced = True
        except Exception as exc:
            log.critical("The bot failed to get ready!", exc_info=exc)
            sys.exit(ExitCodes.CRITICAL)

    
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
       
        activity = discord.Activity(
          type=discord.ActivityType.watching,
          name=f"over {guilds} Guilds with {users} Members!"
        )
        await bot.change_presence(
            status=discord.Status.online,
            activity=activity
        )
        log.info("Ari Toram is Online")