import discord
from discord.ext import commands
from datetime import datetime, timedelta
import json
import os
import asyncio
from flask import Flask
from threading import Thread

# ================= WEB SERVER =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run_web).start()

# ================= BOT =================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)

OWNER_ID = 1095541663121801226
LOG_CHANNEL = "security-logs"

# ================= SAFE LOG =================
async def log(guild, title, desc, color=0xff0000):
    try:
        ch = discord.utils.get(guild.text_channels, name=LOG_CHANNEL)
        if ch:
            embed = discord.Embed(title=title, description=desc, color=color)
            embed.timestamp = datetime.utcnow()
            await ch.send(embed=embed)
    except:
        pass

# ================= READY =================
@bot.event
async def on_ready():
    print(f"✅ Bot Online: {bot.user}")

# ================= SAFE START =================
keep_alive()

try:
    TOKEN = os.getenv("TOKEN")
    if not TOKEN:
        print("❌ TOKEN MISSING")
    else:
        bot.run(TOKEN)
except Exception as e:
    print("CRASH ERROR:", e)
