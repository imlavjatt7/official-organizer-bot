import discord
from discord.ext import commands
import json

# ================= DATA =================
def load():
    try:
        return json.load(open("data.json"))
    except:
        return {
            "antinuke": True,
            "antinuke_wl": {}
        }

def save(d):
    json.dump(d, open("data.json","w"), indent=4)

# ================= COG =================
class Antinuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def safe(self, user, action, data):
        return (
            user.id in data.get("extra_owner", [])
            or user.id in data.get("antinuke_wl", {}).get(action, [])
        )

    async def punish(self, guild, user, action):
        try:
            if user.id != guild.owner_id:
                await guild.ban(user, reason=f"💀 Anti {action}")
        except:
            pass

    async def get_entry(self, guild):
        try:
            async for e in guild.audit_logs(limit=1):
                return e
        except:
            return None

    async def handle(self, guild, action):
        data = load()
        if not data.get("antinuke"): return

        e = await self.get_entry(guild)
        if e and not self.safe(e.user, action, data):
            await self.punish(guild, e.user, action)

    # ================= EVENTS =================

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self.handle(guild, "ban")

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        await self.handle(guild, "unban")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        e = await self.get_entry(member.guild)
        if e and e.action.name == "kick":
            data = load()
            if not self.safe(e.user, "kick", data):
                await self.punish(member.guild, e.user, "kick")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            await self.handle(member.guild, "bot")

    # CHANNEL
    @commands.Cog.listener()
    async def on_guild_channel_create(self, ch):
        await self.handle(ch.guild, "channel_create")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, ch):
        await self.handle(ch.guild, "channel_delete")

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        await self.handle(after.guild, "channel_update")

    # ROLE
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        await self.handle(role.guild, "role_create")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        await self.handle(role.guild, "role_delete")

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        await self.handle(after.guild, "role_update")

    # MEMBER
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        await self.handle(after.guild, "member_update")

    # SERVER
    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        await self.handle(after, "server_update")

    # WEBHOOK
    @commands.Cog.listener()
    async def on_webhooks_update(self, ch):
        await self.handle(ch.guild, "webhook")

    # EMOJI
    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        await self.handle(guild, "emoji")

    # STICKER
    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild, before, after):
        await self.handle(guild, "sticker")

    # INTEGRATION
    @commands.Cog.listener()
    async def on_guild_integrations_update(self, guild):
        await self.handle(guild, "integration")

    # ================= PING PROTECTION =================
    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return

        data = load()

        # everyone / here
        if "@everyone" in msg.content or "@here" in msg.content:
            if not self.safe(msg.author, "everyone_ping", data):
                await msg.delete()
                await self.punish(msg.guild, msg.author, "everyone_ping")

        # role ping
        if msg.role_mentions:
            if not self.safe(msg.author, "role_ping", data):
                await msg.delete()
                await self.punish(msg.guild, msg.author, "role_ping")

        await self.bot.process_commands(msg)

    # ================= COMMANDS =================

    @commands.group()
    async def antinuke(self, ctx):
        pass

    @antinuke.command()
    async def enable(self, ctx):
        data = load()
        data["antinuke"] = True
        save(data)
        await ctx.send("🛡️ Antinuke Enabled")

    @antinuke.command()
    async def disable(self, ctx):
        data = load()
        data["antinuke"] = False
        save(data)
        await ctx.send("❌ Antinuke Disabled")

    # WL COMMANDS
    @antinuke.group()
    async def whitelist(self, ctx):
        pass

    @antinuke.whitelist.command()
    async def add(self, ctx, action, user: discord.Member):
        data = load()
        data.setdefault("antinuke_wl", {}).setdefault(action, []).append(user.id)
        save(data)
        await ctx.send(f"✅ {user} added to {action} WL")

    @antinuke.whitelist.command()
    async def remove(self, ctx, action, user: discord.Member):
        data = load()
        try:
            data["antinuke_wl"][action].remove(user.id)
        except:
            pass
        save(data)
        await ctx.send(f"❌ {user} removed from {action} WL")

    @antinuke.whitelist.command()
    async def show(self, ctx, action):
        data = load()
        users = data.get("antinuke_wl", {}).get(action, [])
        await ctx.send(f"{action} WL: {users}")

# ================= SETUP =================
def setup(bot):
    bot.add_cog(Antinuke(bot))
