import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
from threading import Thread
from flask import Flask

# --- 1. WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "GHOSTNET CORE: ONLINE"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- 2. DATABASE ---
def init_db():
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    # Added 'has_joined' column to track new players
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

# --- 3. THE NEW PLAYER MESSAGE ---
async def send_welcome_dm(user: discord.User):
    embed = discord.Embed(
        title="Welcome to **GHOSTNET** 🪙",
        description=(
            "From fishing unique creatures to collecting hundreds of unique items, "
            "there are no limits to how you can play with your friends.\n\n"
            "You can get started by using `/use` and selecting your brand new "
            "**player pack** 📦 we just gifted you.\n\n"
            "Commands can be ran in DMs with me, or anywhere this bot is added in other servers!\n\n"
            "After that, check out our currency commands and start exploring!"
        ),
        color=0x2b2d31
    )
    # Using your generated pixel box image for the thumbnail
    # Replace the URL below with your actual hosted image link
    embed.set_thumbnail(url="https://i.imgur.com/YOUR_IMAGE_HERE.png")
    
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Commands List", url="https://discord.com", style=discord.ButtonStyle.link))
    view.add_item(discord.ui.Button(label="Community Server", url="https://discord.com", style=discord.ButtonStyle.link))
    
    try:
        await user.send(embed=embed, view=view)
    except discord.Forbidden:
        # DM failed (user has DMs off)
        pass

# --- 4. BOT CORE ---
class GhostNet(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        init_db()
        Thread(target=run_web, daemon=True).start()
        await self.tree.sync()

bot = GhostNet()

# --- 5. THE TRIGGER (New Player Check) ---
@bot.event
async def on_app_command_completion(interaction: discord.Interaction, command: app_commands.Command):
    user_id = interaction.user.id
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    
    # Check if the user is in DB and if they've received the message
    cursor.execute("SELECT has_joined FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    # If they are not in the DB or has_joined is 0
    if not row or row[0] == 0:
        # Register user if they don't exist, and mark as joined
        cursor.execute("INSERT OR REPLACE INTO users (user_id, has_joined) VALUES (?, 1)", (user_id,))
        conn.commit()
        # Send the DM
        await send_welcome_dm(interaction.user)
        
    conn.close()

# Example command to test balance
@bot.tree.command(name="balance", description="Check your wallet")
async def balance(interaction: discord.Interaction):
    await interaction.response.send_message("Checking balance...")

if __name__ == "__main__":
    bot.run(os.environ.get("DISCORD_TOKEN"))
