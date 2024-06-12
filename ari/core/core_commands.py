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

    @commands.command()
    async def ping(self, ctx):
        """Shows the bot's latency."""
        latency = self.bot.latency  # Bot latency in seconds
        latency_ms = round(latency * 1000)  # Convert to milliseconds
        await ctx.send(f'Pong! 🏓 Latency is {latency_ms}ms')

    

class MyHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    @commands.hybrid_command(name="help")
    async def help_command(self, ctx):
        """Shows this message"""
        await self.send_bot_help(ctx)


    async def send_bot_help(self, mapping):
        ctx = self.context
        embed = discord.Embed( color=discord.Color.blue() )
        embed.set_author(name="Commands List", icon_url=ctx.author.avatar.url) 
        
        for cog, commands in mapping.items():
            if not cog :
                continue
            name = cog.qualified_name 
            filtered_cmds = await self.filter_commands(commands, sort=True)
            if filtered_cmds:
                value = ' '.join([f"`{command.name}`" for command in filtered_cmds])
                embed.add_field(name=name, value=value, inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(title=f"{cog.qualified_name} Commands", color=discord.Color.blue())
        filtered_cmds = await self.filter_commands(cog.get_commands(), sort=True)
        for command in filtered_cmds:
            embed.add_field(name=command.name, value=command.help or "No description", inline=False)
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(title=f"{group.qualified_name} Commands", color=discord.Color.blue())
        if group.help:
            embed.description = group.help

        filtered_cmds = await self.filter_commands(group.commands, sort=True)
        for command in filtered_cmds:
            embed.add_field(name=command.name, value=command.help or "No description", inline=False)
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(title=command.qualified_name, color=discord.Color.blue())
        if command.help:
            embed.description = command.help

        signature = self.get_command_signature(command)
        embed.add_field(name="Usage", value=signature, inline=False)
        channel = self.get_destination()
        await channel.send(embed=embed)