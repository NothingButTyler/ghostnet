import discord
from discord import app_commands
from discord.ext import commands
import os, asyncio, uuid, requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread
import google.generativeai as genai

# --- 1. CONFIGURATION ---
SESSION_ID = str(uuid.uuid4())[:8]

# OAuth2 Settings
CLIENT_ID = os.environ.get('CLIENT_ID', '1453941722324402327')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET', '3lClGZQzaRFAirl4lsfgbZj6HyRvR_vc')
REDIRECT_URI = 'https://ghostnet-bot.github.io/dashboard'

# Storage for Server Settings
server_config = {
    "welcome_channel": None,
    "welcome_msg": "Welcome to the terminal, {user}. Connection established.",
    "goodbye_channel": None,
    "goodbye_msg": "{user} has disconnected from the network."
}

# --- 2. AI CORE SETUP ---
genai.configure(api_key=os.environ.get("GEMINI_KEY"))
instruction = "You are the GHOSTNET AI Core. Tone: Professional, Cryptic, Tech-focused."
model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=instruction)

# --- 3. WEB BRIDGE (Flask) ---
app = Flask('')
CORS(app)

@app.route('/')
def home(): 
    return {"status": "ONLINE", "session": SESSION_ID, "system": "GHOSTNET_CORE_V2"}

@app.route('/dashboard')
def callback():
    code = request.args.get('code')
    if not code: return jsonify({"error": "No code found"}), 400
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    r = requests.post('https://discord.com/api/v10/oauth2/token', data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    if r.status_code != 200: return jsonify(r.json()), 400
    token = r.json().get('access_token')
    user_data = requests.get('https://discord.com/api/v10/users/@me', headers={'Authorization': f'Bearer {token}'})
    return jsonify(user_data.json())

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

def keep_alive():
    Thread(target=run, daemon=True).start()

# --- 4. DISCORD BOT ENGINE ---
class GhostBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Syncing slash commands
        await self.tree.sync()
        print(f"📡 Slash Commands Synced")

bot = GhostBot()

# --- 5. EVENTS ---
@bot.event
async def on_ready():
    print(f"🛰️ GHOSTNET V2 LIVE | SESSION: {SESSION_ID}")

@bot.event
async def on_member_join(member):
    if server_config["welcome_channel"]:
        channel = bot.get_channel(server_config["welcome_channel"])
        if channel:
            await channel.send(server_config["welcome_msg"].format(user=member.mention))

@bot.event
async def on_member_remove(member):
    if server_config["goodbye_channel"]:
        channel = bot.get_channel(server_config["goodbye_channel"])
        if channel:
            await channel.send(server_config["goodbye_msg"].format(user=member.name))

# --- 6. SLASH COMMANDS ---

@bot.tree.command(name="ping", description="Check signal latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🛰️ **LATENCY:** {round(bot.latency * 1000)}ms")

@bot.tree.command(name="help", description="View GHOSTNET protocols")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="🛰️ GHOSTNET_CORE V2", color=0x00ff41)
    embed.add_field(name="Configuration", value="`/welcome-setup` `/welcome-edit` `/welcome-test` \n `/goodbye-setup` `/goodbye-edit` `/goodbye-test`", inline=False)
    embed.add_field(name="System", value="`/ping` `/status`", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="welcome-setup", description="Set the welcome channel")
@app_commands.checks.has_permissions(administrator=True)
async def welcome_setup(interaction: discord.Interaction, channel: discord.TextChannel):
    server_config["welcome_channel"] = channel.id
    await interaction.response.send_message(f"✅ Welcome channel set to {channel.mention}")

@bot.tree.command(name="welcome-edit", description="Change the welcome message")
@app_commands.checks.has_permissions(administrator=True)
async def welcome_edit(interaction: discord.Interaction, message: str):
    server_config["welcome_msg"] = message
    await interaction.response.send_message(f"📝 Welcome message updated. Use `{{user}}` to mention members.")

@bot.tree.command(name="welcome-test", description="Test the welcome message")
async def welcome_test(interaction: discord.Interaction):
    await interaction.response.send_message(server_config["welcome_msg"].format(user=interaction.user.mention))

@bot.tree.command(name="goodbye-setup", description="Set the goodbye channel")
@app_commands.checks.has_permissions(administrator=True)
async def goodbye_setup(interaction: discord.Interaction, channel: discord.TextChannel):
    server_config["goodbye_channel"] = channel.id
    await interaction.response.send_message(f"✅ Goodbye channel set to {channel.mention}")

@bot.tree.command(name="goodbye-test", description="Test the goodbye message")
async def goodbye_test(interaction: discord.Interaction):
    await interaction.response.send_message(server_config["goodbye_msg"].format(user=interaction.user.name))

@bot.tree.command(name="status", description="Check AI Core health")
async def status(interaction: discord.Interaction):
    status_report = f"```\nSYSTEM: GHOSTNET_V2\nSESSION: {SESSION_ID}\nAI_CORE: ONLINE\n```"
    await interaction.response.send_message(status_report)

# --- 7. SECURE BOOT ---
if __name__ == "__main__":
    keep_alive()
    if os.environ.get("RESTART_KEY") == "0":
        bot.run(os.environ.get("DISCORD_TOKEN"))
