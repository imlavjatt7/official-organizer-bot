import discord
from discord.ext import commands
from datetime import datetime, timedelta
import json

spam = {}

def load():
    return json.load(open("data.json"))

class Automod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, m):
        if m.author.bot: return

        data = load()

        if data["antilink"] and "http" in m.content:
            await m.delete()

        if data["antispam"]:
            spam.setdefault(m.author.id, []).append(datetime.utcnow())
            spam[m.author.id] = [
                t for t in spam[m.author.id]
                if datetime.utcnow() - t < timedelta(seconds=data["spam_time"])
            ]
            if len(spam[m.author.id]) >= data["spam_limit"]:
                await m.author.timeout(timedelta(seconds=30))

        await self.bot.process_commands(m)

def setup(bot):
    bot.add_cog(Automod(bot))
