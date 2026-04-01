import discord
from discord.ext import commands
from datetime import datetime, timedelta
import json

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)

OWNER_ID = 1234567890
LOG_CHANNEL = "security-logs"

# ================= DATABASE =================
def load_data():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except:
        return {
            "whitelist": [OWNER_ID],
            "extra_owner": [],
            "antinuke": True,
            "automod": True
        }

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f)

data = load_data()

# ================= TRACKERS =================
tracker = {}
spam_tracker = {}
message_cache = {}

# ================= UTILS =================
def track(user, action, limit, sec):
    now = datetime.utcnow()
    tracker.setdefault(user.id, {}).setdefault(action, []).append(now)

    tracker[user.id][action] = [
        t for t in tracker[user.id][action]
        if now - t < timedelta(seconds=sec)
    ]

    return len(tracker[user.id][action]) >= limit

def is_safe(user):
    return user.id in data["whitelist"] or user.id in data["extra_owner"]

def antinuke_on():
    return data["antinuke"]

def automod_on():
    return data["automod"]

async def log(guild, msg):
    ch = discord.utils.get(guild.text_channels, name=LOG_CHANNEL)
    if ch:
        embed = discord.Embed(description=msg, color=0xff0000)
        embed.timestamp = datetime.utcnow()
        await ch.send(embed=embed)

# ================= ANTINUKE EVENTS =================

@bot.event
async def on_guild_channel_delete(channel):
    async for entry in channel.guild.audit_logs(limit=1):
        user = entry.user
        if not antinuke_on() or is_safe(user): return

        if track(user, "ch_del", 2, 10):
            await channel.guild.ban(user)
            await log(channel.guild, f"🚨 {user} banned (Channel Delete)")

@bot.event
async def on_guild_role_delete(role):
    async for entry in role.guild.audit_logs(limit=1):
        user = entry.user
        if not antinuke_on() or is_safe(user): return

        await role.guild.ban(user)
        await log(role.guild, f"🚨 {user} banned (Role Delete)")

@bot.event
async def on_guild_role_create(role):
    async for entry in role.guild.audit_logs(limit=1):
        user = entry.user
        if not antinuke_on() or is_safe(user): return

        await role.guild.ban(user)
        await log(role.guild, f"🚨 {user} banned (Role Create)")

@bot.event
async def on_member_ban(guild, user):
    async for entry in guild.audit_logs(limit=1):
        mod = entry.user
        if not antinuke_on() or is_safe(mod): return

        if track(mod, "ban", 3, 10):
            await guild.ban(mod)
            await log(guild, f"🚨 {mod} banned (Mass Ban)")

@bot.event
async def on_webhooks_update(channel):
    async for entry in channel.guild.audit_logs(limit=1):
        user = entry.user
        if not antinuke_on() or is_safe(user): return

        await channel.guild.ban(user)
        await log(channel.guild, f"🚨 {user} banned (Webhook Abuse)")

@bot.event
async def on_member_join(member):
    now = datetime.utcnow()
    spam_tracker.setdefault(member.guild.id, []).append(now)

    recent = [
        t for t in spam_tracker[member.guild.id]
        if now - t < timedelta(seconds=10)
    ]

    if len(recent) >= 10:
        for ch in member.guild.channels:
            await ch.set_permissions(member.guild.default_role, send_messages=False)

        await log(member.guild, "🚨 Raid detected! Server locked")

# ================= AUTOMOD =================

BAD_WORDS = ["mc", "bc", "madarchod", "bhosdike"]

def is_spam(user):
    now = datetime.utcnow()
    spam_tracker.setdefault(user.id, []).append(now)

    spam_tracker[user.id] = [
        t for t in spam_tracker[user.id]
        if now - t < timedelta(seconds=5)
    ]

    return len(spam_tracker[user.id]) >= 5

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if not automod_on():
        return await bot.process_commands(message)

    # whitelist + extra owner bypass
    if is_safe(message.author):
        return await bot.process_commands(message)

    # spam
    if is_spam(message.author):
        await message.delete()
        await message.author.timeout(timedelta(seconds=30))
        await log(message.guild, f"🚫 {message.author} muted (Spam)")

    # links
    if "discord.gg" in message.content:
        await message.delete()
        await log(message.guild, f"🔗 Link removed ({message.author})")

    # bad words
    for word in BAD_WORDS:
        if word in message.content.lower():
            await message.delete()
            await message.author.timeout(timedelta(seconds=60))
            await log(message.guild, f"🤬 {message.author} muted (Bad Word)")
            break

    # repeat
    if message_cache.get(message.author.id) == message.content:
        await message.delete()
        await log(message.guild, f"🔁 Repeated msg removed ({message.author})")

    message_cache[message.author.id] = message.content

    # everyone abuse
    if "@everyone" in message.content or "@here" in message.content:
        await message.delete()
        await message.author.timeout(timedelta(seconds=60))
        await log(message.guild, f"📢 Everyone abuse ({message.author})")

    await bot.process_commands(message)

# ================= COMMANDS =================

@bot.command()
async def antinuke(ctx, mode):
    if ctx.author.id != OWNER_ID: return
    data["antinuke"] = True if mode == "on" else False
    save_data(data)
    await ctx.send(f"🛡️ Anti-Nuke {mode}")

@bot.command()
async def automod(ctx, mode):
    if ctx.author.id != OWNER_ID: return
    data["automod"] = True if mode == "on" else False
    save_data(data)
    await ctx.send(f"🤖 Automod {mode}")

@bot.command()
async def whitelist(ctx, action, user: discord.Member = None):
    if ctx.author.id != OWNER_ID: return

    if action == "add" and user:
        if user.id not in data["whitelist"]:
            data["whitelist"].append(user.id)

    elif action == "remove" and user:
        if user.id in data["whitelist"]:
            data["whitelist"].remove(user.id)

    elif action == "list":
        return await ctx.send(str(data["whitelist"]))

    save_data(data)
    await ctx.send("✅ Done")

@bot.command()
async def extraowner(ctx, action, user: discord.Member = None):
    if ctx.author.id != OWNER_ID: return

    if action == "add" and user:
        if user.id not in data["extra_owner"]:
            data["extra_owner"].append(user.id)

    elif action == "remove" and user:
        if user.id in data["extra_owner"]:
            data["extra_owner"].remove(user.id)

    save_data(data)
    await ctx.send("👑 Updated")

@bot.command()
async def lockdown(ctx):
    if not is_safe(ctx.author): return

    for ch in ctx.guild.channels:
        await ch.set_permissions(ctx.guild.default_role, send_messages=False)

    await ctx.send("🔒 Server Locked")

@bot.command()
async def unlock(ctx):
    if not is_safe(ctx.author): return

    for ch in ctx.guild.channels:
        await ch.set_permissions(ctx.guild.default_role, send_messages=True)

    await ctx.send("✅ Server Unlocked")

# ================= READY =================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    for g in bot.guilds:
        if not discord.utils.get(g.text_channels, name=LOG_CHANNEL):
            await g.create_text_channel(LOG_CHANNEL)

bot.run("TOKEN")
