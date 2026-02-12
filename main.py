import discord
from discord.ext import commands
import asyncio
import os
from flask import Flask
from threading import Thread

OWNER_ID = 1095541663121801226  # YOUR ID

# ================= KEEP ALIVE =================

if os.environ.get("RENDER") == "true":
    app = Flask('')

    @app.route('/')
    def home():
        return "Bot is running!"

    def run():
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

    Thread(target=run).start()

# ================= DISCORD BOT =================

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

dm_task_running = False
dm_sent = 0
dm_failed = 0
dm_total = 0

# ================= READY =================

@bot.event
async def on_ready():
    if getattr(bot, "already_ready", False):
        return
    bot.already_ready = True

    activity = discord.Game(name="Gilli danda with Hunter in Dark Reign Esports")
    await bot.change_presence(status=discord.Status.online, activity=activity)

    print(f"✅ Logged in as {bot.user}")

# ================= NO PREFIX FOR OWNER =================

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Owner no prefix commands
    if message.author.id == OWNER_ID:
        ctx = await bot.get_context(message)
        if ctx.command:
            await bot.invoke(ctx)
            return

    await bot.process_commands(message)

# ================= STATUS =================

@bot.command()
async def status(ctx):
    await ctx.send(
        f"🟢 Bot ONLINE\n"
        f"📩 DM Sent: {dm_sent}\n"
        f"❌ DM Failed: {dm_failed}\n"
        f"⏳ Remaining: {dm_total - (dm_sent + dm_failed)}"
    )

# ================= STOP DM =================

@bot.command()
async def stop(ctx):
    global dm_task_running
    dm_task_running = False
    await ctx.send("🛑 DM Process Stopped!")

# ================= DM ROLE =================

@bot.command()
async def dmrole(ctx, role: discord.Role, *, message):
    global dm_task_running, dm_sent, dm_failed, dm_total

    if ctx.author.id != OWNER_ID and not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ Only Admin or Owner can use this!")

    if dm_task_running:
        return await ctx.send("⚠️ DM already running!")

    dm_task_running = True
    dm_sent = 0
    dm_failed = 0
    dm_total = len(role.members)

    await ctx.send(f"📨 Starting DM to **{role.name}** ({dm_total} users)")

    for member in role.members:
        if not dm_task_running:
            await ctx.send("❌ DM Cancelled!")
            break

        try:
            await member.send(message)
            dm_sent += 1
            await asyncio.sleep(4)
        except:
            dm_failed += 1

    dm_task_running = False

    await ctx.send(
        f"✅ DM Finished!\n"
        f"📩 Sent: {dm_sent}\n"
        f"❌ Failed: {dm_failed}"
    )

# ================= RUN BOT =================

bot.run(os.getenv("TOKEN"))
