import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
import time
import random 
from datetime import datetime, timedelta
import pytz 
from flask import Flask, jsonify 
from flask_cors import CORS
from threading import Thread

# --- 1. WEB SERVER ---
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
            bank INTEGER DEFAULT 0,
            inventory_val INTEGER DEFAULT 0,
            last_daily_date TEXT, 
            streak INTEGER DEFAULT 0
        )
    """)
    # Ensure all columns exist
    cursor.execute("PRAGMA table_info(users)")
    cols = [c[1] for c in cursor.fetchall()]
    if "bank" not in cols: cursor.execute("ALTER TABLE users ADD COLUMN bank INTEGER DEFAULT 0")
    if "inventory_val" not in cols: cursor.execute("ALTER TABLE users ADD COLUMN inventory_val INTEGER DEFAULT 0")
    conn.commit()
    conn.close()

# --- 3. BOT CORE SETUP ---
class GhostNet(commands.Bot):
    def __init__(self):
        # Using a standard prefix as backup, but focusing on Slash Commands
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        init_db()
        Thread(target=run_web, daemon=True).start()
        
        # ⚡ FORCE SYNC: This clears old cache and pushes ALL commands
        print("📡 GHOSTNET: Syncing command tree...")
        await self.tree.sync()
        print(f"✅ GHOSTNET: {len(self.tree.get_commands())} commands synced to Discord.")

bot = GhostNet()

# --- 4. THE COMMANDS ---

@bot.tree.command(name="balance", description="View your wallet, bank, and total net worth")
async def balance(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (target.id,))
    cursor.execute("SELECT balance, bank, inventory_val FROM users WHERE user_id = ?", (target.id,))
    row = cursor.fetchone()
    conn.close()

    wallet, bank, inv = row
    net_worth = wallet + bank + inv
    
    embed = discord.Embed(title=f"💳 {target.display_name}'s Net Worth", color=0x2b2d31)
    embed.set_author(name="Global Rank: #---", icon_url=target.display_avatar.url)
    
    # Matching your screenshot UI
    embed.add_field(name="Coins", value=f"🟡 {wallet:,}\n🏛️ {bank:,} / 2,574,231\n🎒 {inv:,}", inline=True)
    embed.add_field(name="Net Worth", value=f"🟡 {net_worth:,}\nInventory: 📦 {inv:,}", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="daily", description="Claim your daily reward (Resets 12AM EST)")
async def daily(interaction: discord.Interaction):
    user_id = interaction.user.id
    est = pytz.timezone('US/Eastern')
    now_est = datetime.now(est)
    today_str = now_est.strftime('%Y-%m-%d')
    
    # Reset Calculation
    tomorrow = now_est + timedelta(days=1)
    next_midnight = est.localize(datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0))
    next_midnight_ts = int(next_midnight.timestamp())

    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cursor.execute("SELECT balance, last_daily_date, streak FROM users WHERE user_id = ?", (user_id,))
    balance, last_daily_date, streak = cursor.fetchone()

    if last_daily_date == today_str:
        embed_err = discord.Embed(title="🚫 Already Claimed", description=f"Next reset <t:{next_midnight_ts}:R>", color=0xff4b4b)
        embed_err.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed_err)
        conn.close()
        return

    # Streak Logic
    yesterday_str = (now_est - timedelta(days=1)).strftime('%Y-%m-%d')
    new_streak = (streak + 1) if last_daily_date == yesterday_str else 1
    
    reward = 100000 + (1080 * new_streak)
    cursor.execute("UPDATE users SET balance = balance + ?, last_daily_date = ?, streak = ? WHERE user_id = ?", (reward, today_str, new_streak, user_id))
    conn.commit()
    conn.close()

    embed = discord.Embed(title=f"💳 {interaction.user.name}'s Daily Coins", color=0x2b2d31)
    embed.add_field(name="Base", value="⟡ 100,000", inline=True)
    embed.add_field(name="Streak Bonus", value=f"⟡ {1080 * new_streak:,}", inline=True)
    embed.add_field(name="Next Daily", value=f"<t:{next_midnight_ts}:R>", inline=True)
    embed.add_field(name="Streak", value=str(new_streak), inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="work", description="Earn some quick bits")
async def work(interaction: discord.Interaction):
    gain = random.randint(500, 1500)
    with sqlite3.connect("economy.db") as conn:
        conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (gain, interaction.user.id))
    await interaction.response.send_message(f"💼 You earned **{gain:,}** bits!")

# --- 5. RUN ---
if __name__ == "__main__":
    bot.run(os.environ.get("DISCORD_TOKEN"))
