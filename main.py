import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
import random
import sys
from flask import Flask, jsonify
from flask_cors import CORS  # <--- FIXED: Top-level import added back
from threading import Thread
import google.generativeai as genai

# --- DEBUG CHECK ---
# This helps us see if Render is actually installing your requirements.txt
try:
    import flask_cors
    import google.generativeai
    print("✅ SYSTEM: Libraries verified and ready.")
except ImportError as e:
    print(f"❌ SYSTEM ERROR: {e}")
    print("⚠️ Render is skipping your requirements.txt. Check Settings > Build Command.")

# --- 1. DATABASE ARCHITECTURE ---
def init_db():
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, team_id INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS teams (team_id INTEGER PRIMARY KEY AUTOINCREMENT, team_name TEXT UNIQUE, vault INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS blacklist (user_id INTEGER PRIMARY KEY, reason TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT, details TEXT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    conn.close()
    print("🛰️ DATABASE: economy.db verified.")

# --- 2. DASHBOARD API ---
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
    # Use port 10000 for Render
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

# --- 4. SLASH COMMANDS ---

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

# --- 5. EXECUTION ---
if __name__ == "__main__":
    # AI Config
    api_key = os.environ.get("GEMINI_KEY")
    if api_key:
        genai.configure(api_key=api_key)
    
    # Start Web Server
    Thread(target=run_web, daemon=True).start()
    
    # Run Bot
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ CRITICAL: DISCORD_TOKEN is missing in Render Environment Variables.")
