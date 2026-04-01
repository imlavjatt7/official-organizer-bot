import discord
from discord.ext import commands
import json

# ================= BASIC =================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

OWNER_ID = 1234567890  # CHANGE

# ================= DATA =================
def load():
    try:
        return json.load(open("data.json"))
    except:
        return {
            "extra_owner": [],
            "antinuke": True,
            "antinuke_wl": {}
        }

def save(d):
    json.dump(d, open("data.json","w"), indent=4)

data = load()

# ================= UTILS =================
def safe(u):
    return u.id == OWNER_ID or u.id in data["extra_owner"]

def wl(u, action):
    return safe(u) or u.id in data["antinuke_wl"].get(action, [])

async def punish(guild, user):
    try:
        if user.id != guild.owner_id:
            await guild.ban(user, reason="💀 Antinuke")
    except:
        pass

async def get_entry(guild):
    try:
        async for e in guild.audit_logs(limit=1):
            return e
    except:
        return None

# ================= EVENTS =================

@bot.event
async def on_guild_channel_delete(ch):
    if not data["antinuke"]: return
    e = await get_entry(ch.guild)
    if e and not wl(e.user, "channel_delete"):
        await punish(ch.guild, e.user)

@bot.event
async def on_guild_role_delete(role):
    if not data["antinuke"]: return
    e = await get_entry(role.guild)
    if e and not wl(e.user, "role_delete"):
        await punish(role.guild, e.user)

@bot.event
async def on_member_ban(guild, user):
    if not data["antinuke"]: return
    e = await get_entry(guild)
    if e and not wl(e.user, "ban"):
        await punish(guild, e.user)

@bot.event
async def on_member_join(member):
    if member.bot:
        e = await get_entry(member.guild)
        if e and not wl(e.user, "bot"):
            await punish(member.guild, e.user)

# ================= MESSAGE =================
@bot.event
async def on_message(msg):
    if msg.author.bot:
        return

    if "@everyone" in msg.content or "@here" in msg.content:
        if not wl(msg.author, "everyone"):
            try:
                await msg.delete()
                await punish(msg.guild, msg.author)
            except:
                pass

    await bot.process_commands(msg)

# ================= COMMANDS =================

@bot.command()
async def help(ctx):
    await ctx.send("💀 Antinuke Bot Running")

@bot.command()
async def antinuke(ctx, mode):
    if not safe(ctx.author): return
    data["antinuke"] = (mode=="enable")
    save(data)
    await ctx.send("Updated")

@bot.group()
async def whitelist(ctx):
    pass

@whitelist.command()
async def add(ctx, action, user: discord.Member):
    if not safe(ctx.author): return
    data["antinuke_wl"].setdefault(action, []).append(user.id)
    save(data)
    await ctx.send("✅ Added")

@whitelist.command()
async def remove(ctx, action, user: discord.Member):
    if not safe(ctx.author): return
    try:
        data["antinuke_wl"][action].remove(user.id)
    except:
        pass
    save(data)
    await ctx.send("❌ Removed")

# ================= READY =================
@bot.event
async def on_ready():
    print(f"🔥 {bot.user} ONLINE")

# ⚠️ DIRECT TOKEN (TESTING)
bot.run("TOKEN")
