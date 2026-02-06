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

# --- 1. DASHBOARD SETUP ---
app = Flask('')
CORS(app)

@app.route('/')
def home():
    return "GHOSTNET CORE: ONLINE"

def run_web():
    # Render looks for port 10000 to keep the service "Live"
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- 2. DATABASE SYSTEM ---
def init_db():
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    # Users & Balance table
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 100)")
    # Blacklist table
    cursor.execute("CREATE TABLE IF NOT EXISTS blacklist (user_id INTEGER PRIMARY KEY, reason TEXT)")
    conn.commit()
    conn.close()
    print("✅ DATABASE: Systems verified.")

# --- 3. BOT ARCHITECTURE ---
class GhostNet(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        init_db()
        # Starts the web server in a background thread
        Thread(target=run_web, daemon=True).start()
        await self.tree.sync()
        print(f"✅ CORE: {self.user} is operational.")

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
    
    await interaction.response.send_message(f"💻 **TASK SUCCESS:** Earned `{reward}` bits.")

# --- 5. EXECUTION ---
if __name__ == "__main__":
    # AI Config (Optional)
    api_key = os.environ.get("GEMINI_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ CRITICAL: DISCORD_TOKEN not found in Render Environment Variables.")
