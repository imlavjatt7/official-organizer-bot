import discord
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=".", intents=intents)

@bot.event
async def on_ready():
    print("BOT ONLINE")

bot.run("TOKEN")
