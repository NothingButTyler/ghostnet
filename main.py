import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
import pytz
from datetime import datetime, timedelta

# --- FLASK / LOGIN ---
from flask import Flask, redirect, request
import urllib.parse
import threading
import requests

# -------------------------
# 🔐 DISCORD OAUTH CONFIG
# -------------------------
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = "https://ghostnet-0p4u.onrender.com/login-callback"

# -------------------------
#  Variables
# -------------------------
ADMIN_IDS = [711601844740292649, 1210240420047749151]
BIG_TRANSFER = 100_000_000

# -------------------------
# 🌐 FLASK APP
# -------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "GhostNet API running"

@app.route("/login")
def login():
    url = (
        "https://discord.com/api/oauth2/authorize?"
        + urllib.parse.urlencode({
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": "identify guilds"
        })
    )
    return redirect(url)

@app.route("/login-callback")
def login_callback():
    code = request.args.get("code")

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    token = requests.post(
        "https://discord.com/api/oauth2/token",
        data=data,
        headers=headers
    ).json()

    print("TOKEN RESPONSE:", token)  # 🔥 DEBUG

    access_token = token.get("access_token")

    # ❌ If OAuth failed, show error instead of crashing
    if not access_token:
        return f"OAuth failed: {token}"

    user = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    print("USER:", user)  # 🔥 DEBUG

    # redirect to dashboard
    return redirect(
        f"https://ghostnet-bot.github.io/dashboard?username={user.get('username')}&avatar={user.get('id')}/{user.get('avatar')}"
    )

# -------------------------
# 🧠 DATABASE
# -------------------------
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

# -------------------------
# 🤖 BOT
# -------------------------
class GhostNet(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or("net ", "net"),
            intents=discord.Intents.all(),
            help_command=None
        )

    async def setup_hook(self):
        init_db()
        await self.tree.sync()
        print("Bot ready")

bot = GhostNet()

@bot.hybrid_command(name="help")
async def help_command(ctx: commands.Context):
    if is_interaction(ctx):
        await ctx.defer(thinking=True)

    is_admin = ctx.author.id in ADMIN_IDS

    base_text = """
💰 Currency:
/daily
/balance

🎒 Items:
/inventory
/use
"""

    admin_text = """
🔐 Admin:
net give @user amount
"""

    if not is_admin:
        return await respond(ctx, base_text)

    await respond(ctx, base_text + admin_text, ephemeral=True)
# -------------------------
# 🚀 RUN BOTH
# -------------------------
def run_flask():
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()

    TOKEN = os.environ.get("DISCORD_TOKEN")
    bot.run(TOKEN)

# note to br3h: if any of the commands got removed, that's chatgpt's fault since we were working on the website on the chatgpt gc - tyler
    #replied to tyler:
    #just make a new chatgpt gc
