import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def help(self, ctx):
        # This is the main help command that displays the help menu
        embed = discord.Embed(title="Help Menu", description="List of available Modules:\n[Join our Community Server](https://discord.gg/2WREYJNaXK)")
        embed.add_field(name=":earth_asia: Global Commands", value="Check out my Global Commands with `a!help global_commands`!", inline=False)

        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.set_footer(text="Use a!about to learn more about me!")

        await ctx.send(embed=embed)

    @help.command()
    async def global_commands(self, ctx):
        # Help command for 'command1'
        embed = discord.Embed(title=":earth_asia: Global Commands", description="Check my Global Commands:\n[Join our Community Server](https://discord.gg/2WREYJNaXK)")
        embed.add_field(name="1. a!connect", value="> **Example:** a!connect #global-channel\n> **Description:** Connects the channel to global world lobby", inline=False)
        embed.add_field(name="2. a!switch <lobbies>", value="> **Example:** a!switch \"Hall of Legends\"\n> **Description:** Connects the channel to global world lobby", inline=False)
        embed.add_field(name="3. a!lobbies", value="> **Example:** a!lobbies\n> **Description:** Check for available lobbies", inline=False)
        embed.add_field(name="4. reportmessage", value="> **Example:** tap hold a message > apps > Report Message\n> **Description:** Sends a report to us for review", inline=False)
      
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.set_footer(text="Use a!about to learn more about me!")

        await ctx.send(embed=embed)

    # @help.command()
    # async def command2(self, ctx):
    #     # Help command for 'command2'
    #     embed = discord.Embed(title="Command 2", description="Description of command 2")
    #     embed.add_field(name="Usage", value="!command2 <arguments>", inline=False)
    #     embed.add_field(name="Example", value="!command2 argument1 argument2", inline=False)
    #     # Add more fields for additional information as needed

    #     embed.set_thumbnail(url=self.bot.user.avatar.url)
    #     embed.set_footer(text="Footer text")

    #     await ctx.send(embed=embed)

    # @help.command()
    # async def command3(self, ctx):
    #     # Help command for 'command3'
    #     embed = discord.Embed(title="Command 3", description="Description of command 3")
    #     embed.add_field(name="Usage", value="!command3 <arguments>", inline=False)
    #     embed.add_field(name="Example", value="!command3 argument1 argument2", inline=False)
    #     # Add more fields for additional information as needed

    #     embed.set_thumbnail(url=self.bot.user.avatar.url)
    #     embed.set_footer(text="Footer text")

    #     await ctx.send(embed=embed)

    # # Add more help commands for additional commands as needed


async def setup(bot:commands.Bot):
    print("Help Cog Loading")
    await bot.add_cog(Help(bot))