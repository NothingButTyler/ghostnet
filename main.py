import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
import time
import random 
import requests 
from datetime import datetime, timedelta
import pytz 
from flask import Flask, jsonify 
from flask_cors import CORS
from threading import Thread
import google.generativeai as genai

# --- 1. DASHBOARD ---
app = Flask('')
CORS(app)

@app.route('/')
def home(): return "GHOSTNET CORE: ONLINE"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- 2. DATABASE ---
def init_db():
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, 
            balance INTEGER DEFAULT 100, 
            last_daily_date TEXT, 
            streak INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# --- 3. BOT SETUP ---
class GhostNet(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        init_db()
        Thread(target=run_web, daemon=True).start()
        await self.tree.sync()
        print(f"✅ GHOSTNET: Operational.")

bot = GhostNet()

# --- 4. THE DAILY COMMAND ---

@bot.tree.command(name="daily", description="Claim your daily bits (Resets 12:00 AM EST)")
async def daily(interaction: discord.Interaction):
    user_id = interaction.user.id
    
    # Timezone Logic
    est = pytz.timezone('US/Eastern')
    now_est = datetime.now(est)
    today_str = now_est.strftime('%Y-%m-%d')
    
    # Calculate Next Midnight EST
    tomorrow = now_est + timedelta(days=1)
    next_midnight = est.localize(datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0))
    next_midnight_ts = int(next_midnight.timestamp())

    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cursor.execute("SELECT balance, last_daily_date, streak FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    balance, last_daily_date, streak = res

    # --- PUBLIC ERROR EMBED ---
    if last_daily_date == today_str:
        embed_error = discord.Embed(
            title="🚫 Already Claimed",
            # Use :R for relative time ("in 5 hours", "in a day")
            description=f"You already got your daily today! Try again <t:{next_midnight_ts}:R>",
            color=0xff4b4b 
        )
        embed_error.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed_error)
        conn.close()
        return

    # --- STREAK LOGIC ---
    yesterday_str = (now_est - timedelta(days=1)).strftime('%Y-%m-%d')
    
    if last_daily_date == yesterday_str:
        new_streak = streak + 1
    elif last_daily_date is None:
        new_streak = 1
    else:
        last_dt = datetime.strptime(last_daily_date, '%Y-%m-%d')
        days_missed = (now_est.replace(tzinfo=None) - last_dt).days - 1
        new_streak = max(0, streak - days_missed) + 1

    total_reward = 100000 + (1080 * new_streak)

    cursor.execute("UPDATE users SET balance = balance + ?, last_daily_date = ?, streak = ? WHERE user_id = ?", 
                   (total_reward, today_str, new_streak, user_id))
    conn.commit()
    conn.close()

    # --- SUCCESS EMBED ---
    embed = discord.Embed(
        title=f"💳 {interaction.user.name}'s Daily Coins",
        description=f"**{total_reward:,}** was placed in your wallet!",
        color=0x2b2d31
    )
    embed.add_field(name="Base", value="⟡ 100,000", inline=True)
    embed.add_field(name="Streak Bonus", value=f"⟡ {1080 * new_streak:,}", inline=True)
    embed.add_field(name="Donor Bonus", value="⟡ 0", inline=True)
    
    # "Next Daily" now formatted as a relative countdown
    embed.add_field(name="Next Daily", value=f"<t:{next_midnight_ts}:R>", inline=True)
    embed.add_field(name="Next Item Reward", value="Daily Box in 1 day", inline=True)
    embed.add_field(name="Streak", value=str(new_streak), inline=True)
    
    await interaction.response.send_message(embed=embed)

# --- 5. RUN ---
if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    api_key = os.environ.get("GEMINI_KEY")
    if api_key:
        genai.configure(api_key=api_key)
    bot.run(token)
