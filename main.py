import discord
from discord.ext import commands
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

teams = []

@bot.event
async def on_ready():
    print(f"✅ Official Organizer Online as {bot.user}")

@bot.command()
async def scrim(ctx, *, name):
    await ctx.send(f"🏆 Scrim Created: **{name}**")

@bot.command()
async def tournament(ctx, *, name):
    await ctx.send(f"🔥 Tournament Created: **{name}**")

@bot.command()
async def register(ctx, team_name):
    teams.append(team_name)
    await ctx.send(f"✅ Team Registered: **{team_name}**")

@bot.command()
async def slots(ctx):
    if not teams:
        await ctx.send("❌ No teams registered")
        return
    msg = "**📋 SLOT LIST:**\n"
    for i, t in enumerate(teams, 1):
        msg += f"{i}. {t}\n"
    await ctx.send(msg)

@bot.command()
async def room(ctx, room_id, password):
    await ctx.send(f"🎮 ROOM ID: `{room_id}`\n🔑 PASS: `{password}`")

bot.run(os.getenv("TOKEN"))
