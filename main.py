import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
import pytz
import asyncio
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread

# --- 1. WEB SERVER (For UptimeRobot) ---
app = Flask('')
@app.route('/')
def home(): return "GHOSTNET CORE: ONLINE"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- 2. DATABASE ---
def init_db():
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    # Main User Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, 
            balance INTEGER DEFAULT 100, 
            last_daily_date TEXT, 
            streak INTEGER DEFAULT 0,
            has_joined INTEGER DEFAULT 0
        )
    """)
    # Inventory Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            user_id INTEGER,
            item_name TEXT,
            quantity INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, item_name)
        )
    """)
    conn.commit()
    conn.close()

# --- 3. WELCOME SYSTEM ---
async def send_welcome_dm(user: discord.User):
    # Give Player Pack
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO inventory (user_id, item_name, quantity) VALUES (?, ?, ?)", 
                   (user.id, "Player Pack", 1))
    conn.commit()
    conn.close()

    embed = discord.Embed(
        title="Welcome to [**GHOSTNET**](https://ghostnet-bot.github.io/) 🪙",
        description="You received a **Player Pack** 📦! Use `/use item: Player Pack` to claim your starter bits.",
        color=0x2b2d31
    )
    embed.set_thumbnail(url="https://i.imgur.com/image_90951b.png")
    try: await user.send(embed=embed)
    except: pass

# --- 4. BOT SETUP ---
class GhostNet(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        init_db()
        Thread(target=run_web, daemon=True).start()
        await self.tree.sync()

bot = GhostNet()

@bot.event
async def on_app_command_completion(interaction: discord.Interaction, command: app_commands.Command):
    user_id = interaction.user.id
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("SELECT has_joined FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row or row[0] == 0:
        cursor.execute("INSERT OR REPLACE INTO users (user_id, has_joined) VALUES (?, 1)", (user_id,))
        conn.commit()
        await send_welcome_dm(interaction.user)
    conn.close()

# --- 5. COMMANDS ---
@bot.tree.command(name="daily", description="Claim your bits (Resets 12AM EST)")
async def daily(interaction: discord.Interaction):
    user_id = interaction.user.id
    est = pytz.timezone('US/Eastern')
    now_est = datetime.now(est)
    today_str = now_est.strftime('%Y-%m-%d')
    
    # Calculate next reset timestamp
    next_reset_dt = (est.localize(datetime(now_est.year, now_est.month, now_est.day, 0, 0, 0)) + timedelta(days=1))
    reset_ts = int(next_reset_dt.timestamp())
    
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cursor.execute("SELECT balance, last_daily_date, streak FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()

    if res and res[1] == today_str:
        embed = discord.Embed(title="🚫 Already Claimed", description=f"Next reset <t:{reset_ts}:R>", color=0xff4b4b)
        await interaction.response.send_message(embed=embed)
        conn.close()
        return

    streak = (res[2] if res else 0) + 1
    total_reward = 100000 + (1080 * streak)
    
    cursor.execute("UPDATE users SET balance = balance + ?, last_daily_date = ?, streak = ? WHERE user_id = ?", 
                   (total_reward, today_str, streak, user_id))
    conn.commit()
    conn.close()

    embed = discord.Embed(title=f"💳 {interaction.user.display_name}'s Daily", color=0x2b2d31)
    embed.add_field(name="Reward", value=f"**{total_reward:,}** bits", inline=True)
    embed.add_field(name="Next Daily", value=f"<t:{reset_ts}:R>", inline=True)
    embed.add_field(name="Streak", value=f"{streak}", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="use", description="Use an item")
async def use(interaction: discord.Interaction, item: str):
    user_id = interaction.user.id
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()

    cursor.execute("SELECT quantity FROM inventory WHERE user_id = ? AND item_name = ?", (user_id, item.title()))
    res = cursor.fetchone()

    if not res or res[0] <= 0:
        await interaction.response.send_message(f"❌ You don't have a **{item}**!", ephemeral=True)
    elif item.title() == "Player Pack":
        cursor.execute("UPDATE inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_name = ?", (user_id, "Player Pack"))
        cursor.execute("UPDATE users SET balance = balance + 50000 WHERE user_id = ?", (user_id,))
        await interaction.response.send_message("📦 You opened your **Player Pack** and found **50,000** bits!")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    bot.run(os.environ.get("DISCORD_TOKEN"))
