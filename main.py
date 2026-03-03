import discord
from discord.ext import commands
import yt_dlp
import openai
import asyncio

# ================= CONFIG ================= #

TOKEN = "YOUR_BOT_TOKEN"
OPENAI_KEY = "YOUR_OPENAI_KEY"

openai.api_key = OPENAI_KEY

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= GLOBAL DATA ================= #

queues = {}
autoplay_status = {}
stay_247 = {}

# ================= AI CHAT ================= #

@bot.command()
async def ai(ctx, *, question):
    try:
        msg = await ctx.send("🤖 Thinking...")
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": question}]
        )
        reply = response.choices[0].message.content
        await msg.edit(content=reply[:2000])
    except Exception as e:
        await ctx.send(f"❌ AI Error: {e}")

# ================= MUSIC SYSTEM ================= #

async def play_next(ctx):
    guild_id = ctx.guild.id
    vc = ctx.voice_client

    if guild_id in queues and queues[guild_id]:
        next_song = queues[guild_id].pop(0)
        await play_song(ctx, next_song)
    else:
        if autoplay_status.get(guild_id, False):
            current = getattr(vc, "last_title", None)
            if current:
                await play_song(ctx, current)

async def play_song(ctx, query):
    guild_id = ctx.guild.id
    vc = ctx.voice_client

    ydl_opts = {'format': 'bestaudio', 'noplaylist': True, 'quiet': True}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)
        info = info['entries'][0]
        url2 = info['url']
        title = info['title']

    source = discord.FFmpegPCMAudio(
        url2,
        before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        options="-vn"
    )

    vc.last_title = title

    def after_play(error):
        fut = asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        try:
            fut.result()
        except:
            pass

    vc.play(source, after=after_play)
    await ctx.send(f"🎵 Now Playing: **{title}**")

@bot.command(aliases=["p"])
async def play(ctx, *, query):
    if not ctx.author.voice:
        return await ctx.send("❌ Join VC first!")

    channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        await channel.connect()

    guild_id = ctx.guild.id

    if ctx.voice_client.is_playing():
        queues.setdefault(guild_id, []).append(query)
        await ctx.send(f"➕ Added to Queue: **{query}**")
    else:
        await play_song(ctx, query)

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭ Skipped")

@bot.command()
async def stop(ctx):
    guild_id = ctx.guild.id
    queues[guild_id] = []
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("⏹ Music Stopped")

# ================= AUTOPLAY ================= #

@bot.command()
async def autoplay(ctx, mode):
    guild_id = ctx.guild.id
    if mode.lower() == "on":
        autoplay_status[guild_id] = True
        await ctx.send("🔁 Autoplay Enabled")
    else:
        autoplay_status[guild_id] = False
        await ctx.send("⛔ Autoplay Disabled")

# ================= 24/7 MODE ================= #

@bot.command(name="247")
async def stay(ctx, mode):
    guild_id = ctx.guild.id
    if mode.lower() == "on":
        stay_247[guild_id] = True
        await ctx.send("♾ 24/7 Mode Enabled")
    else:
        stay_247[guild_id] = False
        await ctx.send("❌ 24/7 Mode Disabled")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    vc = member.guild.voice_client
    if vc and not stay_247.get(member.guild.id, False):
        if len(vc.channel.members) == 1:
            await vc.disconnect()

# ================= READY ================= #

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
