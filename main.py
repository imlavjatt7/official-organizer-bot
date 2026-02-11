import discord
from discord.ext import commands
import asyncio
import os

# INTENTS
intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
intents.dm_messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

dm_task_running = False

# BOT READY + ACTIVITY STATUS
@bot.event
async def on_ready():
    activity = discord.Game(name="Gilli danda with Hunter in Dark Reign Esports")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f"✅ Logged in as {bot.user}")

# STATUS COMMAND
@bot.command()
async def status(ctx):
    await ctx.send("🟢 Bot is ONLINE and Running!")

# STOP DM COMMAND
@bot.command()
async def stop(ctx):
    global dm_task_running
    dm_task_running = False
    await ctx.send("🛑 DM process stopped!")

# DM ROLE COMMAND
@bot.command()
async def dmrole(ctx, role: discord.Role, *, message):
    global dm_task_running

    # Permission Check
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ You need Administrator permission!")

    # Prevent multiple runs
    if dm_task_running:
        return await ctx.send("⚠️ DM process already running!")

    dm_task_running = True
    sent = 0
    failed = 0
    skipped_users = []

    await ctx.send(f"📨 Starting DM to role: **{role.name}**")

    for member in role.members:
        if not dm_task_running:
            await ctx.send("❌ DM task cancelled!")
            break

        try:
            await member.send(message)
            sent += 1
            await asyncio.sleep(4)  # 3–5 second delay
        except:
            failed += 1
            skipped_users.append(member.name)

    dm_task_running = False

    report = (
        f"✅ **DM Process Finished**\n"
        f"📩 Sent: {sent}\n"
        f"❌ Failed: {failed}"
    )

    if skipped_users:
        report += "\n🚫 Skipped (DM Off): " + ", ".join(skipped_users)

    await ctx.send(report)
    from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "Bot is running"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

def keep_alive():
    Thread(target=run).start()

keep_alive()

# RUN BOT
bot.run(os.getenv("TOKEN"))
