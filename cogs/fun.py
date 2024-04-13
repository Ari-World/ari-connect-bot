import discord
from discord.ext import commands

class Fun(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="funtest", description="fun test command")
    async def FunTest(self, ctx):
        embed = discord.Embed(
            color = (discord.Colour.random()),
            description= f"Fun Command Test!"
        )

        await ctx.send(embed=embed)


async def setup(bot:commands.Bot):
    await bot.add_cog(Fun(bot))