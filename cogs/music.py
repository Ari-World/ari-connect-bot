import discord
from discord.ext import commands

class Music(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot

    @commands.command
    async def MusicTest(self, ctx):
        embed = discord.Embed(
            color = (discord.Colour.random()),
            description= f"Music Cog Test!"
        )

        await ctx.send(embed)


async def setup(bot:commands.Bot):
    print("Music Cog Loading")
    await bot.add_cog(Music(bot))