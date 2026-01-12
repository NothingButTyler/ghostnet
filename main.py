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

# Securely pull from Render Env
CLIENT_ID = os.environ.get('CLIENT_ID', '1453941722324402327')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET', '3lClGZQzaRFAirl4lsfgbZj6HyRvR_vc')
REDIRECT_URI = 'https://ghostnet-bot.github.io/dashboard'

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

# --- 3. WEB BRIDGE ---
app = Flask('')
CORS(app)

@app.route('/')
def home(): 
    return {"status": "ONLINE", "session": SESSION_ID}

@app.route('/dashboard')
def callback():
    code = request.args.get('code')
    if not code: return jsonify({"error": "No code"}), 400
    
    # FIXED: Added proper quotes to the strings below
    data = {
        'client_id': '1453941722324402327',
        'client_secret': '3lClGZQzaRFAirl4lsfgbZj6HyRvR_vc',
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'https://ghostnet-bot.github.io/dashboard'
    }
    r = requests.post('https://discord.com/api/v10/oauth2/token', data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    if r.status_code != 200: return jsonify(r.json()), 400
    
    token = r.json().get('access_token')
    user_data = requests.get('https://discord.com/api/v10/users/@me', headers={'Authorization': f'Bearer {token}'})
    return jsonify(user_data.json())

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()

# --- 4. DISCORD BOT ENGINE ---
class GhostBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        try:
            print("🔄 Syncing Slash Commands...")
            await self.tree.sync()
            print("✅ Sync Complete")
        except Exception as e:
            print(f"❌ Sync Failed: {e}")

bot = GhostBot()

# --- 5. SLASH COMMANDS ---
@bot.tree.command(name="ping", description="Check signal latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🛰️ **LATENCY:** {round(bot.latency * 1000)}ms")

@bot.tree.command(name="welcome-setup", description="Set welcome channel")
@app_commands.checks.has_permissions(administrator=True)
async def welcome_setup(interaction: discord.Interaction, channel: discord.TextChannel):
    server_config["welcome_channel"] = channel.id
    await interaction.response.send_message(f"✅ Set to {channel.mention}")

@bot.tree.command(name="status", description="AI Health Check")
async def status(interaction: discord.Interaction):
    await interaction.response.send_message(f"```\nSYSTEM: ONLINE\nSESSION: {SESSION_ID}\n```")

# --- 6. BOOT ---
if __name__ == "__main__":
    keep_alive()
    if os.environ.get("RESTART_KEY") == "0":
        bot.run(os.environ.get("DISCORD_TOKEN"))
