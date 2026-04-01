import discord
from discord.ext import commands
import json
import re

# --- SETTINGS ---
TOKEN = "YOUR_BOT_TOKEN"
PREFIX = "."

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# --- DATABASE LOGIC ---
def get_data():
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except:
        return {"antinuke": {}, "whitelist": {}, "automod": {}}

def save_data(data):
    with open("config.json", "w") as f:
        json.dump(data, f, indent=4)

# --- CORE PROTECTION CHECK ---
async def is_authorized(guild, user):
    if user.id == guild.owner_id or user.id == bot.user.id:
        return True
    data = get_data()
    whitelist = data["whitelist"].get(str(guild.id), [])
    return user.id in whitelist

async def punish(guild, member_id, reason):
    try:
        member = await guild.fetch_member(member_id)
        await member.ban(reason=f"Antinuke: {reason}")
    except:
        pass

# --- ANTINUKE EVENTS (Sare Features Yahan Hain) ---

@bot.event
async def on_audit_log_entry_create(entry):
    guild = entry.guild
    data = get_data()
    
    # Check if Antinuke is ON
    if not data["antinuke"].get(str(guild.id)):
        return

    # Check if user is whitelisted
    if await is_authorized(guild, entry.user):
        return

    action = entry.action
    user = entry.user

    # Mapping Actions to Punishments
    nuke_triggers = [
        discord.AuditLogAction.ban,
        discord.AuditLogAction.kick,
        discord.AuditLogAction.channel_create,
        discord.AuditLogAction.channel_delete,
        discord.AuditLogAction.channel_update,
        discord.AuditLogAction.role_create,
        discord.AuditLogAction.role_delete,
        discord.AuditLogAction.role_update,
        discord.AuditLogAction.server_update,
        discord.AuditLogAction.webhook_create,
        discord.AuditLogAction.webhook_delete,
        discord.AuditLogAction.emoji_create,
        discord.AuditLogAction.sticker_create,
        discord.AuditLogAction.bot_add
    ]

    if action in nuke_triggers:
        await punish(guild, user.id, f"Triggered {action.name}")

# --- AUTOMOD EVENTS ---

@bot.event
async def on_message(message):
    if not message.guild or message.author.bot:
        return
    
    data = get_data()
    guild_id = str(message.guild.id)
    config = data["automod"].get(guild_id, {})

    if await is_authorized(message.guild, message.author):
        await bot.process_commands(message)
        return

    # 1. Anti-Link & Anti-Invite
    if config.get("antilink") or config.get("antiinvite"):
        if "http" in message.content or "discord.gg/" in message.content:
            await message.delete()
            return await message.channel.send(f"{message.author.mention} No links allowed!", delete_after=3)

    # 2. Mention Everyone/Role
    if "@everyone" in message.content or "@here" in message.content or len(message.role_mentions) > 0:
        await message.delete()
        await punish(message.guild, message.author.id, "Mention Spam")

    await bot.process_commands(message)

# --- COMMANDS SECTION ---

@bot.group(invoke_without_command=True)
async def antinuke(ctx):
    await ctx.send("Commands: `enable`, `disable`, `whitelist add/remove`, `config`")

@antinuke.command()
@commands.has_permissions(administrator=True)
async def enable(ctx):
    data = get_data()
    data["antinuke"][str(ctx.guild.id)] = True
    save_data(data)
    await ctx.send("🛡️ Antinuke is now **Enabled**.")

@antinuke.command()
@commands.has_permissions(administrator=True)
async def whitelist(ctx, option: str, member: discord.Member):
    data = get_data()
    gid = str(ctx.guild.id)
    if gid not in data["whitelist"]: data["whitelist"][gid] = []

    if option == "add":
        if member.id not in data["whitelist"][gid]:
            data["whitelist"][gid].append(member.id)
            await ctx.send(f"✅ Added {member} to whitelist.")
    elif option == "remove":
        if member.id in data["whitelist"][gid]:
            data["whitelist"][gid].remove(member.id)
            await ctx.send(f"❌ Removed {member} from whitelist.")
    
    save_data(data)

@bot.group(invoke_without_command=True)
async def automod(ctx):
    await ctx.send("Commands: `antilink on/off`, `antiinvite on/off`")

@automod.command()
@commands.has_permissions(manage_guild=True)
async def antilink(ctx, status: str):
    data = get_data()
    gid = str(ctx.guild.id)
    if gid not in data["automod"]: data["automod"][gid] = {}
    
    data["automod"][gid]["antilink"] = (status.lower() == "on")
    save_data(data)
    await ctx.send(f"🤖 Anti-link set to {status}")

bot.run(TOKEN)
