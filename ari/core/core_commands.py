from datetime import datetime, timezone
from typing import TYPE_CHECKING
import discord
from discord.ext import commands

from . import i18n
from .i18n import Translator
from .utils.chat_formatting import humanize_timedelta

if TYPE_CHECKING:
    from ari.core.bot import Ari

__all__ = ["Core"]

_ = Translator("Core", __file__)


class CoreLogic:
    def __init__(self, bot: "Ari"):
            self.bot = bot


@i18n.cog_i18n(_)
class Core(commands.Cog,CoreLogic):
   
    @commands.command(hidden=True)
    async def ping(self, ctx: commands.Context):
        """Pong."""
        await ctx.send("Pong.")


  
    @commands.command()
    async def uptime(self, ctx: commands.Context):
        """Shows [botname]'s uptime."""
        now = datetime.now(timezone.utc)
        delta = now - self.bot.uptime
        uptime_str = humanize_timedelta(timedelta=delta) or _("Less than one second.")
        
        embed = discord.Embed (
            description= _("I have been up for: **{time_quantity}** (since {timestamp})").format(
                time_quantity=uptime_str, timestamp=discord.utils.format_dt(self.bot.uptime, "f")),
            color= 0x7289DA
        )
        await ctx.send(
            embed = embed
        )