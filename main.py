import discord
from discord.ext import commands
import os, asyncio, random, time, uuid, requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread
import google.generativeai as genai

# --- 1. CONFIGURATION & PERSONALITY ---
SESSION_ID = str(uuid.uuid4())[:8]
ISAAC_ID = 1444073106384621631
infected_users = {} 

# DISCORD OAUTH2 (Fill these in from the Dev Portal)
CLIENT_ID = '1453941722324402327'
CLIENT_SECRET = 'Ts9dPTZneVvfud9tlrEHJB3lqxN5U5mA'
# This must match what you put in the Discord Dev Portal exactly!
REDIRECT_URI = 'https://ghostnet-bot.github.io/dashboard'

# Default Configs
welcome_config = {
    "channel_id": None,
    "message": "Welcome to the terminal, {user}. Connection established."
}

# Setup Gemini
genai.configure(api_key=os.environ.get("GEMINI_KEY"))
instruction = "You are the GHOSTNET AI Core. Your tone is professional, cryptic, and tech-focused. Use terms like 'LATENCY', 'ENCRYPTION', and 'PROTOCOL'. Keep responses concise."
model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=instruction)

# --- 2. WEB SERVER (The Bridge) ---
app = Flask('')
CORS(app) # This allows your GitHub site to talk to this server

@app.route('/')
def home(): 
    return {"status": "ONLINE", "session": SESSION_ID, "system": "GHOSTNET_CORE"}

# DISCORD LOGIN HANDSHAKE
@app.route('/login-callback')
def callback():
    code = request.args.get('code')
    if not code: return jsonify({"error": "No code provided"}), 400

    # Trade code for token
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post('https://discord.com/api/v10/oauth2/token', data=data, headers=headers)
    
    if r.status_code != 200: return jsonify(r.json()), 400
    
    token = r.json().get('access_token')

    # Get User Profile
    user_r = requests.get('https://discord.com/api/v10/users/@me', headers={
        'Authorization': f'Bearer {token}'
    })
    return jsonify(user_r.json())

@app.route('/update-welcome', methods=['POST'])
def update_welcome():
    data = request.json
    welcome_config["message"] = data.get("message", welcome_config["message"])
    return jsonify({"status": "success"})

@app.route('/broadcast', methods=['POST'])
def broadcast():
    data = request.json
    msg = data.get("message")
    if welcome_config["channel_id"] and msg:
        channel = bot.get_channel(welcome_config["channel_id"])
        embed = discord.Embed(description=f"📡 **SYSTEM_BROADCAST:** {msg}", color=0x00ff41)
        bot.loop.create_task(channel.send(embed=embed))
        return jsonify({"status": "sent"})
    return jsonify({"status": "error"}), 400

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 3. BOT SETUP ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')

# --- 4. THE GEMINI "SAFETY SHIELD" ---
async def get_gemini_response(prompt):
    try:
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text[:1900] 
    except Exception as e:
        print(f"GEMINI_ERROR: {e}")
        return "⚠️ [SIGNAL_LOST] AI_CORE_TIMEOUT"

# --- 5. COMMANDS ---
@bot.command(name="welcome-setup")
@commands.has_permissions(administrator=True)
async def welcome_setup(ctx, channel: discord.TextChannel):
    welcome_config["channel_id"] = channel.id
    await ctx.send(f"✅ **WELCOME PROTOCOL:** Destination set to {channel.mention}")

@bot.command(name="help")
async def help_cmd(ctx):
    author = ctx.author
    is_infected = author.id in infected_users and time.time() < infected_users[author.id]
    if author.id == ISAAC_ID or is_infected: return
    embed = discord.Embed(title="🛰️ GHOSTNET STAFF TERMINAL", color=0x00ff00)
    embed.add_field(name="👋 WELCOME", value="`!welcome-setup` | `!welcome-edit`", inline=False)
    embed.add_field(name="🛡️ SECURITY", value="`!lockdown` | `!hard-reset`", inline=False)
    embed.set_footer(text=f"SESSION: {SESSION_ID}")
    await ctx.reply(embed=embed)

@bot.command(name="hard-reset")
@commands.has_permissions(administrator=True)
async def hard_reset(ctx):
    await ctx.send(f"🚨 **REBOOTING SESSION...**")
    os._exit(0)

# --- 6. EVENTS ---
@bot.event
async def on_message(message):
    if message.author == bot.user: return
    if message.author.id in infected_users:
        if time.time() < infected_users[message.author.id]:
            try: await message.add_reaction("☣️")
            except: pass
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        async with message.channel.typing():
            response = await get_gemini_response(message.content)
            if response: await message.reply(response)
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"--- GHOSTNET {SESSION_ID} IS DEPLOYED ---")

if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    bot.run(token)

@app.route('/broadcast', methods=['POST'])
def broadcast():
    data = request.json
    msg = data.get("message")
    if welcome_config["channel_id"] and msg:
        channel = bot.get_channel(welcome_config["channel_id"])
        embed = discord.Embed(description=f"📡 **SYSTEM_BROADCAST:** {msg}", color=0x00ff41)
        # Using the bot's loop to send from the web thread
        bot.loop.create_task(channel.send(embed=embed))
        return jsonify({"status": "sent"})
    return jsonify({"status": "error"}), 400

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 3. BOT SETUP ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')

# --- 4. THE GEMINI "SAFETY SHIELD" ---
async def get_gemini_response(prompt):
    try:
        # Runs Gemini in a separate thread so it doesn't freeze Discord
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text[:1900] 
    except Exception as e:
        print(f"GEMINI_ERROR: {e}")
        return "⚠️ [SIGNAL_LOST] AI_CORE_TIMEOUT"

# --- 5. COMMANDS ---
@bot.command(name="welcome-setup")
@commands.has_permissions(administrator=True)
async def welcome_setup(ctx, channel: discord.TextChannel):
    welcome_config["channel_id"] = channel.id
    await ctx.send(f"✅ **WELCOME PROTOCOL:** Destination set to {channel.mention}")

@bot.command(name="help")
async def help_cmd(ctx):
    # Prank check
    author = ctx.author
    is_infected = author.id in infected_users and time.time() < infected_users[author.id]
    if author.id == ISAAC_ID or is_infected: return

    embed = discord.Embed(title="🛰️ GHOSTNET STAFF TERMINAL", color=0x00ff00)
    embed.add_field(name="👋 WELCOME", value="`!welcome-setup` | `!welcome-edit`", inline=False)
    embed.add_field(name="🛡️ SECURITY", value="`!lockdown` | `!hard-reset`", inline=False)
    embed.set_footer(text=f"SESSION: {SESSION_ID}")
    await ctx.reply(embed=embed)

@bot.command(name="hard-reset")
@commands.has_permissions(administrator=True)
async def hard_reset(ctx):
    await ctx.send(f"🚨 **REBOOTING SESSION...**")
    os._exit(0)

# --- 6. EVENTS ---
@bot.event
async def on_message(message):
    if message.author == bot.user: return

    # Infection Logic (Biohazard reaction)
    if message.author.id in infected_users:
        if time.time() < infected_users[message.author.id]:
            try: await message.add_reaction("☣️")
            except: pass

    # AI Chat Trigger
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        async with message.channel.typing():
            response = await get_gemini_response(message.content)
            if response:
                await message.reply(response)

    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"--- GHOSTNET {SESSION_ID} IS DEPLOYED ---")

if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    bot.run(token)
