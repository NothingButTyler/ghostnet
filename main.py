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
    conn.commit()
    conn.close()

# --- 3. INTERACTIVE UI (Screenshot Accurate Toggle) ---
class BalanceView(discord.ui.View):
    def __init__(self, target, wallet, bank, inv):
        super().__init__(timeout=60)
        self.target = target
        self.wallet = wallet
        self.bank = bank
        self.inv = inv
        self.net_worth = wallet + bank + inv

    @discord.ui.button(label="Balances", style=discord.ButtonStyle.secondary)
    async def balances_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title=f"💳 {self.target.display_name}'s Balances", color=0x2b2d31)
        embed.add_field(
            name="Coins", 
            value=f"🪙 {self.wallet:,}\n🏦 {self.bank:,} / 2,574,231\n🎒 {self.inv:,}", 
            inline=False
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Net Worth", style=discord.ButtonStyle.primary)
    async def networth_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title=f"💳 {self.target.display_name}'s Net Worth", color=0x2b2d31)
        embed.set_author(name=f"Global Rank: #---", icon_url=self.target.display_avatar.url)
        # Left side: Breakdown
        embed.add_field(name="Coins", value=f"🪙 {self.wallet:,}\n🏛️ {self.bank:,} / 2,574,231\n🎒 {self.inv:,}", inline=True)
        # Right side: Summary
        embed.add_field(name="Net Worth", value=f"🪙 {self.net_worth:,}\nInventory: 📦 {self.inv:,}", inline=True)
        await interaction.response.edit_message(embed=embed, view=self)

# --- 4. BOT CORE SETUP ---
class GhostNet(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        init_db()
        Thread(target=run_web, daemon=True).start()
        await self.tree.sync()
        print(f"✅ GHOSTNET: Live with 🪙 iconography.")

bot = GhostNet()

# --- 5. ECONOMY COMMANDS ---

@bot.tree.command(name="balance", description="Check balances or net worth")
async def balance(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (target.id,))
    cursor.execute("SELECT balance, bank, inventory_val FROM users WHERE user_id = ?", (target.id,))
    wallet, bank, inv = cursor.fetchone()
    conn.close()

    net_worth = wallet + bank + inv
    view = BalanceView(target, wallet, bank, inv)
    
    # Matching the 'Net Worth' image as the default starting view
    embed = discord.Embed(title=f"💳 {target.display_name}'s Net Worth", color=0x2b2d31)
    embed.set_author(name="Global Rank: #---", icon_url=target.display_avatar.url)
    embed.add_field(name="Coins", value=f"🪙 {wallet:,}\n🏛️ {bank:,} / 2,574,231\n🎒 {inv:,}", inline=True)
    embed.add_field(name="Net Worth", value=f"🪙 {net_worth:,}\nInventory: 📦 {inv:,}", inline=True)
    
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="daily", description="Claim daily bits (Resets 12:00 AM EST)")
async def daily(interaction: discord.Interaction):
    user_id = interaction.user.id
    est = pytz.timezone('US/Eastern')
    now_est = datetime.now(est)
    today_str = now_est.strftime('%Y-%m-%d')
    next_midnight_ts = int((est.localize(datetime(now_est.year, now_est.month, now_est.day, 0, 0, 0)) + timedelta(days=1)).timestamp())

    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cursor.execute("SELECT balance, last_daily_date, streak FROM users WHERE user_id = ?", (user_id,))
    balance, last_daily_date, streak = cursor.fetchone()

    if last_daily_date == today_str:
        embed_err = discord.Embed(title="🚫 Already Claimed", description=f"Try again <t:{next_midnight_ts}:R>", color=0xff4b4b)
        await interaction.response.send_message(embed=embed_err)
        conn.close()
        return

    yesterday_str = (now_est - timedelta(days=1)).strftime('%Y-%m-%d')
    new_streak = (streak + 1) if last_daily_date == yesterday_str else 1
    reward = 100000 + (1080 * new_streak)

    cursor.execute("UPDATE users SET balance = balance + ?, last_daily_date = ?, streak = ? WHERE user_id = ?", (reward, today_str, new_streak, user_id))
    conn.commit()
    conn.close()

    embed = discord.Embed(title=f"💳 {interaction.user.name}'s Daily Coins", color=0x2b2d31)
    embed.add_field(name="Base", value="🪙 100,000", inline=True)
    embed.add_field(name="Streak Bonus", value=f"🪙 {1080 * new_streak:,}", inline=True)
    embed.add_field(name="Next Daily", value=f"<t:{next_midnight_ts}:R>", inline=True)
    embed.add_field(name="Streak", value=f"🔥 {new_streak}", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="work", description="Earn bits")
async def work(interaction: discord.Interaction):
    gain = random.randint(500, 1500)
    with sqlite3.connect("economy.db") as conn:
        conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (gain, interaction.user.id))
    await interaction.response.send_message(f"💼 You earned **🪙 {gain:,}** bits!")

# --- 6. RUN ---
if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    api_key = os.environ.get("GEMINI_KEY")
    if api_key: genai.configure(api_key=api_key)
    bot.run(token)
