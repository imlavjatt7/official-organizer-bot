import discord
from discord.ext import commands
import asyncio
import os
from flask import Flask
from threading import Thread

OWNER_ID = 1095541663121801226  # TERI ID

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

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

dm_task_running = False
sent_count = 0
total_members = 0

# BOT READY
@bot.event
async def on_ready():
    activity = discord.Game(name="Gilli danda with Hunter in Dark Reign Esports")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f"✅ Logged in as {bot.user}")

# ================= NO PREFIX FOR OWNER =================

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id == OWNER_ID and not message.content.startswith("!"):
        ctx = await bot.get_context(message)
        await bot.invoke(ctx)
        return

    await bot.process_commands(message)

# STATUS COMMAND
@bot.command()
async def status(ctx):
    remaining = total_members - sent_count
    await ctx.send(
        f"🟢 **DM Status**\n"
        f"📩 Sent: {sent_count}\n"
        f"📥 Remaining: {remaining if remaining > 0 else 0}"
    )

# STOP DM COMMAND
@bot.command()
async def stop(ctx):
    global dm_task_running
    if ctx.author.id != OWNER_ID and not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ No permission!")

    dm_task_running = False
    await ctx.send("🛑 DM process stopped!")

# DM ROLE COMMAND
@bot.command()
async def dmrole(ctx, role: discord.Role, *, message):
    global dm_task_running, sent_count, total_members

    if ctx.author.id != OWNER_ID and not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ You need Administrator permission!")

    if dm_task_running:
        return await ctx.send("⚠️ DM already running!")

    dm_task_running = True
    sent_count = 0
    failed = 0
    skipped_users = []

    members = list(set(role.members))  # DUPLICATE FIX
    total_members = len(members)

    await ctx.send(f"📨 Starting DM to **{role.name}** ({total_members} members)")

    for member in members:
        if not dm_task_running:
            await ctx.send("❌ DM cancelled!")
            break

        try:
            await member.send(message)
            sent_count += 1
            await asyncio.sleep(4)
        except:
            failed += 1
            skipped_users.append(member.name)

    dm_task_running = False

    report = (
        f"✅ **DM Finished**\n"
        f"📩 Sent: {sent_count}\n"
        f"❌ Failed: {failed}\n"
        f"📦 Total: {total_members}"
    )

    if skipped_users:
        report += "\n🚫 Skipped: " + ", ".join(skipped_users)

    await ctx.send(report)

# RUN BOT
bot.run(os.getenv("TOKEN"))
