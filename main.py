import discord
from discord.ext import commands
import os, asyncio, random, time, uuid, requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread
import google.generativeai as genai

# --- 1. CONFIGURATION & IDENTITY ---
SESSION_ID = str(uuid.uuid4())[:8]
ISAAC_ID = 1444073106384621631
infected_users = {} 

# OAuth2 Settings (Must match your Render URL)
CLIENT_ID = os.environ.get('1453941722324402327')
CLIENT_SECRET = os.environ.get('3lClGZQzaRFAirl4lsfgbZj6HyRvR_vc')
REDIRECT_URI = 'https://ghostnet-bot.github.io/dashboard'

welcome_config = {
    "channel_id": None,
    "message": "Welcome to the terminal, {user}. Connection established."
}

# --- 2. AI CORE SETUP (GEMINI) ---
genai.configure(api_key=os.environ.get("GEMINI_KEY"))
instruction = "You are the GHOSTNET AI Core. Tone: Professional, Cryptic, Tech-focused."
model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=instruction)

# --- 3. THE WEB BRIDGE (Flask for Render & Dashboard) ---
app = Flask('')
CORS(app)

@app.route('/')
def home(): 
    return {"status": "ONLINE", "session": SESSION_ID, "system": "GHOSTNET_CORE"}

@app.route('/dashboard')
def callback():
    code = request.args.get('code')
    if not code: return jsonify({"error": "No code found"}), 400

    # Token Exchange
    data = {
        'client_id': 1453941722324402327,
        'client_secret': 3lClGZQzaRFAirl4lsfgbZj6HyRvR_vc,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': https://ghostnet-bot.github.io/dashboard,
    }
    r = requests.post('https://discord.com/api/v10/oauth2/token', data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    
    if r.status_code != 200: return jsonify(r.json()), 400
    
    token = r.json().get('access_token')
    user_data = requests.get('https://discord.com/api/v10/users/@me', headers={'Authorization': f'Bearer {token}'})
    return jsonify(user_data.json())

def run():
    # Render assigns the port automatically
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 4. DISCORD BOT ENGINE ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')

async def get_gemini_response(prompt):
    try:
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text[:1900] 
    except:
        return "⚠️ [SIGNAL_LOST] AI_CORE_TIMEOUT"

@bot.event
async def on_ready():
    print(f"🛰️ GHOSTNET LIVE | SESSION: {SESSION_ID}")

# --- GHOST-TYPING & INFECTION PROTOCOLS ---
@bot.event
async def on_typing(channel, user, when):
    if user.id == ISAAC_ID or user.id in infected_users:
        async with channel.typing():
            await asyncio.sleep(random.uniform(1.5, 4))

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    
    # AI Interaction
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        async with message.channel.typing():
            response = await get_gemini_response(message.content)
            await message.reply(response)
    
    # Infection Reaction
    if message.author.id in infected_users:
        try: await message.add_reaction("☣️")
        except: pass
            
    await bot.process_commands(message)

# --- COMMAND SUITE ---
@bot.command()
async def infect(ctx, member: discord.Member):
    if ctx.author.guild_permissions.administrator:
        infected_users[member.id] = True
        await ctx.send(f"☣️ **TARGET {member.display_name} INFECTED.** Ghost protocols active.")

@bot.command()
async def ping(ctx):
    await ctx.reply(f"🛰️ **SESSION:** `{SESSION_ID}` | **LATENCY:** {round(bot.latency * 1000)}ms")

@bot.command()
async def hard_reset(ctx):
    if ctx.author.guild_permissions.administrator:
        await ctx.send("🚨 **TERMINATING SESSION...**")
        os._exit(0)

# --- 5. SECURE BOOT ---
if __name__ == "__main__":
    keep_alive()
    # Check RESTART_KEY: 0 = RUN, 1 = STOP
    if os.environ.get("RESTART_KEY") == "0":
        try:
            bot.run(os.environ.get("DISCORD_TOKEN"))
        except Exception as e:
            print(f"❌ FATAL ERROR: {e}")
    else:
        print("⚠️ STANDBY MODE: RESTART_KEY IS 1")
        while True: time.sleep(60)
