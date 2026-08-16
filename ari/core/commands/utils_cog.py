import enum
import logging
import discord

from datetime import datetime, timezone
from discord.ext import commands
from discord import app_commands
from typing import List, Optional

from ..utils.chat_formatting import humanize_timedelta
from ..utils.utility import Color
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

    @commands.hybrid_command(name="avatar", with_app_command=True, description="Shows a user's avatar")
    @app_commands.describe(user="The user whose avatar to show (defaults to you)")
    async def avatar(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        user = user or ctx.author
        embed = discord.Embed(color=Color.PRIMARY.to_discord_color())
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
        embed.set_image(url=user.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="userinfo", with_app_command=True, description="Shows information about a user")
    @app_commands.describe(user="The user to look up (defaults to you)")
    async def userinfo(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        user = user or ctx.author
        embed = discord.Embed(color=Color.PRIMARY.to_discord_color())
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="ID", value=str(user.id), inline=False)
        embed.add_field(
            name="Joined server",
            value=discord.utils.format_dt(user.joined_at, "F") if user.joined_at else "Unknown",
            inline=True,
        )
        embed.add_field(name="Account created", value=discord.utils.format_dt(user.created_at, "F"), inline=True)
        roles = [role.mention for role in reversed(user.roles) if role.name != "@everyone"]
        embed.add_field(name=f"Roles [{len(roles)}]", value=" ".join(roles) if roles else "None", inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="serverinfo", with_app_command=True, description="Shows information about this server")
    @commands.guild_only()
    async def serverinfo(self, ctx: commands.Context):
        guild = ctx.guild
        embed = discord.Embed(color=Color.PRIMARY.to_discord_color())
        embed.set_author(name=guild.name, icon_url=guild.icon.url if guild.icon else None)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Owner", value=str(guild.owner) if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Members", value=str(guild.member_count), inline=True)
        embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="Boost tier", value=str(guild.premium_tier), inline=True)
        embed.add_field(name="Boosts", value=str(guild.premium_subscription_count), inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(guild.created_at, "F"), inline=True)
        await ctx.send(embed=embed)

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

            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Invite", style=discord.ButtonStyle.link, url=self.bot.inv_url))
        
            await ctx.send(embed=embed, view=view)

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
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Invite", style=discord.ButtonStyle.link, url=self.context.bot.inv_url))
        
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
                        value+=f"<:_blank:1266299283737677844>**/{command.name}:** [Join](https://discord.gg/w8XKwkZQza) our support server\n"                    
                    elif command.name == "support":
                        value+=f"<:_blank:1266299283737677844>**/{command.name}:** [Invite](https://discord.com/) Ari to your server\n"
                    else:
                        value+=f"<:_blank:1266299283737677844>**/{command.name}:** {command.description}\n"
                embed.add_field(name=f"{emoji} {name}:", value=value, inline=False)
        return embed

    async def send_command_help(self, command):
        ctx = self.context
        embed = discord.Embed(color=Color.PRIMARY.to_discord_color())
        embed.set_author(name=f"AriConnect - {command.qualified_name}", icon_url=ctx.bot.user.avatar.url, url=self.context.bot.inv_url or "https://discord.com/") 

        if command.help:
            embed.description = command.help

        signature = self.get_command_signature(command)
        embed.add_field(name="Usage", value=signature, inline=False)
        return embed