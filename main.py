import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
import random
from flask import Flask, jsonify
from threading import Thread

# --- 1. DATABASE ARCHITECTURE (The "Creator") ---
def init_db():
    # This automatically creates 'economy.db' if it doesn't exist
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    
    # Create Economy Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            team_id INTEGER
        )
    """)
    
    # Create Security/Blacklist Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blacklist (
            user_id INTEGER PRIMARY KEY,
            reason TEXT
        )
    """)
    
    # Create Security Logs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT,
            details TEXT,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("🛰️ DATABASE: economy.db is synced and secure.")

# --- 2. DASHBOARD API (Flask) ---
app = Flask('')

@app.route('/')
def home():
    return "GHOSTNET CORE: ONLINE"

@app.route('/api/status')
def get_status():
    return jsonify({"status": "active", "database": "connected"})

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- 3. BOT CORE SETUP ---
class GhostNet(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        init_db()  # Runs the database creator
        await self.tree.sync() # Syncs slash commands
        print(f"🛰️ GHOSTNET: Systems synchronized.")

bot = GhostNet()

# --- 4. SECURITY PROTOCOLS ---

# This check runs before EVERY command to block blacklisted users
@bot.check
async def is_not_blacklisted(ctx):
    with sqlite3.connect("economy.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM blacklist WHERE user_id = ?", (ctx.author.id,))
        if cursor.fetchone():
            await ctx.send("🚫 **ACCESS DENIED.** You are blacklisted from GHOSTNET.")
            return False
    return True

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    log_text = f"Content: {message.content} | Author: {message.author}"
    with sqlite3.connect("economy.db") as conn:
        conn.execute("INSERT INTO logs (event, details) VALUES (?, ?)", ("MSG_DELETE", log_text))

# --- 5. SLASH COMMANDS ---

@bot.tree.command(name="work", description="Earn bits for the economy")
async def work(interaction: discord.Interaction):
    gain = random.randint(50, 150)
    user_id = interaction.user.id
    
    with sqlite3.connect("economy.db") as conn:
        conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (gain, user_id))
    
    await interaction.response.send_message(f"💻 Task complete! You earned **{gain} bits**.")

@bot.tree.command(name="blacklist_user", description="[ADMIN] Ban a user from the bot")
@app_commands.checks.has_permissions(administrator=True)
async def blacklist_user(interaction: discord.Interaction, user: discord.Member, reason: str):
    with sqlite3.connect("economy.db") as conn:
        conn.execute("INSERT OR REPLACE INTO blacklist (user_id, reason) VALUES (?, ?)", (user.id, reason))
    await interaction.response.send_message(f"🚫 {user.name} has been blacklisted for: {reason}")

# --- 6. EXECUTION ---
if __name__ == "__main__":
    # Start the web server thread
    Thread(target=run_web, daemon=True).start()
    # Start the bot
    bot.run(os.environ.get("DISCORD_TOKEN"))
