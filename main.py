import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
import random
import asyncio
from flask import Flask, jsonify
from flask_cors import CORS
from threading import Thread

# --- 1. DASHBOARD SETUP ---
app = Flask('')
CORS(app)

@app.route('/')
def home():
    return "GHOSTNET CORE: ONLINE"

@app.route('/api/status')
def status():
    return jsonify({"status": "online", "systems": "nominal"})

def run_web():
    # Render specifically looks for port 10000
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- 2. DATABASE SYSTEM ---
def init_db():
    try:
        conn = sqlite3.connect("economy.db")
        cursor = conn.cursor()
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY, 
                balance INTEGER DEFAULT 100
            )
        """)
        # Create blacklist table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blacklist (
                user_id INTEGER PRIMARY KEY, 
                reason TEXT
            )
        """)
        conn.commit()
        conn.close()
        print("✅ DATABASE: Connection established.")
    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}")

# --- 3. BOT ARCHITECTURE ---
class GhostNet(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Start the web server in the background
        thread = Thread(target=run_web)
        thread.daemon = True
        thread.start()
        
        # Initialize Database
        init_db()
        
        # Sync Slash Commands
        await self.tree.sync()
        print(f"✅ CORE: Logged in as {self.user} (ID: {self.user.id})")

bot = GhostNet()

# --- 4. COMMANDS ---

@bot.tree.command(name="ping", description="Check terminal latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"⏳ **LATENCY:** {round(bot.latency * 1000)}ms")

@bot.tree.command(name="work", description="Execute a task for bits")
async def work(interaction: discord.Interaction):
    reward = random.randint(50, 200)
    user_id = interaction.user.id
    
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0)", (user_id,))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
    conn.commit()
    conn.close()
    
    await interaction.response.send_message(f"💻 **TASK SUCCESS:** You earned `{reward}` bits.")

@bot.tree.command(name="balance", description="Check your current bit count")
async def balance(interaction: discord.Interaction):
    user_id = interaction.user.id
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    bal = result[0] if result else 0
    await interaction.response.send_message(f"🏦 **ACCOUNT:** {interaction.user.name} | **BALANCE:** `{bal}` bits")

# --- 5. EXECUTION ---
if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("❌ CRITICAL ERROR: DISCORD_TOKEN not found in environment.")
    else:
        bot.run(token)
