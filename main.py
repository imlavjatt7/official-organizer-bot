import discord
from discord.ext import commands
from discord.ui import View, Select
import json, os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

OWNER_ID = 1095541663121801226  # CHANGE THIS

# ================= DATA =================
def load_data():
    try:
        with open("data.json") as f:
            return json.load(f)
    except:
        return {
            "extra_owner": [],
            "autorole": None,
            "antinuke": True,
            "antinuke_wl": {
                "ban": [], "unban": [], "kick": [], "bot": [],
                "channel_create": [], "channel_delete": [], "channel_update": [],
                "role_create": [], "role_delete": [], "role_update": [],
                "member_update": [], "integration": [], "server_update": [],
                "webhook": [], "emoji": [], "sticker": [],
                "guild_event_create": [], "guild_event_update": [], "guild_event_delete": [],
                "invite_delete": [], "role_ping": [], "everyone_ping": []
            }
        }

def save_data(d):
    with open("data.json","w") as f:
        json.dump(d,f,indent=4)

data = load_data()

# ================= UTILS =================
def is_safe(user):
    return user.id == OWNER_ID or user.id in data["extra_owner"]

def wl(user, action):
    return is_safe(user) or user.id in data["antinuke_wl"].get(action, [])

async def punish(guild, user):
    if user.id == guild.owner_id:
        return
    try:
        await guild.ban(user, reason="💀 Anti-Nuke V3")
    except:
        pass

async def get_entry(guild):
    async for e in guild.audit_logs(limit=1):
        return e

# ================= HELP =================
@bot.command()
async def help(ctx):
    await ctx.send("💀 V3 Security Bot Active")

# ================= ANTINUKE EVENTS =================

# BAN / UNBAN
@bot.event
async def on_member_ban(guild, user):
    e = await get_entry(guild)
    if e and not wl(e.user, "ban"):
        await punish(guild, e.user)

@bot.event
async def on_member_unban(guild, user):
    e = await get_entry(guild)
    if e and not wl(e.user, "unban"):
        await punish(guild, e.user)

# KICK
@bot.event
async def on_member_remove(member):
    e = await get_entry(member.guild)
    if e and e.action.name == "kick":
        if not wl(e.user, "kick"):
            await punish(member.guild, e.user)

# BOT ADD
@bot.event
async def on_member_join(member):
    if member.bot:
        e = await get_entry(member.guild)
        if e and not wl(e.user, "bot"):
            await punish(member.guild, e.user)

# CHANNEL
@bot.event
async def on_guild_channel_create(ch):
    e = await get_entry(ch.guild)
    if e and not wl(e.user, "channel_create"):
        await punish(ch.guild, e.user)

@bot.event
async def on_guild_channel_delete(ch):
    e = await get_entry(ch.guild)
    if e and not wl(e.user, "channel_delete"):
        await punish(ch.guild, e.user)

@bot.event
async def on_guild_channel_update(before, after):
    e = await get_entry(after.guild)
    if e and not wl(e.user, "channel_update"):
        await punish(after.guild, e.user)

# ROLE
@bot.event
async def on_guild_role_create(role):
    e = await get_entry(role.guild)
    if e and not wl(e.user, "role_create"):
        await punish(role.guild, e.user)

@bot.event
async def on_guild_role_delete(role):
    e = await get_entry(role.guild)
    if e and not wl(e.user, "role_delete"):
        await punish(role.guild, e.user)

@bot.event
async def on_guild_role_update(before, after):
    e = await get_entry(after.guild)
    if e and not wl(e.user, "role_update"):
        await punish(after.guild, e.user)

# MEMBER UPDATE
@bot.event
async def on_member_update(before, after):
    e = await get_entry(after.guild)
    if e and not wl(e.user, "member_update"):
        await punish(after.guild, e.user)

# SERVER UPDATE
@bot.event
async def on_guild_update(before, after):
    e = await get_entry(after)
    if e and not wl(e.user, "server_update"):
        await punish(after, e.user)

# WEBHOOK
@bot.event
async def on_webhooks_update(ch):
    e = await get_entry(ch.guild)
    if e and not wl(e.user, "webhook"):
        await punish(ch.guild, e.user)

# EMOJI
@bot.event
async def on_guild_emojis_update(guild, before, after):
    e = await get_entry(guild)
    if e and not wl(e.user, "emoji"):
        await punish(guild, e.user)

# STICKER
@bot.event
async def on_guild_stickers_update(guild, before, after):
    e = await get_entry(guild)
    if e and not wl(e.user, "sticker"):
        await punish(guild, e.user)

# INTEGRATION
@bot.event
async def on_guild_integrations_update(guild):
    e = await get_entry(guild)
    if e and not wl(e.user, "integration"):
        await punish(guild, e.user)

# EVENTS (SCHEDULED EVENTS)
@bot.event
async def on_scheduled_event_create(event):
    e = await get_entry(event.guild)
    if e and not wl(e.user, "guild_event_create"):
        await punish(event.guild, e.user)

@bot.event
async def on_scheduled_event_update(before, after):
    e = await get_entry(after.guild)
    if e and not wl(e.user, "guild_event_update"):
        await punish(after.guild, e.user)

@bot.event
async def on_scheduled_event_delete(event):
    e = await get_entry(event.guild)
    if e and not wl(e.user, "guild_event_delete"):
        await punish(event.guild, e.user)

# MESSAGE (PING / ROLE PING)
@bot.event
async def on_message(msg):
    if msg.author.bot:
        return

    if "@everyone" in msg.content or "@here" in msg.content:
        if not wl(msg.author, "everyone_ping"):
            await msg.delete()
            await punish(msg.guild, msg.author)

    for role in msg.role_mentions:
        if not wl(msg.author, "role_ping"):
            await msg.delete()
            await punish(msg.guild, msg.author)

    await bot.process_commands(msg)

# ================= WL COMMAND =================
@bot.group()
async def antinuke(ctx):
    pass

@antinuke.group()
async def whitelist(ctx):
    pass

@antinuke.whitelist.command()
async def add(ctx, action, user: discord.Member):
    if not is_safe(ctx.author): return
    data["antinuke_wl"][action].append(user.id)
    save_data(data)
    await ctx.send("✅ WL Added")

@antinuke.whitelist.command()
async def remove(ctx, action, user: discord.Member):
    if not is_safe(ctx.author): return
    try:
        data["antinuke_wl"][action].remove(user.id)
    except:
        pass
    save_data(data)
    await ctx.send("❌ WL Removed")

# ================= READY =================
@bot.event
async def on_ready():
    print(f"💀 {bot.user} V3 ACTIVE")

bot.run(os.getenv("TOKEN"))
