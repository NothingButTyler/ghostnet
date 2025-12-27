import discord
from discord.ext import commands
import random
import os
from flask import Flask
from threading import Thread

# --- KEEP ALIVE SECTION FOR RENDER ---
app = Flask('')
@app.route('/')
def home():
    return "System Online: Hacker Bot is Running."

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- BOT LOGIC ---
intents = discord.Intents.default()
intents.members = True  # Required for welcome/goodbye and auto-role
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 3. Auto-role configuration
AUTO_ROLE_NAME = "Initiate" # Change this to the role name you want

@bot.event
async def on_ready():
    print(f'--- CONNECTION ESTABLISHED: {bot.user} ---')
    print('Injecting scripts into mainframe...')

# 1. Welcome Users
@bot.event
async def on_member_join(member):
    channel = member.guild.system_channel
    if channel:
        responses = [
            f"ID detected: {member.mention}. Bypassing firewall... Access granted. Welcome to the grid.",
            f"New node connected: {member.mention}. Initializing encrypted handshake...",
        ]
        await channel.send(f"```json\n[SYSTEM]: {random.choice(responses)}\n```")
    
    # Auto-role logic
    role = discord.utils.get(member.guild.roles, name=AUTO_ROLE_NAME)
    if role:
        await member.add_roles(role)

# 2. Goodbye Users
@bot.event
async def on_member_remove(member):
    channel = member.guild.system_channel
    if channel:
        await channel.send(f"```diff\n- [WARNING]: Connection lost with {member.name}. Signal trace failed. Terminating session...\n```")

# 4. Fake Hacker Messages
@bot.command()
async def hack(ctx, target: discord.Member = None):
    if not target:
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
