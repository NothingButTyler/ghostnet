import discord
from discord.ext import commands
import os, asyncio, random, time, uuid, requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread
import google.generativeai as genai

# --- 1. CONFIGURATION ---
SESSION_ID = str(uuid.uuid4())[:8]
ISAAC_ID = 1444073106384621631
infected_users = {} 

# --- USE ENV VARIABLES FOR SECURITY ---
CLIENT_ID = os.environ.get('CLIENT_ID') # Put your Client ID in Render Env
CLIENT_SECRET = os.environ.get('CLIENT_SECRET') # Put your Secret in Render Env
# This MUST match what you saved in the Dev Portal
REDIRECT_URI = 'https://ghostnet.onrender.com/login-callback' 

welcome_config = {
    "channel_id": None,
    "message": "Welcome to the terminal, {user}. Connection established."
}

# --- AI SETUP ---
genai.configure(api_key=os.environ.get("GEMINI_KEY"))
instruction = "You are the GHOSTNET AI Core. Tone: Professional, Cryptic, Tech-focused."
model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=instruction)

# --- 2. THE WEB BRIDGE (Flask) ---
app = Flask('')
CORS(app)

@app.route('/')
def home(): 
    return {"status": "ONLINE", "session": SESSION_ID, "bot": "GHOSTNET"}

@app.route('/login-callback')
def callback():
    code = request.args.get('code')
    if not code: return jsonify({"error": "No code"}), 400

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
    user_r = requests.get('https://discord.com/api/v10/users/@me', headers={'Authorization': f'Bearer {token}'})
    return jsonify(user_r.json())

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 3. BOT LOGIC ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

async def get_gemini_response(prompt):
    try:
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text[:1900] 
    except:
        return "⚠️ [SIGNAL_LOST] AI_CORE_TIMEOUT"

@bot.event
async def on_ready():
    print(f"🛰️ GHOSTNET LIVE | SESSION {SESSION_ID}")

# --- GHOST TYPING ENGINE ---
@bot.event
async def on_typing(channel, user, when):
    if user.id == ISAAC_ID or user.id in infected_users:
        async with channel.typing():
            await asyncio.sleep(random.uniform(1, 3))

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    
    # AI Response if mentioned
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        async with message.channel.typing():
            response = await get_gemini_response(message.content)
            await message.reply(response)
            
    await bot.process_commands(message)

# --- ADD BACK THE MISSING !INFECT COMMAND ---
@bot.command()
async def infect(ctx, member: discord.Member):
    if ctx.author.guild_permissions.administrator:
        infected_users[member.id] = True
        await ctx.send(f"☣️ **TARGET {member.display_name} INFECTED.** Ghost protocols active.")

if __name__ == "__main__":
    keep_alive()
    # Check RESTART_KEY before running
    if os.environ.get("RESTART_KEY") == "0":
        bot.run(os.environ.get("DISCORD_TOKEN"))
    else:
        print("⚠️ STANDBY: RESTART_KEY is 1.")
