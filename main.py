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
            streak INTEGER DEFAULT 0,
            has_joined INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# --- 3. NEW PLAYER DM SYSTEM ---
async def send_welcome_dm(user: discord.User):
    embed = discord.Embed(
        title="Welcome to **GHOSTNET** 🪙",
        description=(
            "From fishing unique creatures to collecting hundreds of unique items, "
            "there are no limits to how you can play with your friends.\n\n"
            "You can get started by using `/use` and selecting your brand new "
            "**player pack** 📦 we just gifted you."
        ),
        color=0x2b2d31
    )
    embed.set_thumbnail(url="https://i.imgur.com/image_90951b.png") 
    
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Commands List", url="https://discord.com", style=discord.ButtonStyle.link))
    
    try:
        await user.send(embed=embed, view=view)
    except discord.Forbidden:
        pass

# --- 4. INTERACTIVE UI ---
class BalanceView(discord.ui.View):
    def __init__(self, target, data):
        super().__init__(timeout=120)
        self.target = target
        self.wallet, self.bank, self.inv = data
        self.total = self.wallet + self.bank + self.inv

    def get_net_worth_embed(self):
        embed = discord.Embed(title=f"{self.target.display_name}'s Net Worth", color=0x2b2d31)
        embed.add_field(name="Coins", value=f"🪙 {self.wallet:,}", inline=False)
        embed.add_field(name="Inventory", value=f"🎒 {self.inv:,}", inline=False)
        embed.add_field(name="Total", value=f"💼 {self.total:,}", inline=False)
        return embed

    def get_balances_embed(self):
        embed = discord.Embed(title=f"{self.target.display_name}'s Balances", color=0x2b2d31)
        embed.description = f"🪙 {self.wallet:,}\n🏛️ {self.bank:,} / 2,574,231"
        return embed

    @discord.ui.button(label="Balances", style=discord.ButtonStyle.secondary)
    async def balances(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.get_balances_embed(), view=self)

    @discord.ui.button(label="Net Worth", style=discord.ButtonStyle.secondary)
    async def net_worth(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.get_net_worth_embed(), view=self)

# --- 5. BOT SETUP ---
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

# --- 6. COMMANDS ---
@bot.tree.command(name="balance", description="Check your wallet and total net worth")
async def balance(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (target.id,))
    cursor.execute("SELECT balance, bank, inventory_val FROM users WHERE user_id = ?", (target.id,))
    data = cursor.fetchone()
    conn.close()
    view = BalanceView(target, data)
    await interaction.response.send_message(embed=view.get_net_worth_embed(), view=view)

@bot.tree.command(name="daily", description="Claim your bits (Resets 12AM EST)")
async def daily(interaction: discord.Interaction):
    user_id = interaction.user.id
    est = pytz.timezone('US/Eastern')
    now_est = datetime.now(est)
    today_str = now_est.strftime('%Y-%m-%d')
    next_reset = (est.localize(datetime(now_est.year, now_est.month, now_est.day, 0, 0, 0)) + timedelta(days=1))
    
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cursor.execute("SELECT balance, last_daily_date, streak FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()

    if res and res[1] == today_str:
        embed_err = discord.Embed(title="🚫 Already Claimed", description=f"Next reset <t:{int(next_reset.timestamp())}:R>", color=0xff4b4b)
        await interaction.response.send_message(embed=embed_err)
        conn.close()
        return

    # UPDATED MATH: 1080 * streak + 100,000
    base_reward = 100000
    streak = (res[2] if res else 0) + 1
    streak_bonus = 1080 * streak
    total_reward = base_reward + streak_bonus
    
    cursor.execute("UPDATE users SET balance = balance + ?, last_daily_date = ?, streak = ? WHERE user_id = ?", (total_reward, today_str, streak, user_id))
    conn.commit()
    conn.close()

    # The Grid Embed layout
    embed = discord.Embed(title=f"💳 {interaction.user.display_name}'s Daily Coins", color=0x2b2d31)
    embed.description = f"**{total_reward:,}** was placed in your wallet!"
    
    embed.add_field(name="Base", value=f"✧ {base_reward:,}", inline=True)
    embed.add_field(name="Streak Bonus", value=f"✧ {streak_bonus:,}", inline=True)
    embed.add_field(name="Donor Bonus", value="✧ 0", inline=True)
    
    embed.add_field(name="Next Daily", value="Today", inline=True)
    embed.add_field(name="Next Item Reward", value="Daily Box in 1 day", inline=True)
    embed.add_field(name="Streak", value=f"{streak}", inline=True)

    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    bot.run(os.environ.get("DISCORD_TOKEN"))
