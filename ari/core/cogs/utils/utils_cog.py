import enum
import logging
import discord

from datetime import datetime, timezone
from discord.ext import commands
from discord import app_commands
from typing import List

from ...utils.chat_formatting import humanize_timedelta
from ...utils.utility import Color
log = logging.getLogger("Core")


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="uptime", description="Shows how long the bot is active")
    async def uptime(self, ctx: commands.Context):
        """Shows [botname]'s uptime."""
        now = datetime.now(timezone.utc)
        delta = now - self.bot.uptime
        uptime_str = humanize_timedelta(timedelta=delta)
        
        embed = discord.Embed (
            description= ("I have been up for: **{time_quantity}** (since {timestamp})").format(
                time_quantity=uptime_str, timestamp=discord.utils.format_dt(self.bot.uptime, "f")),
            color= Color.PRIMARY
        )

        await ctx.send(
            embed = embed
        )

    @commands.hybrid_command(name="ping", description="Shows the bot latency")
    async def ping(self, ctx):
        """Shows the bot's latency."""
        latency = self.bot.latency  # Bot latency in seconds
        latency_ms = round(latency * 1000)  # Convert to milliseconds
        await ctx.send(f'Pong! 🏓 Latency is {latency_ms}ms')

    async def command_autocompletion(
            self,
            interaction: discord.Interaction,
            current: str
        ) -> List[app_commands.Choice[str]]:
            excluded_commands = ["help"]

            # List top-level commands for auto-completion, excluding specific commands
            top_level_commands = [
                app_commands.Choice(name=cmd.name, value=cmd.name)
                for cmd in self.bot.tree.walk_commands()
                if not cmd.parent and current.lower() in cmd.name.lower() and cmd.name not in excluded_commands
            ]

            # Combine and limit the number of choices to 25 or fewer
            return top_level_commands[:25]

    @commands.hybrid_command(name='help', with_app_command=True , description='Shows help information')
    @app_commands.autocomplete(command=command_autocompletion)
    async def help(self, ctx:commands.Context, command: str = None):
        help_command = MyHelpCommand()
        help_command.context = ctx
        if command:
            cmd = self.bot.get_command(command)
            embed = await help_command.send_command_help(cmd)
            await ctx.interaction.response.send_message(embed=embed)
        else:
            embed = await help_command.command_callback(ctx)
            await ctx.send(embed=embed)

class MyHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    async def send_bot_help(self, mapping = None):
        ctx = self.context
        embed = discord.Embed( color= Color.PRIMARY.to_discord_color() )
        embed.set_author(name=f"AriConnect", icon_url=ctx.bot.user.avatar.url, url=self.context.bot.inv_url or "https://discord.com/") 
        
        cog_emojis = {
            'Utils': '🔎',
            'Chat': '🌐',
            'Config': '⚙️',
            'Info': '🗿'
        }

        for cog, commands in mapping.items():
            if not cog :
                continue
            name = cog.qualified_name 
            emoji = cog_emojis.get(name, " ")
            filtered_cmds = await self.filter_commands(commands, sort=True)
            if filtered_cmds:
                value = ""
                for command in filtered_cmds:
                    # Brute force for hyperlinks descriptions
                    if command.name == "invite":
                        value+=f"\u1CBC\u1CBC **/{command.name}:** [Join](https://discord.gg/w8XKwkZQza) our support server\n"                    
                    elif command.name == "support":
                        value+=f"\u1CBC\u1CBC **/{command.name}:** [Invite](https://discord.com/) Ari to your server\n"
                    else:
                        value+=f"\u1CBC\u1CBC **/{command.name}:** {command.description}\n"
                embed.add_field(name=f"{emoji} {name}:", value=value, inline=False)
        return embed
    
    # This shows cogs
    # async def send_cog_help(self, cog):
    #     ctx = self.context
    #     embed = discord.Embed(title=f"{cog.qualified_name} Commands", color=Color.PRIMARY.to_discord_color())
    #     filtered_cmds = await self.filter_commands(cog.get_commands(), sort=True)
    #     for command in filtered_cmds:
    #         embed.add_field(name=command.name, value=command.help or "No description", inline=False)
    #     channel = self.get_destination()
    #     await channel.send(embed=embed)

    async def send_command_help(self, command):
        ctx = self.context
        embed = discord.Embed(color=Color.PRIMARY.to_discord_color())
        embed.set_author(name=f"AriConnect - {command.qualified_name}", icon_url=ctx.bot.user.avatar.url, url=self.context.bot.inv_url or "https://discord.com/") 

        if command.help:
            embed.description = command.help

        signature = self.get_command_signature(command)
        embed.add_field(name="Usage", value=signature, inline=False)
        return embed