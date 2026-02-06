import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
import time
import random  # <--- FIXED: Restored for future use
from flask import Flask, jsonify
from flask_cors import CORS
from threading import Thread

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
            balance INTEGER DEFAULT 0,
            last_daily INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# --- 3. BOT CORE ---
class GhostNet(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        init_db()
        Thread(target=run_web, daemon=True).start()
        await self.tree.sync()
        print(f"✅ GHOSTNET: {self.user} Online")

bot = GhostNet()

# --- 4. COMMANDS ---

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
        # Subtract 1 streak for every full day missed after the first 48h
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

@bot.tree.command(name="balance", description="Check your wallet")
async def balance(interaction: discord.Interaction):
    user_id = interaction.user.id
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance, streak FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    
    bal = res[0] if res else 0
    stk = res[1] if res else 0
    await interaction.response.send_message(f"💰 **Wallet:** {bal:,} bits | **Streak:** {stk}")

# --- 5. RUN ---
if __name__ == "__main__":
    bot.run(os.environ.get("DISCORD_TOKEN"))
