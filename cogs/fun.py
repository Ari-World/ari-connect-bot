import discord
from discord.ext import commands

class Fun(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot

    @commands.command(name="FunTest")
    async def FunTest(self, ctx):
        embed = discord.Embed(
            color = (discord.Colour.random()),
            description= f"Fun Command Test!"
        )

        await ctx.send(embed=embed)


async def setup(bot:commands.Bot):
    print("Fun Cog Loading")
    await bot.add_cog(Fun(bot))