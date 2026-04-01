import discord
from discord.ext import commands
from datetime import datetime, timedelta
import json

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

OWNER_ID = 1095541663121801226  # CHANGE

# ================= DATA =================
def load():
    try:
        return json.load(open("data.json"))
    except:
        return {
            "antinuke": True,
            "antilink": False,
            "antispam": False,
            "spam_time": 5,
            "spam_limit": 5,
            "extra_owner": [],
            "wl": []
        }

def save(d):
    json.dump(d, open("data.json","w"), indent=4)

data = load()

# ================= UTILS =================
def safe(u):
    return u.id == OWNER_ID or u.id in data["extra_owner"] or u.id in data["wl"]

async def punish(guild, user, reason="Antinuke"):
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

# ================= ANTINUKE EVENTS =================

async def handle(guild, action):
    if not data["antinuke"]: return
    e = await get_entry(guild)
    if e and not safe(e.user):
        await punish(guild, e.user, f"💀 {action}")

@bot.event
async def on_member_ban(guild, user):
    await handle(guild, "Anti Ban")

@bot.event
async def on_member_unban(guild, user):
    await handle(guild, "Anti Unban")

@bot.event
async def on_member_remove(member):
    e = await get_entry(member.guild)
    if e and e.action.name == "kick":
        if not safe(e.user):
            await punish(member.guild, e.user, "Anti Kick")

@bot.event
async def on_member_join(member):
    if member.bot:
        await handle(member.guild, "Anti Bot Add")

@bot.event
async def on_guild_channel_create(ch):
    await handle(ch.guild, "Channel Create")

@bot.event
async def on_guild_channel_delete(ch):
    await handle(ch.guild, "Channel Delete")

@bot.event
async def on_guild_channel_update(before, after):
    await handle(after.guild, "Channel Update")

@bot.event
async def on_guild_role_create(role):
    await handle(role.guild, "Role Create")

@bot.event
async def on_guild_role_delete(role):
    await handle(role.guild, "Role Delete")

@bot.event
async def on_guild_role_update(before, after):
    await handle(after.guild, "Role Update")

@bot.event
async def on_member_update(before, after):
    await handle(after.guild, "Member Update")

@bot.event
async def on_guild_update(before, after):
    await handle(after, "Server Update")

@bot.event
async def on_webhooks_update(ch):
    await handle(ch.guild, "Webhook")

@bot.event
async def on_guild_emojis_update(guild, before, after):
    await handle(guild, "Emoji Manage")

@bot.event
async def on_guild_stickers_update(guild, before, after):
    await handle(guild, "Sticker Manage")

@bot.event
async def on_guild_integrations_update(guild):
    await handle(guild, "Integration")

# ================= AUTOMOD =================
spam = {}

@bot.event
async def on_message(m):
    if m.author.bot:
        return

    # Anti Everyone / Role Ping
    if "@everyone" in m.content or "@here" in m.content or m.role_mentions:
        if not safe(m.author):
            await m.delete()
            await punish(m.guild, m.author, "Ping Abuse")

    # AntiLink
    if data["antilink"] and "http" in m.content:
        await m.delete()

    # AntiSpam
    if data["antispam"]:
        spam.setdefault(m.author.id, []).append(datetime.utcnow())
        spam[m.author.id] = [
            t for t in spam[m.author.id]
            if datetime.utcnow() - t < timedelta(seconds=data["spam_time"])
        ]
        if len(spam[m.author.id]) >= data["spam_limit"]:
            await m.author.timeout(timedelta(seconds=30))

    await bot.process_commands(m)

# ================= COMMANDS =================

@bot.command()
async def help(ctx):
    await ctx.send("💀 FULL SECURITY BOT ACTIVE")

@bot.command()
async def antinuke(ctx, mode):
    if not safe(ctx.author): return
    data["antinuke"] = (mode=="enable")
    save(data)
    await ctx.send("Antinuke Updated")

@bot.command()
async def antilink(ctx, mode):
    if not safe(ctx.author): return
    data["antilink"] = (mode=="on")
    save(data)

@bot.command()
async def antispam(ctx, mode, time:int=None, limit:int=None):
    if not safe(ctx.author): return
    if mode=="on":
        data["antispam"]=True
        data["spam_time"]=time
        data["spam_limit"]=limit
    else:
        data["antispam"]=False
    save(data)

@bot.command()
async def whitelist(ctx, mode, user: discord.Member):
    if not safe(ctx.author): return
    if mode=="add":
        data["wl"].append(user.id)
    elif mode=="remove":
        data["wl"].remove(user.id)
    save(data)

@bot.command()
async def extraowner(ctx, user: discord.Member):
    if ctx.author.id != OWNER_ID: return
    data["extra_owner"].append(user.id)
    save(data)

# ================= MODERATION =================

@bot.command()
async def kick(ctx, user: discord.Member):
    if not safe(ctx.author): return
    await user.kick()

@bot.command()
async def ban(ctx, user: discord.Member):
    if not safe(ctx.author): return
    await user.ban()

@bot.command()
async def unban(ctx, user_id: int):
    if not safe(ctx.author): return
    await ctx.guild.unban(discord.Object(id=user_id))

@bot.command()
async def mute(ctx, user: discord.Member):
    await user.timeout(timedelta(minutes=10))

@bot.command()
async def unmute(ctx, user: discord.Member):
    await user.timeout(None)

# ================= READY =================
@bot.event
async def on_ready():
    print(f"💀 {bot.user} GOD MODE ACTIVE")

bot.run("TOKEN")
