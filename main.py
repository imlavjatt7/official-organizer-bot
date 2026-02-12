import discord
from discord.ext import commands
import asyncio
import os
from flask import Flask
from threading import Thread

# ================= FLASK KEEP ALIVE =================

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

def keep_alive():
    Thread(target=run).start()

keep_alive()

# ================= DISCORD BOT =================

OWNER_ID = 1095541663121801226  # YOUR USER ID

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
intents.guilds = True

def get_prefix(bot, message):
    if message.author.id == OWNER_ID:
        return ""  # No prefix for owner
    return "!"     # Prefix for others

bot = commands.Bot(command_prefix=get_prefix, intents=intents)

# DM TRACKING DATA
dm_task_running = False
sent_count = 0
failed_count = 0
total_targets = 0

# ================= BOT READY =================

@bot.event
async def on_ready():
    if hasattr(bot, "ready_once"):
        return
    bot.ready_once = True

    activity = discord.Game(name="Gilli danda with Hunter in Dark Reign Esports")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f"✅ Logged in as {bot.user}")

# ================= STATUS COMMAND =================

@bot.command()
async def status(ctx):
    if dm_task_running:
        remaining = total_targets - sent_count - failed_count
        await ctx.send(
            f"📊 **DM STATUS (LIVE)**\n"
            f"▶ Running: ✅\n"
            f"📩 Sent: {sent_count}\n"
            f"❌ Failed: {failed_count}\n"
            f"⏳ Remaining: {remaining}"
        )
    else:
        await ctx.send(
            f"🟢 **Bot is ONLINE**\n"
            f"📩 Last Sent: {sent_count}\n"
            f"❌ Last Failed: {failed_count}\n"
            f"⛔ DM Process: Not Running"
        )

# ================= STOP COMMAND =================

@bot.command()
async def stop(ctx):
    global dm_task_running
    dm_task_running = False
    await ctx.send("🛑 DM process stopped!")

# ================= DM ROLE COMMAND =================

@bot.command()
async def dmrole(ctx, role: discord.Role, *, message):
    global dm_task_running, sent_count, failed_count, total_targets

    # Permission Check
    if ctx.author.id != OWNER_ID and not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ Admin or Owner only!")

    # Prevent duplicate runs
    if dm_task_running:
        return await ctx.send("⚠️ DM process already running!")

    dm_task_running = True
    sent_count = 0
    failed_count = 0
    total_targets = len(role.members)

    await ctx.send(f"📨 Starting DM to role: **{role.name}**")

    for member in role.members:
        if not dm_task_running:
            await ctx.send("❌ DM task cancelled!")
            break

        try:
            await member.send(message)
            sent_count += 1
            await asyncio.sleep(4)  # Delay to avoid rate limits
        except Exception:
            failed_count += 1

    dm_task_running = False

    remaining = total_targets - sent_count - failed_count

    report = (
        f"✅ **DM Process Finished**\n"
        f"📩 Sent: {sent_count}\n"
        f"❌ Failed: {failed_count}\n"
        f"⏳ Remaining: {remaining}"
    )

    await ctx.send(report)

# ================= ERROR HANDLER =================

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    await ctx.send("❌ Command Error!")

# ================= RUN BOT =================

bot.run(os.getenv("TOKEN"))
