import discord
from discord import app_commands
from discord.ext import commands
import os, asyncio, uuid
from flask import Flask
from threading import Thread

# --- 1. WEB SERVER (Render Support) ---
app = Flask('')
@app.route('/')
def home(): return f"GHOSTNET SLASH-PROTOCOL: ONLINE | SESSION: {SESSION_ID}"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. BOT CORE ---
# We still need a CommandTree for Slash Commands
class GhostNet(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)
        self.SESSION_ID = str(uuid.uuid4())[:8]

    async def setup_hook(self):
        # Syncs the commands to Discord's API
        await self.tree.sync()
        print(f"Synced slash commands for Session {self.SESSION_ID}")

bot = GhostNet()
SESSION_ID = bot.SESSION_ID

# Storage for Welcome Config
welcome_config = {"channel_id": None, "message": "Welcome {user} to the server."}

# --- 3. SLASH COMMANDS ---

@bot.tree.command(name="ping", description="Check terminal latency and session ID")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(
        f"🛰️ **SESSION:** `{SESSION_ID}`\n⏳ **LATENCY:** {latency}ms"
    )

@bot.tree.command(name="welcome-setup", description="Set the channel for welcome messages")
@app_commands.checks.has_permissions(administrator=True)
async def welcome_setup(interaction: discord.Interaction, channel: discord.TextChannel):
    welcome_config["channel_id"] = channel.id
    await interaction.response.send_message(f"✅ Welcome destination set to {channel.mention}")

@bot.tree.command(name="welcome-edit", description="Change the welcome message text")
@app_commands.checks.has_permissions(administrator=True)
async def welcome_edit(interaction: discord.Interaction, message: str):
    welcome_config["message"] = message
    await interaction.response.send_message(f"📝 Template updated to: `{message}`")

@bot.tree.command(name="hard-reset", description="Force restart the bot (Render Fix)")
@app_commands.checks.has_permissions(administrator=True)
async def hard_reset(interaction: discord.Interaction):
    await interaction.response.send_message(f"🚨 Killing Session `{SESSION_ID}`... Restarting.")
    os._exit(0)

# --- 4. EVENTS ---

@bot.event
async def on_member_join(member):
    if welcome_config["channel_id"]:
        channel = bot.get_channel(welcome_config["channel_id"])
        if channel:
            msg = welcome_config["message"].replace("{user}", member.mention)
            embed = discord.Embed(title="🛰️ NEW USER DETECTED", description=msg, color=0x00ff00)
            await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
