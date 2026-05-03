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

# -------------------------
# 🔧 HYBRID HELPERS (ADD THIS)
# -------------------------
def is_interaction(ctx):
    return ctx.interaction is not None

async def respond(ctx, message, ephemeral=False):
    if is_interaction(ctx):
        if not ctx.interaction.response.is_done():
            await ctx.interaction.response.send_message(message, ephemeral=ephemeral)
        else:
            await ctx.followup.send(message, ephemeral=ephemeral)
    else:
        await ctx.send(message)
# -------------------------
# 💰 COMMANDS
# -------------------------

# -------------------------
# 💰 DAILY
# -------------------------
@bot.hybrid_command(name="daily", description="Claim your daily reward")
async def daily(ctx: commands.Context):
    await ctx.defer(thinking=True)

    user_id = ctx.author.id
    est = pytz.timezone('US/Eastern')
    now = datetime.now(est)
    today = now.strftime('%Y-%m-%d')

    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cursor.execute("SELECT last_daily_date, streak FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()

    if res and res[0] == today:
        conn.close()
        return await ctx.followup.send("🚫 Already claimed today.")

    streak = (res[1] if res else 0) + 1
    reward = 100000 + (1080 * streak)

    cursor.execute("""
        UPDATE users SET balance = balance + ?, last_daily_date = ?, streak = ?
        WHERE user_id = ?
    """, (reward, today, streak, user_id))

    conn.commit()
    conn.close()

    await ctx.followup.send(f"💰 {reward:,} bits | streak {streak}")


# -------------------------
# 💳 BALANCE
# -------------------------
@bot.hybrid_command(name="balance", description="Check your balance")
async def balance(ctx: commands.Context):
    await ctx.defer(thinking=True)

    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()

    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (ctx.author.id,))
    res = cursor.fetchone()

    conn.close()

    bal = res[0] if res else 0
    await ctx.followup.send(f"🪙 {bal:,} bits")


# -------------------------
# 🎒 INVENTORY
# -------------------------
@bot.hybrid_command(name="inventory", description="View your inventory")
async def inventory(ctx: commands.Context):
    await ctx.defer(thinking=True)

    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT item_name, quantity FROM inventory
        WHERE user_id = ? AND quantity > 0
    """, (ctx.author.id,))

    items = cursor.fetchall()
    conn.close()

    if not items:
        return await ctx.followup.send("🎒 Inventory is empty.")

    text = "\n".join([f"{name} x{qty}" for name, qty in items])
    await ctx.followup.send(f"🎒 Inventory:\n{text}")


# -------------------------
# 📦 USE ITEM
# -------------------------
@bot.hybrid_command(name="use", description="Use an item")
@app_commands.describe(item="Item name")
async def use(ctx: commands.Context, item: str):
    await ctx.defer(thinking=True)

    user_id = ctx.author.id
    item = item.title()

    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT quantity FROM inventory
        WHERE user_id = ? AND item_name = ?
    """, (user_id, item))

    res = cursor.fetchone()

    if not res or res[0] <= 0:
        conn.close()
        return await ctx.followup.send("❌ You don’t have that item.")

    reward = 50000

    cursor.execute("""
        UPDATE inventory SET quantity = quantity - 1
        WHERE user_id = ? AND item_name = ?
    """, (user_id, item))

    cursor.execute("""
        UPDATE users SET balance = balance + ?
        WHERE user_id = ?
    """, (reward, user_id))

    conn.commit()
    conn.close()

    await ctx.followup.send(f"📦 Used {item} → +{reward:,} bits")


# -------------------------
# 🔐 ADMIN GIVE (PREFIX ONLY)
# -------------------------
@bot.command(name="give")
async def give(ctx, member: discord.Member, amount: int):
    if ctx.author.id not in ADMIN_IDS:
        return await ctx.send("❌ Not allowed.")

    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (ctx.author.id,))
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (member.id,))

    # 💥 BIG TRANSFER CONFIRM (still kept)
    if amount >= BIG_TRANSFER:
        confirm_msg = await ctx.send(
            f"⚠️ Confirm {amount:,} → {member.mention}\nType `yes`"
        )

        def check(m):
            return m.author == ctx.author and m.content.lower() == "yes"

        try:
            await bot.wait_for("message", timeout=15, check=check)
        except:
            await confirm_msg.edit(content="❌ Cancelled.")
            conn.close()
            return

    # 💰 TRANSFER (no limits now)
    cursor.execute(
        "UPDATE users SET balance = balance - ? WHERE user_id = ?",
        (amount, ctx.author.id)
    )
    cursor.execute(
        "UPDATE users SET balance = balance + ? WHERE user_id = ?",
        (amount, member.id)
    )

    conn.commit()
    conn.close()

    await ctx.message.add_reaction("✅")

# -------------------------
# ❓ HELP (ADMIN HIDDEN)
# -------------------------
@bot.hybrid_command(name="help", description="View commands")
async def help_command(ctx: commands.Context):
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
        return await ctx.followup.send(base_text)

    # admin sees extra, but ONLY they see it
    await ctx.followup.send(base_text + admin_text, ephemeral=True)
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
