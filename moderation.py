import discord
from discord.ext import commands
from datetime import timedelta

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def kick(self, ctx, user: discord.Member):
        await user.kick()

    @commands.command()
    async def ban(self, ctx, user: discord.Member):
        await user.ban()

    @commands.command()
    async def unban(self, ctx, user_id: int):
        await ctx.guild.unban(discord.Object(id=user_id))

    @commands.command()
    async def mute(self, ctx, user: discord.Member):
        await user.timeout(timedelta(minutes=10))

    @commands.command()
    async def unmute(self, ctx, user: discord.Member):
        await user.timeout(None)

def setup(bot):
    bot.add_cog(Moderation(bot))
