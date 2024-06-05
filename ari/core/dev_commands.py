import datetime
import discord
from discord.ext import commands

from . import i18n
from .i18n import Translator
from .utils.chat_formatting import humanize_timedelta


_ = Translator("Dev", __file__)

@i18n.cog_i18n(_)
class Dev(commands.Cog):
    """
    The Core cog has many commands related to core functions.

    These commands come loaded with every Red bot, and cover some of the most basic usage of the bot.
    """
    
    def __init__(self, bot) -> None:
        self.bot = bot
        super().__init__()

    @commands.command()
    async def ping(self, ctx):
        """Shows the bot's latency."""
        latency = self.bot.latency  # Bot latency in seconds
        latency_ms = round(latency * 1000)  # Convert to milliseconds
        await ctx.send(f'Pong! 🏓 Latency is {latency_ms}ms')