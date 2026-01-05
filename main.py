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

# --- DISCORD OAUTH2 (CRITICAL: MUST MATCH DEV PORTAL) ---
CLIENT_ID = 'YOUR_CLIENT_ID'
CLIENT_SECRET = 'YOUR_CLIENT_SECRET'
REDIRECT_URI = 'https://ghostnet-bot.github.io/dashboard.html'

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
    return {"status": "ONLINE", "session": SESSION_ID}

@app.route('/login-callback')
def callback():
    code = request.args.get('code')
    if not code: 
        print("DEBUG: No code found in callback!")
        return jsonify({"error": "No code"}), 400

    # Step 1: Exchange code for Token
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post('https://discord.com/api/v10/oauth2/token', data=data, headers=headers)
    
    if r.status_code != 200:
        print(f"DEBUG: Token Exchange Failed: {r.text}")
        return jsonify(r.json()), 400
    
    token = r.json().get('access_token')

    # Step 2: Get User Data
    user_r = requests.get('https://discord.com/api/v10/users/@me', headers={
        'Authorization': f'Bearer {token}'
    })
    
    print(f"DEBUG: User Authorized: {user_r.json().get('username')}")
    return jsonify(user_r.json())

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

# --- 3. BOT LOGIC ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')

async def get_gemini_response(prompt):
    try:
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text[:1900] 
    except Exception as e:
        return "⚠️ [SIGNAL_LOST] AI_CORE_TIMEOUT"

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        async with message.channel.typing():
            response = await get_gemini_response(message.content)
            if response: await message.reply(response)
    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
