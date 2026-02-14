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

# --- 3. INTERACTIVE UI (Toggling Views) ---
class BalanceView(discord.ui.View):
    def __init__(self, target, data):
        super().__init__(timeout=120)
        self.target = target
        # data: (wallet/balance, bank, inventory)
        self.wallet, self.bank, self.inv = data
        self.total = self.wallet + self.bank + self.inv

    def get_net_worth_embed(self):
        # Title: User's Display Name + Net Worth | No Global Rank
        embed = discord.Embed(title=f"{self.target.display_name}'s Net Worth", color=0x2b2d31)
        embed.add_field(name="Coins", value=f"🪙 {self.wallet:,}", inline=False)
        embed.add_field(name="Inventory", value=f"🎒 {self.inv:,}", inline=False)
        embed.add_field(name="Total", value=f"💼 {self.total:,}", inline=False)
        return embed

    def get_balances_embed(self):
        # Title: User's Display Name + Balances | No Global Rank
        embed = discord.Embed(title=f"{self.target.display_name}'s Balances", color=0x2b2d31)
        desc = (
            f"🪙 {self.wallet:,}\n"
            f"🏛️ {self.bank:,} / 2,574,231"
        )
        embed.description = desc
        return embed

    @discord.ui.button(label="Balances", style=discord.ButtonStyle.secondary)
    async def balances(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.get_balances_embed(), view=self)

    @discord.ui.button(label="Net Worth", style=discord.ButtonStyle.secondary)
    async def net_worth(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.get_net_worth_embed(), view=self)

# --- 4. BOT SETUP ---
class GhostNet(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        init_db()
        Thread(target=run_web, daemon=True).start()
        await self.tree.sync()
        print(f"✅ GHOSTNET: Tree Synced. Market removed from Net Worth.")

bot = GhostNet()

@bot.tree.command(name="balance", description="Check your wallet, bank, and total net worth")
async def balance(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (target.id,))
    # Pulling synced balance/wallet data
    cursor.execute("SELECT balance, bank, inventory_val FROM users WHERE user_id = ?", (target.id,))
    data = cursor.fetchone()
    conn.close()

    view = BalanceView(target, data)
    await interaction.response.send_message(embed=view.get_net_worth_embed(), view=view)

# --- 5. THE DAILY COMMAND ---
@bot.tree.command(name="daily", description="Claim your bits (Resets 12AM EST)")
async def daily(interaction: discord.Interaction):
    user_id = interaction.user.id
    est = pytz.timezone('US/Eastern')
    now_est = datetime.now(est)
    today_str = now_est.strftime('%Y-%m-%d')
    next_reset = (est.localize(datetime(now_est.year, now_est.month, now_est.day, 0, 0, 0)) + timedelta(days=1))
    
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance, last_daily_date FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()

    if res and res[1] == today_str:
        embed = discord.Embed(title="🚫 Already Claimed", description=f"Try again <t:{int(next_reset.timestamp())}:R>", color=0xff4b4b)
        await interaction.response.send_message(embed=embed)
        conn.close()
        return

    reward = 100000
    cursor.execute("UPDATE users SET balance = balance + ?, last_daily_date = ? WHERE user_id = ?", (reward, today_str, user_id))
    conn.commit()
    conn.close()

    await interaction.response.send_message(f"✅ **{interaction.user.display_name}**, you claimed **🪙 {reward:,}** bits!")

if __name__ == "__main__":
    bot.run(os.environ.get("DISCORD_TOKEN"))
