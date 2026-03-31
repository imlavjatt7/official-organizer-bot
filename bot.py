import discord
from discord.ext import commands
from datetime import datetime, timedelta
import json

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)

OWNER_ID = 1095541663121801226
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

# ================= UTILS =================
def is_safe(user):
    return user.id in data["whitelist"] or user.id in data["extra_owner"]

def antinuke_on():
    return data["antinuke"]

def automod_on():
    return data["automod"]

# ================= LOG =================
async def log(guild, title, desc, color=0xff0000):
    ch = discord.utils.get(guild.text_channels, name=LOG_CHANNEL)
    if ch:
        embed = discord.Embed(title=title, description=desc, color=color)
        embed.set_footer(text="🛡️ Security System")
        embed.timestamp = datetime.utcnow()
        await ch.send(embed=embed)

# ================= ANTINUKE =================

@bot.event
async def on_guild_channel_delete(channel):
    async for entry in channel.guild.audit_logs(limit=1):
        user = entry.user
        if not antinuke_on() or is_safe(user): return
        await channel.guild.ban(user)
        await log(channel.guild, "🚨 Anti-Nuke Triggered",
                  f"**User:** {user}\n**Action:** Channel Delete\n**Punishment:** Ban")

@bot.event
async def on_guild_role_delete(role):
    async for entry in role.guild.audit_logs(limit=1):
        user = entry.user
        if not antinuke_on() or is_safe(user): return
        await role.guild.ban(user)
        await log(role.guild, "🚨 Role Delete",
                  f"**User:** {user}\n**Punishment:** Ban")

@bot.event
async def on_guild_role_create(role):
    async for entry in role.guild.audit_logs(limit=1):
        user = entry.user
        if not antinuke_on() or is_safe(user): return
        await role.guild.ban(user)
        await log(role.guild, "🚨 Role Create",
                  f"**User:** {user}\n**Punishment:** Ban")

@bot.event
async def on_member_ban(guild, user):
    async for entry in guild.audit_logs(limit=1):
        mod = entry.user
        if not antinuke_on() or is_safe(mod): return
        await guild.ban(mod)
        await log(guild, "🚨 Mass Ban",
                  f"**User:** {mod}\n**Punishment:** Ban")

@bot.event
async def on_webhooks_update(channel):
    async for entry in channel.guild.audit_logs(limit=1):
        user = entry.user
        if not antinuke_on() or is_safe(user): return
        await channel.guild.ban(user)
        await log(channel.guild, "🚨 Webhook Abuse",
                  f"**User:** {user}\n**Punishment:** Ban")

# 🤖 Bot Add Protection
@bot.event
async def on_member_join(member):
    if member.bot:
        async for entry in member.guild.audit_logs(limit=1):
            user = entry.user
            if not is_safe(user):
                await member.guild.ban(user)
                await log(member.guild, "🚨 Bot Add",
                          f"**Adder:** {user}\n**Punishment:** Ban")

# ================= AUTOMOD =================

BAD_WORDS = ["mc", "bc", "madarchod", "bhosdike"]
spam_tracker = {}
message_cache = {}
ping_tracker = {}

def is_spam(user):
    now = datetime.utcnow()
    spam_tracker.setdefault(user.id, []).append(now)
    spam_tracker[user.id] = [t for t in spam_tracker[user.id] if now - t < timedelta(seconds=5)]
    return len(spam_tracker[user.id]) >= 5

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if not automod_on():
        return await bot.process_commands(message)

    if is_safe(message.author):
        return await bot.process_commands(message)

    # 💬 Spam
    if is_spam(message.author):
        await message.delete()
        await message.author.timeout(timedelta(seconds=30))
        await log(message.guild, "🚫 Spam Detected",
                  f"**User:** {message.author}\n**Punishment:** Timeout", 0xffa500)

    # 🔗 Links
    if "discord.gg" in message.content:
        await message.delete()
        await log(message.guild, "🔗 Link Blocked",
                  f"**User:** {message.author}", 0x3498db)

    # 🤬 Bad Words
    for word in BAD_WORDS:
        if word in message.content.lower():
            await message.delete()
            await message.author.timeout(timedelta(seconds=60))
            await log(message.guild, "🤬 Abuse",
                      f"**User:** {message.author}\n**Punishment:** Timeout", 0xff4500)
            break

    # 🔁 Repeat
    if message_cache.get(message.author.id) == message.content:
        await message.delete()
        await log(message.guild, "🔁 Repeated Message",
                  f"**User:** {message.author}")

    message_cache[message.author.id] = message.content

    # 💀 MASS PING AUTO LOCKDOWN
    if "@everyone" in message.content or "@here" in message.content:
        now = datetime.utcnow()

        ping_tracker.setdefault(message.author.id, []).append(now)
        ping_tracker[message.author.id] = [
            t for t in ping_tracker[message.author.id]
            if now - t < timedelta(seconds=10)
        ]

        if len(ping_tracker[message.author.id]) >= 3:
            # FULL HIDE LOCKDOWN
            for ch in message.guild.channels:
                try:
                    await ch.set_permissions(message.guild.default_role, view_channel=False)
                except:
                    pass

            await log(
                message.guild,
                "💀 AUTO LOCKDOWN",
                f"**User:** {message.author}\n**Reason:** 3x Mass Ping\n**Action:** Server Hidden",
                0x000000
            )

        else:
            await message.delete()
            await message.author.timeout(timedelta(seconds=60))
            await log(
                message.guild,
                "📢 Ping Warning",
                f"**User:** {message.author}\n**Count:** {len(ping_tracker[message.author.id])}/3",
                0xffa500
            )

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

# ================= READY =================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="Server Security 🛡️"
    ))

    for g in bot.guilds:
        if not discord.utils.get(g.text_channels, name=LOG_CHANNEL):
            await g.create_text_channel(LOG_CHANNEL)

bot.run("YOUR_NEW_TOKEN")
