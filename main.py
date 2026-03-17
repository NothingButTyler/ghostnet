import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
import pytz
import random
from datetime import datetime, timedelta

# --- 1. DATABASE ---

def init_db():
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 100,
            last_daily_date TEXT,
            streak INTEGER DEFAULT 0,
            has_joined INTEGER DEFAULT 0
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


# --- 2. BOT SETUP ---

class GhostNet(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=["net ", "Net ", "NET "],
            intents=intents,
            case_insensitive=True
        )

    async def setup_hook(self):
        init_db()

        # SAFE COMMAND SYNC (won’t crash loop)
        try:
            await self.tree.sync()
            print("GHOSTNET: Commands synced")
        except Exception as e:
            print(f"Command sync failed: {e}")


bot = GhostNet()


# --- 3. WELCOME SYSTEM ---

async def send_welcome_dm(user: discord.User):
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR REPLACE INTO inventory (user_id, item_name, quantity) VALUES (?, ?, ?)",
        (user.id, "Player Pack", 1)
    )

    conn.commit()
    conn.close()

    embed = discord.Embed(
        title="Welcome to GHOSTNET 🪙",
        description="You received a **Player Pack** 📦! Use `net use Player Pack`.",
        color=0xffa500
    )

    try:
        await user.send(embed=embed)
    except:
        pass


@bot.event
async def on_app_command_completion(interaction: discord.Interaction, command: app_commands.Command):
    user_id = interaction.user.id

    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()

    cursor.execute("SELECT has_joined FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if not row or row[0] == 0:
        cursor.execute(
            "INSERT OR REPLACE INTO users (user_id, has_joined) VALUES (?, 1)",
            (user_id,)
        )
        conn.commit()
        await send_welcome_dm(interaction.user)

    conn.close()


# --- 4. COMMANDS ---

@bot.hybrid_command(name="daily", description="Claim your bits (Resets 12AM EST)")
async def daily(ctx: commands.Context):
    await ctx.defer()

    user_id = ctx.author.id
    est = pytz.timezone('US/Eastern')
    now_est = datetime.now(est)
    today_str = now_est.strftime('%Y-%m-%d')

    next_reset_dt = (
        est.localize(datetime(now_est.year, now_est.month, now_est.day))
        + timedelta(days=1)
    )
    reset_ts = int(next_reset_dt.timestamp())

    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cursor.execute(
        "SELECT balance, last_daily_date, streak FROM users WHERE user_id = ?",
        (user_id,)
    )
    res = cursor.fetchone()

    if res and res[1] == today_str:
        conn.close()
        return await ctx.send(f"🚫 Already claimed! Next reset <t:{reset_ts}:R>")

    streak = (res[2] if res else 0) + 1
    reward = 100000 + (1080 * streak)

    cursor.execute("""
        UPDATE users
        SET balance = balance + ?, last_daily_date = ?, streak = ?
        WHERE user_id = ?
    """, (reward, today_str, streak, user_id))

    conn.commit()
    conn.close()

    embed = discord.Embed(
        title=f"💳 {ctx.author.display_name}'s Daily",
        color=0xffa500
    )

    embed.add_field(name="Reward", value=f"{reward:,} bits")
    embed.add_field(name="Next Daily", value=f"<t:{reset_ts}:R>")
    embed.add_field(name="Streak", value=str(streak))

    await ctx.send(embed=embed)


@bot.hybrid_command(name="balance", description="Check your bits")
async def balance(ctx: commands.Context):
    await ctx.defer()

    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()

    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (ctx.author.id,))
    res = cursor.fetchone()

    conn.close()

    bal = res[0] if res else 0
    await ctx.send(f"🪙 {ctx.author.display_name}, you have {bal:,} bits.")


@bot.hybrid_command(name="inventory", description="View items")
async def inventory(ctx: commands.Context):
    await ctx.defer()

    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT item_name, quantity
        FROM inventory
        WHERE user_id = ? AND quantity > 0
    """, (ctx.author.id,))

    items = cursor.fetchall()
    conn.close()

    embed = discord.Embed(
        title=f"🎒 {ctx.author.display_name}'s Inventory",
        color=0xffa500
    )

    if not items:
        embed.description = "Your backpack is empty."
    else:
        embed.description = "\n".join(
            [f"**{name}** — x{qty}" for name, qty in items]
        )

    await ctx.send(embed=embed)


@bot.hybrid_command(name="use", description="Use an item")
async def use(ctx: commands.Context, item: str):
    await ctx.defer()

    user_id = ctx.author.id
    item_title = item.title()

    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT quantity
        FROM inventory
        WHERE user_id = ? AND item_name = ?
    """, (user_id, item_title))

    res = cursor.fetchone()

    if not res or res[0] <= 0:
        conn.close()
        return await ctx.send(f"❌ You don't have a {item_title}!")

    if item_title == "Player Pack":
        creatures = [
            "Neon Tetra Ghost",
            "Glitch Guppy",
            "Data Drift Eel"
        ]

        caught = random.choice(creatures)

        cursor.execute("""
            UPDATE inventory
            SET quantity = quantity - 1
            WHERE user_id = ? AND item_name = ?
        """, (user_id, "Player Pack"))

        cursor.execute("""
            UPDATE users
            SET balance = balance + 50000
            WHERE user_id = ?
        """, (user_id,))

        cursor.execute("""
            INSERT INTO inventory (user_id, item_name, quantity)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, item_name)
            DO UPDATE SET quantity = quantity + 1
        """, (user_id, caught))

        await ctx.send(
            f"📦 Player Pack Opened!\n"
            f"🪙 50,000 Bits\n"
            f"🐟 1x {caught}"
        )

    else:
        await ctx.send(f"❓ {item_title} cannot be used yet.")

    conn.commit()
    conn.close()


# --- 5. START BOT ---

if __name__ == "__main__":
    TOKEN = os.environ.get("DISCORD_TOKEN")

    if not TOKEN:
        raise ValueError("DISCORD_TOKEN not set")

    bot.run(TOKEN)
