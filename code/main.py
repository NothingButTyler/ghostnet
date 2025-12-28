import discord
from discord.ext import commands
import random
import os
import time
from flask import Flask
from threading import Thread

# --- 1. WEB SERVER (THE HEARTBEAT) ---
app = Flask('')

@app.route('/')
def home():
    return "STATUS: SYSTEM OPERATIONAL // GHOSTNET ONLINE"

def run():
    # Render provides a 'PORT' environment variable automatically
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True # This ensures the thread dies when the main script stops
    t.start()

# --- 2. BOT INITIALIZATION ---
intents = discord.Intents.default()
intents.members = True  
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
start_time = time.time()
AUTO_ROLE_NAME = "Initiate" 

@bot.event
async def on_ready():
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

