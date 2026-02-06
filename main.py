import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
import time
import random
from flask import Flask, jsonify
from flask_cors import CORS
from threading import Thread
import google.generativeai as genai

# --- 1. DASHBOARD & WEB SERVER ---
app = Flask('')
CORS(app)

@app.route('/')
def home():
    return "GHOSTNET CORE: ONLINE"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- 2. DATABASE ARCHITECTURE ---
def init_db():
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    
    # Base Tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, 
            balance INTEGER DEFAULT 100
        )
    """)
    
    # --- MIGRATION BLOCK: Adds columns if they are missing ---
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if "last_daily" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN last_daily INTEGER DEFAULT 0")
    if "streak" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN streak INTEGER DEFAULT 0")
        
    cursor.execute("CREATE TABLE IF NOT EXISTS teams (team_id INTEGER PRIMARY KEY AUTOINCREMENT, team_name TEXT UNIQUE, vault INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS blacklist (user_id INTEGER PRIMARY KEY, reason TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT, details TEXT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    
    conn.commit()
    conn.close()
    print("🛰️ DATABASE: Systems migrated and verified.")

# --- 3. BOT CORE SETUP ---
class GhostNet(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        init_db() 
        Thread(target=run_web, daemon=True).start()
        await self.tree.sync()
        print(f"🛰️ GHOSTNET: Logged in as {self.user}")

bot = GhostNet()

# --- 4. ECONOMY & DAILY COMMANDS ---

@bot.tree.command(name="daily", description="Claim your daily bits")
async def daily(interaction: discord.Interaction):
    user_id = interaction.user.id
    now = int(time.time())
    day_sec = 86400
    
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cursor.execute("SELECT balance, last_daily, streak FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    balance, last_daily, streak = res
    
    if now - last_daily < day_sec:
        next_claim = last_daily + day_sec
        await interaction.response.send_message(
            f"🚫 You already got your daily today! Try again <t:{next_claim}:R>", 
            ephemeral=True
        )
        return

    # Decreasing Streak Logic
    time_passed = now - last_daily
    if last_daily == 0:
        new_streak = 1
    elif time_passed < (day_sec * 2):
        new_streak = streak + 1
    else:
        days_missed = (time_passed // day_sec) - 1
        new_streak = max(0, streak - days_missed) + 1

    base_reward = 100000
    streak_bonus = 1080 * new_streak
    total_reward = base_reward + streak_bonus
    
    cursor.execute("UPDATE users SET balance = balance + ?, last_daily = ?, streak = ? WHERE user_id = ?", 
                   (total_reward, now, new_streak, user_id))
    conn.commit()
    conn.close()

    embed = discord.Embed(
        title=f"💳 {interaction.user.name}'s Daily Coins",
        description=f"**{total_reward:,}** was placed in your wallet!",
        color=discord.Color.from_rgb(43, 45, 49)
    )
    embed.add_field(name="Base", value=f"⟡ {base_reward:,}", inline=True)
    embed.add_field(name="Streak Bonus", value=f"⟡ {streak_bonus:,}", inline=True)
    embed.add_field(name="Donor Bonus", value="⟡ 0", inline=True)
    embed.add_field(name="Next Daily", value="in a day", inline=True)
    embed.add_field(name="Next Item Reward", value="Daily Box in 1 day", inline=True)
    embed.add_field(name="Streak", value=str(new_streak), inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ping", description="Check terminal latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"⏳ **LATENCY:** {round(bot.latency * 1000)}ms")

# --- 5. EXECUTION ---
if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_KEY")
    if api_key:
        genai.configure(api_key=api_key)
    
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ CRITICAL: DISCORD_TOKEN not found.")
