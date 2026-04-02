import discord
from discord.ext import commands
from datetime import datetime, timedelta
import json

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents)

OWNER_ID = 1234567890  # CHANGE

# ================= DATA =================
def load():
    try:
        return json.load(open("data.json"))
    except:
        return {
            "antilink": True,
            "antispam": True,
            "spam_time": 5,
            "spam_limit": 5,
            "extra_owner": [],
            "wl": [],
            "autorole_humans": None,
            "autorole_bots": None
        }

def save(d):
    json.dump(d, open("data.json","w"), indent=4)

data = load()

# ================= UTILS =================
def safe(u):
    return u.id == OWNER_ID or u.id in data["extra_owner"] or u.id in data["wl"]

async def punish(guild, user, reason="Protection"):
    try:
        if user.id != guild.owner_id:
            await guild.ban(user, reason=reason)
    except:
        pass

async def get_entry(guild):
    try:
        async for e in guild.audit_logs(limit=1):
            return e
    except:
        return None

# ================= ANTINUKE =================

@bot.event
async def on_guild_channel_create(ch):
    e = await get_entry(ch.guild)
    if e and not safe(e.user):
        await punish(ch.guild, e.user, "Channel Create")

@bot.event
async def on_guild_channel_delete(ch):
    e = await get_entry(ch.guild)
    if e and not safe(e.user):
        await punish(ch.guild, e.user, "Channel Delete")

@bot.event
async def on_guild_channel_update(before, after):
    e = await get_entry(after.guild)
    if e and not safe(e.user):
        await punish(after.guild, e.user, "Channel Update")

# ================= AUTOMOD =================
spam = {}

@bot.event
async def on_message(m):
    if m.author.bot:
        return

    # Anti Ping
    if "@everyone" in m.content or "@here" in m.content or m.role_mentions:
        if not safe(m.author):
            await m.delete()
            await punish(m.guild, m.author, "Ping Abuse")

    # AntiLink
    if data["antilink"] and "http" in m.content:
        try:
            await m.delete()
        except:
            pass

    # AntiSpam
    if data["antispam"]:
        spam.setdefault(m.author.id, []).append(datetime.utcnow())
        spam[m.author.id] = [
            t for t in spam[m.author.id]
            if datetime.utcnow() - t < timedelta(seconds=data["spam_time"])
        ]
        if len(spam[m.author.id]) >= data["spam_limit"]:
            try:
                await m.author.timeout(timedelta(seconds=30))
            except:
                pass

    await bot.process_commands(m)

# ================= AUTOROLE =================

@bot.event
async def on_member_join(member):
    try:
        if member.bot and data.get("autorole_bots"):
            role = member.guild.get_role(data["autorole_bots"])
            if role:
                await member.add_roles(role)

        elif not member.bot and data.get("autorole_humans"):
            role = member.guild.get_role(data["autorole_humans"])
            if role:
                await member.add_roles(role)
    except:
        pass

@bot.group()
async def autorole(ctx):
    pass

@autorole.command()
async def humans(ctx, role: discord.Role):
    if not safe(ctx.author): return
    data["autorole_humans"] = role.id
    save(data)
    await ctx.send(f"👤 Humans autorole set: {role.name}")

@autorole.command()
async def bots(ctx, role: discord.Role):
    if not safe(ctx.author): return
    data["autorole_bots"] = role.id
    save(data)
    await ctx.send(f"🤖 Bots autorole set: {role.name}")

# ================= WL & OWNER =================

@bot.command()
async def whitelist(ctx, mode, user: discord.Member):
    if not safe(ctx.author): return
    if mode == "add":
        if user.id not in data["wl"]:
            data["wl"].append(user.id)
    elif mode == "remove":
        if user.id in data["wl"]:
            data["wl"].remove(user.id)
    save(data)
    await ctx.send("WL Updated")

@bot.command()
async def extraowner(ctx, user: discord.Member):
    if ctx.author.id != OWNER_ID: return
    if user.id not in data["extra_owner"]:
        data["extra_owner"].append(user.id)
    save(data)
    await ctx.send("Extra Owner Added")

# ================= LOCKDOWN =================

@bot.command()
async def lockdown(ctx):
    if not safe(ctx.author): return
    for ch in ctx.guild.channels:
        try:
            await ch.set_permissions(ctx.guild.default_role, view_channel=False)
        except:
            pass
    await ctx.send("🔒 Server Fully Hidden")

@bot.command()
async def unlockdown(ctx):
    if not safe(ctx.author): return
    for ch in ctx.guild.channels:
        try:
            await ch.set_permissions(ctx.guild.default_role, view_channel=True)
        except:
            pass
    await ctx.send("🔓 Server Visible Again")

# ================= READY =================

@bot.event
async def on_ready():
    print(f"🔥 {bot.user} ONLINE")

bot.run("TOKEN")
