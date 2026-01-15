import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
import random
from flask import Flask, jsonify
from flask_cors import CORS 
from threading import Thread
import google.generativeai as genai 

# --- 1. DATABASE ARCHITECTURE ---
def init_db():
    # This creates 'economy.db' automatically on Render
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    # Economy & Teams
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, team_id INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS teams (team_id INTEGER PRIMARY KEY AUTOINCREMENT, team_name TEXT UNIQUE, vault INTEGER DEFAULT 0)")
    # Security
    cursor.execute("CREATE TABLE IF NOT EXISTS blacklist (user_id INTEGER PRIMARY KEY, reason TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT, details TEXT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    conn.close()
    print("🛰️ DATABASE: economy.db verified.")

# --- 2. DASHBOARD API (With CORS) ---
app = Flask('')
CORS(app) 

@app.route('/')
def home():
    return "GHOSTNET CORE: ONLINE"

@app.route('/api/leaderboard')
def get_leaderboard():
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 10")
    data = [{"user_id": r[0], "balance": r[1]} for r in cursor.fetchall()]
    conn.close()
    return jsonify(data)

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- 3. BOT CORE SETUP ---
class GhostNet(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        init_db() 
        await self.tree.sync()
        print("🛰️ GHOSTNET: Systems synchronized.")

bot = GhostNet()

# Storage for Welcome Config (Resets on restart)
welcome_config = {"channel_id": None, "message": "Welcome {user} to the server."}

# --- 4. EVENTS ---

@bot.event
async def on_member_join(member):
    if welcome_config["channel_id"]:
        channel = bot.get_channel(welcome_config["channel_id"])
        if channel:
            msg = welcome_config["message"].replace("{user}", member.mention)
            await channel.send(msg)

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    log_text = f"Content: {message.content} | Author: {message.author}"
    with sqlite3.connect("economy.db") as conn:
        conn.execute("INSERT INTO logs (event, details) VALUES (?, ?)", ("MSG_DELETE", log_text))

# --- 5. SLASH COMMANDS ---

@bot.tree.command(name="ping", description="Check terminal latency")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"⏳ **LATENCY:** {latency}ms")

@bot.tree.command(name="work", description="Earn bits")
async def work(interaction: discord.Interaction):
    gain = random.randint(50, 150)
    with sqlite3.connect("economy.db") as conn:
        conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (interaction.user.id,))
        conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (gain, interaction.user.id))
    await interaction.response.send_message(f"💻 Task complete! Earned **{gain} bits**.")

@bot.tree.command(name="blacklist", description="[ADMIN] Ban a user from the bot")
@app_commands.checks.has_permissions(administrator=True)
async def blacklist(interaction: discord.Interaction, user: discord.Member, reason: str):
    with sqlite3.connect("economy.db") as conn:
        conn.execute("INSERT OR REPLACE INTO blacklist (user_id, reason) VALUES (?, ?)", (user.id, reason))
    await interaction.response.send_message(f"🚫 {user.name} has been blacklisted.")

@bot.tree.command(name="hard-reset", description="Force restart the bot")
@app_commands.checks.has_permissions(administrator=True)
async def hard_reset(interaction: discord.Interaction):
    await interaction.response.send_message("🚨 Restarting...")
    os._exit(0)

# --- 6. SECURITY CHECK ---
@bot.check
async def is_not_blacklisted(ctx):
    with sqlite3.connect("economy.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM blacklist WHERE user_id = ?", (ctx.author.id,))
        if cursor.fetchone():
            return False # Silently block or add a message here
    return True

# --- 7. EXECUTION ---
if __name__ == "__main__":
    # AI Config
    api_key = os.environ.get("GEMINI_KEY")
    if api_key:
        genai.configure(api_key=api_key)

    Thread(target=run_web, daemon=True).start()
    bot.run(os.environ.get("DISCORD_TOKEN"))
