import discord
from discord.ext import commands
import json

def load():
    return json.load(open("data.json"))

def safe(user, data):
    return user.id in data["extra_owner"] or user.id in data["wl"]

class Antinuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def punish(self, guild, user):
        try:
            await guild.ban(user)
        except:
            pass

    async def get_entry(self, guild):
        async for e in guild.audit_logs(limit=1):
            return e

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, ch):
        data = load()
        if not data["antinuke"]: return
        e = await self.get_entry(ch.guild)
        if e and not safe(e.user, data):
            await self.punish(ch.guild, e.user)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        data = load()
        e = await self.get_entry(role.guild)
        if e and not safe(e.user, data):
            await self.punish(role.guild, e.user)

def setup(bot):
    bot.add_cog(Antinuke(bot))
