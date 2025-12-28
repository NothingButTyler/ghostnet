import discord
from discord.ext import commands
import os
import random
import time
from flask import Flask
from threading import Thread

# --- 1. WEB SERVER ---
app = Flask('')
@app.route('/')
def home():
    return "GHOSTNET: ONLINE"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. BOT SETUP ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
start_time = time.time()

@bot.event
async def on_ready():
    print(f'>>> SUCCESS: {bot.user} is online.')

# --- 3. COMMANDS ---
@bot.command()
async def ping(ctx):
    await ctx.send("```fix\nPONG: Mainframe stable.```")

@bot.command()
async def hack(ctx, target: discord.Member = None):
    if not target:
        await ctx.send("Target required.")
        return
    msg = await ctx.send(f"```fix\n[BREACHING]: {target.name}...```")
    # This 'await' is INSIDE a function, so it is safe!
    await ctx.send(f"```diff\n+ [DONE]: {target.name} pwned.```")

# --- 4. THE STARTUP (THE FIX) ---
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        # bot.run handles the loop, so no 'await' is needed here!
        bot.run(token)
    else:
        print("TOKEN NOT FOUND")
async def on_ready():
    print(f'>>> SUCCESS: {bot.user} is connected to Discord.')

@bot.command()
async def ping(ctx):
    await ctx.send("```fix\nPONG: Connection Stable.```")

# --- STARTUP ---
if __name__ == "__main__":
    try:
        keep_alive()
        token = os.environ.get("DISCORD_TOKEN")
        if not token:
            print(">>> CRITICAL: DISCORD_TOKEN is missing in Render Environment!")
        else:
            print(">>> SYSTEM: Attempting Discord login...")
            bot.run(token)
    except Exception as e:
        print(f">>> CRITICAL FAILURE: {e}")
    print(f'>>> LOG: {bot.user} logged into mainframe.')

# --- 3. HACKER COMMANDS ---
@bot.command()
async def hack(ctx, target: discord.Member = None):
    if not target:
        await ctx.send("Specify a target to breach.")
        return
    msg = await ctx.send(f"```fix\n[INITIATING BREACH]: {target.name}...```")
    await discord.utils.sleep_until(discord.utils.utcnow() + discord.timedelta(seconds=2))
    await msg.edit(content=f"```fix\n[SUCCESS]: {target.name} has been pwned. IP: {random.randint(100,999)}.0.0.1```")

@bot.command()
async def status(ctx):
    uptime = int(time.time() - start_time)
    await ctx.send(f"```yaml\nUPTIME: {uptime}s\nCONNECTION: STABLE\nWEB_SERVER: ACTIVE\n```")

# --- 4. EXECUTION ---
if __name__ == "__main__":
    keep_alive() # Start the Flask server first
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("CRITICAL ERROR: NO DISCORD_TOKEN FOUND")
        await ctx.send("Specify a target to breach.")
        return

    steps = [
        f"🔍 Locating {target.name}'s IP...",
        "⚡ Brute-forcing SSH credentials...",
        "📂 Extracting 'secret_cookies.txt'...",
        "🛰️ Routing traffic through 7 proxies...",
        f"✅ Breach complete. {target.name} has been pwned."
    ]
    
    msg = await ctx.send(f"```fix\nInitializing breach on {target.name}...```")
    for step in steps:
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.timedelta(seconds=1.5))
        await msg.edit(content=f"```fix\n{step}```")

# 5. Bonus Feature: "The Matrix" (Encrypted messages)
@bot.command()
async def encrypt(ctx, *, text):
    """Turns your text into a fake hex-code string."""
    encrypted = "".join(hex(ord(c))[2:] for c in text)
    await ctx.send(f"**DECRYPTED MESSAGE:**\n`0x{encrypted.upper()}`")

keep_alive() # Starts the web server
token = os.environ.get("DISCORD_TOKEN") # Set this in Render's Environment Variables
bot.run(token)


import time

start_time = time.time()

@bot.command()
async def status(ctx):
    """Displays the bot's system health and uptime."""
    current_time = time.time()
    uptime_seconds = int(current_time - start_time)
    
    # Calculate uptime in a readable format
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    await ctx.send(
        f"```yaml\n"
        f"--- [GHOSTNET SYSTEM STATUS] ---\n"
        f"UPTIME: {hours}h {minutes}m {seconds}s\n"
        f"HEARTBEAT: Stable\n"
        f"CONNECTION: Encrypted via UptimeRobot\n"
        f"MAIN_DIRECTORY: /code/\n"
        f"STATUS: Fully Operational\n"
        f"-------------------------------\n"
        f"```"
    )

