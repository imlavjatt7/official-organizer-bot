import discord
from discord.ext import commands
import os
import asyncio
import yt_dlp

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

queue = []

@bot.event
async def on_ready():
    activity = discord.Game(name="Driving GT 650 at 200Km/h speed")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f"✅ Logged in as {bot.user}")

# STATUS
@bot.command()
async def status(ctx):
    await ctx.send("✅ Official Organizer Bot is Online!")

# STOP BOT (ADMIN)
@bot.command()
@commands.has_permissions(administrator=True)
async def stopbot(ctx):
    await ctx.send("🛑 Bot shutting down...")
    await bot.close()

# DM ROLE COMMAND
@bot.command()
async def dmrole(ctx, role: discord.Role, *, message):
    sent = 0
    failed = 0
    await ctx.send(f"📨 Sending DMs to {role.name}...")

    for member in role.members:
        try:
            await asyncio.sleep(4)
            await member.send(message)
            sent += 1
        except:
            failed += 1

    await ctx.send(f"✅ Sent: {sent} | ❌ Failed: {failed}")

# MUSIC PLAY
@bot.command()
async def play(ctx, *, search):
    if not ctx.author.voice:
        return await ctx.send("❌ Join a voice channel first!")

    channel = ctx.author.voice.channel

    if not ctx.voice_client:
        await channel.connect()

    vc = ctx.voice_client

    ydl_opts = {"format": "bestaudio"}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{search}", download=False)
        url = info["entries"][0]["url"]

    vc.stop()
    vc.play(discord.FFmpegPCMAudio(url))

    await ctx.send(f"🎵 Now Playing: **{search}**")

# PAUSE
@bot.command()
async def pause(ctx):
    if ctx.voice_client:
        ctx.voice_client.pause()
        await ctx.send("⏸ Paused")

# RESUME
@bot.command()
async def resume(ctx):
    if ctx.voice_client:
        ctx.voice_client.resume()
        await ctx.send("▶️ Resumed")

# STOP MUSIC
@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("🛑 Music stopped")

bot.run(os.getenv("TOKEN"))
