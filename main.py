import discord
from discord.ext import commands
from datetime import datetime, timedelta
import json, os
from flask import Flask
from threading import Thread

# ================= WEB =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Alive"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_web).start()

# ================= BOT =================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents)

OWNER_ID = 1095541663121801226
LOG_CHANNEL = "security-logs"

# ================= DATA =================
def load_data():
    try:
        with open("data.json") as f:
            return json.load(f)
    except:
        return {
            "extra_owner": [],
            "antinuke": True,
            "automod": True,
            "autorole": None,
            "antinuke_wl": {
                "ban": [], "unban": [], "kick": [], "bot": [],
                "channel_create": [], "channel_delete": [], "channel_update": [],
                "everyone_ping": [],
                "role_create": [], "role_delete": [], "role_update": [],
                "member_update": [], "integration": [], "server_update": [],
                "webhook": [], "emoji": [], "sticker": []
            }
        }

def save_data(d):
    with open("data.json","w") as f:
        json.dump(d,f)

data = load_data()

# ================= UTILS =================
def is_safe(user):
    return user.id == OWNER_ID or user.id in data["extra_owner"]

def wl_check(user, action):
    return is_safe(user) or user.id in data["antinuke_wl"].get(action, [])

def create_embed(t, d, c=0x5865F2):
    e = discord.Embed(title=t, description=d, color=c)
    e.timestamp = datetime.utcnow()
    return e

# ================= WL PANEL =================
from discord.ui import View, Select

class WLMenu(View):
    def __init__(self, target):
        super().__init__(timeout=60)
        self.target = target
        self.add_item(Select(
            placeholder="Select WL",
            options=[
                discord.SelectOption(label="Anti Ban", value="ban"),
                discord.SelectOption(label="Anti Kick", value="kick"),
                discord.SelectOption(label="Channel Delete", value="channel_delete"),
                discord.SelectOption(label="Role Delete", value="role_delete"),
                discord.SelectOption(label="Webhook", value="webhook"),
                discord.SelectOption(label="Everyone Ping", value="everyone_ping"),
            ]
        ))

    @discord.ui.select()
    async def callback(self, interaction: discord.Interaction, select: Select):
        cat = select.values[0]
        data["antinuke_wl"][cat].append(self.target.id)
        save_data(data)
        await interaction.response.send_message(embed=create_embed("WL Added", f"{self.target.mention} → {cat}"), ephemeral=True)

@bot.command()
async def wl(ctx, user: discord.Member):
    if not is_safe(ctx.author): return
    await ctx.send(embed=create_embed("WL Panel", f"{user.mention}"), view=WLMenu(user))

# ================= AUTOROLE =================
@bot.command()
async def autorole(ctx, role: discord.Role):
    if not is_safe(ctx.author): return
    data["autorole"] = role.id
    save_data(data)
    await ctx.send(embed=create_embed("Autorole Set", role.mention))

@bot.event
async def on_member_join(member):
    if member.bot:
        async for e in member.guild.audit_logs(limit=1):
            if not wl_check(e.user, "bot"):
                await member.guild.ban(e.user)
    rid = data.get("autorole")
    if rid:
        r = member.guild.get_role(rid)
        if r:
            await member.add_roles(r)

# ================= AUTOMOD =================
@bot.event
async def on_message(m):
    if m.author.bot: return
    if "@everyone" in m.content:
        if not wl_check(m.author, "everyone_ping"):
            await m.delete()
    await bot.process_commands(m)

# ================= ANTINUKE =================
async def punish(guild, user):
    try:
        await guild.ban(user, reason="AntiNuke")
    except:
        pass

@bot.event
async def on_guild_channel_delete(ch):
    async for e in ch.guild.audit_logs(limit=1):
        if not wl_check(e.user, "channel_delete"):
            await punish(ch.guild, e.user)

@bot.event
async def on_guild_role_delete(role):
    async for e in role.guild.audit_logs(limit=1):
        if not wl_check(e.user, "role_delete"):
            await punish(role.guild, e.user)

@bot.event
async def on_webhooks_update(ch):
    async for e in ch.guild.audit_logs(limit=1):
        if not wl_check(e.user, "webhook"):
            await punish(ch.guild, e.user)

# ================= READY =================
@bot.event
async def on_ready():
    print("🔥 Bot Online")

bot.run(os.getenv("TOKEN"))
