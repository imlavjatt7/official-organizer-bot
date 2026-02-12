import discord
from discord.ext import commands
import asyncio
from pymongo import MongoClient
import os
from flask import Flask
from threading import Thread

# ---------------- INTENTS ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- MONGODB ----------------
MONGO_URL = os.getenv("MONGO_URL")
client = MongoClient(MONGO_URL)
db = client["scrims_bot"]
teams_col = db["teams"]

TOTAL_SLOTS = 25
TIMEOUT = 420  # 7 minutes

active_regs = {}

# ---------------- BOT READY ----------------
@bot.event
async def on_ready():
    activity = discord.Game(name="Scrims Organizer | Dark Reign")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f"✅ Logged in as {bot.user}")

# ---------------- REGISTER COMMAND ----------------
@bot.command()
async def register(ctx):
    user_id = ctx.author.id

    if user_id in active_regs:
        return await ctx.send("⚠️ You already started registration!")

    if teams_col.count_documents({}) >= TOTAL_SLOTS:
        return await ctx.send("❌ Slots Full!")

    await ctx.send("📝 **Registration Started**\nReply in 7 minutes")

    answers = {}

    questions = [
        ("team", "Enter Team Name"),
        ("captain", "Enter Captain Name"),
        ("player1", "Enter Player 1 IGN"),
        ("player2", "Enter Player 2 IGN"),
        ("discord", "Enter Discord Tag")
    ]

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        for key, question in questions:
            await ctx.send(question)
            msg = await bot.wait_for("message", timeout=TIMEOUT, check=check)
            answers[key] = msg.content

        # Duplicate Team Check
        if teams_col.find_one({"team": answers["team"]}):
            return await ctx.send("❌ Team already registered!")

        slot_no = teams_col.count_documents({}) + 1

        teams_col.insert_one({
            "user": user_id,
            "team": answers["team"],
            "captain": answers["captain"],
            "players": [answers["player1"], answers["player2"]],
            "discord": answers["discord"],
            "slot": slot_no,
            "status": "PENDING"
        })

        await ctx.send(f"✅ Registered Successfully!\n🎟 Slot: {slot_no}")

    except asyncio.TimeoutError:
        await ctx.send("⌛ Registration Timeout!")

    active_regs.pop(user_id, None)

# ---------------- SLOTLIST ----------------
@bot.command()
async def slotlist(ctx):
    teams = list(teams_col.find())

    if not teams:
        return await ctx.send("❌ No teams registered yet!")

    text = "**📋 SLOT LIST**\n\n"

    for t in teams:
        text += f"🎟 {t['slot']} | {t['team']} | {t['status']}\n"

    await ctx.send(text)

# ---------------- ADMIN APPROVE ----------------
@bot.command()
@commands.has_permissions(administrator=True)
async def approve(ctx, team_name):
    team = teams_col.find_one({"team": team_name})

    if not team:
        return await ctx.send("❌ Team not found!")

    teams_col.update_one({"team": team_name}, {"$set": {"status": "APPROVED"}})
    await ctx.send(f"✅ Team **{team_name}** Approved!")

# ---------------- ADMIN REJECT ----------------
@bot.command()
@commands.has_permissions(administrator=True)
async def reject(ctx, team_name):
    teams_col.delete_one({"team": team_name})
    await ctx.send(f"❌ Team **{team_name}** Rejected & Removed!")

# ---------------- STATUS ----------------
@bot.command()
async def status(ctx):
    await ctx.send("🟢 Scrims Organizer Bot Running!")

# ---------------- KEEP ALIVE (RENDER) ----------------
app = Flask('')

@app.route('/')
def home():
    return "Bot Online"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

def keep_alive():
    Thread(target=run).start()

keep_alive()

# ---------------- RUN ----------------
bot.run(os.getenv("TOKEN"))
