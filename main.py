import discord
from discord.ext import commands
import asyncio
import os
from flask import Flask
from threading import Thread

OWNER_ID = 1095541663121801226  # TERI ID
REQUIRED_ROLE_NAME = "Dadmin"  # REQUIRED ROLE NAME

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

# ================= BOT READY =================

@bot.event
async def on_ready():
    activity = discord.Game(name="Gilli danda with Hunter in Dark Reign Esports")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f"✅ Logged in as {bot.user}")

# ================= OWNER NO PREFIX =================

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # OWNER = no prefix allowed
    if message.author.id == OWNER_ID:
        ctx = await bot.get_context(message)
        if ctx.command:
            await bot.invoke(ctx)
            return

    await bot.process_commands(message)

# ================= ROLE CHECK =================

def has_required_role():
    async def predicate(ctx):
        # Owner bypass
        if ctx.author.id == OWNER_ID:
            return True
        
        role = discord.utils.get(ctx.author.roles, name=REQUIRED_ROLE_NAME)
        if role is None:
            await ctx.send("❌ You need **Dadmin** role to use this command!")
            return False
        
        return True
    return commands.check(predicate)

# ================= STATUS COMMAND =================

@bot.command()
@has_required_role()
async def status(ctx):
    remaining = total_members - sent_count
    await ctx.send(
        f"🟢 **DM STATUS**\n"
        f"📩 Sent: {sent_count}\n"
        f"📥 Remaining: {remaining if remaining > 0 else 0}\n"
        f"📦 Total: {total_members}"
    )

# ================= STOP COMMAND =================

@bot.command()
@has_required_role()
async def stop(ctx):
    global dm_task_running
    dm_task_running = False
    await ctx.send("🛑 DM process stopped!")

# ================= DM ROLE COMMAND =================

@bot.command()
@has_required_role()
async def dmrole(ctx, role: discord.Role, *, message):
    global dm_task_running, sent_count, total_members

    if dm_task_running:
        return await ctx.send("⚠️ DM already running!")

    dm_task_running = True
    sent_count = 0
    failed = 0
    skipped_users = []

    members = list(set(role.members))  # DUPLICATE FIX
    total_members = len(members)

    await ctx.send(f"📨 Starting DM to **{role.name}** ({total_members} users)")

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
        f"✅ **DM FINISHED**\n"
        f"📩 Sent: {sent_count}\n"
        f"❌ Failed: {failed}\n"
        f"📦 Total: {total_members}"
    )

    if skipped_users:
        report += "\n🚫 Skipped (DM OFF): " + ", ".join(skipped_users)

    await ctx.send(report)

# ================= RUN BOT =================

bot.run(os.getenv("TOKEN"))
