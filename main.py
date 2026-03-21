import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
import pytz
from datetime import datetime, timedelta

# --- 1. LOOT TABLES ---
LOOT_TABLES = {
    "Player Pack": {
        "currency": 50000,
        "items": [
            {"name": "Basic Box", "amount": 1}
        ]
    }
}

# --- 2. DATABASE ---
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

# --- 3. AUTOCOMPLETE ---
async def item_autocomplete(interaction: discord.Interaction, current: str):
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT item_name FROM inventory
        WHERE user_id = ? AND quantity > 0
    """, (interaction.user.id,))

    items = cursor.fetchall()
    conn.close()

    return [
        app_commands.Choice(name=name, value=name)
        for (name,) in items
        if current.lower() in name.lower()
    ][:25]

# --- 4. BOT SETUP ---
class GhostNet(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=commands.when_mentioned_or("net ", "net"),
            intents=intents,
            case_insensitive=True,
            help_command=None  # IMPORTANT
        )

    async def setup_hook(self):
        init_db()
        await self.tree.sync()
        print("GHOSTNET: Commands synced")

bot = GhostNet()

# --- 5. DAILY ---
@bot.hybrid_command(name="daily")
async def daily(ctx: commands.Context):
    await ctx.defer(thinking=True)

    user_id = ctx.author.id
    est = pytz.timezone('US/Eastern')
    now_est = datetime.now(est)
    today_str = now_est.strftime('%Y-%m-%d')

    next_reset = int((now_est.replace(hour=0, minute=0, second=0) + timedelta(days=1)).timestamp())

    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cursor.execute("SELECT last_daily_date, streak FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()

    if res and res[0] == today_str:
        conn.close()
        return await ctx.send(f"🚫 Already claimed! Next reset <t:{next_reset}:R>")

    streak = (res[1] if res else 0) + 1
    reward = 100000 + (1080 * streak)

    cursor.execute("""
        UPDATE users
        SET balance = balance + ?, last_daily_date = ?, streak = ?
        WHERE user_id = ?
    """, (reward, today_str, streak, user_id))

    conn.commit()
    conn.close()

    embed = discord.Embed(title="💳 Daily", color=0xffa500)
    embed.add_field(name="Reward", value=f"{reward:,} bits")
    embed.add_field(name="Streak", value=str(streak))

    await ctx.send(embed=embed)

# --- 6. BALANCE ---
@bot.hybrid_command(name="balance", aliases=["bal"])
async def balance(ctx: commands.Context):
    await ctx.defer(thinking=True)

    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()

    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (ctx.author.id,))
    res = cursor.fetchone()
    conn.close()

    bal = res[0] if res else 0
    await ctx.send(f"🪙 {ctx.author.display_name}: {bal:,} bits")

# --- 7. INVENTORY ---
@bot.hybrid_command(name="inventory", aliases=["inv"])
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

    embed = discord.Embed(title="🎒 Inventory", color=0xffa500)

    if not items:
        embed.description = "Empty."
    else:
        embed.description = "\n".join(
            [f"**{name}** x{qty}" for name, qty in items]
        )

    await ctx.send(embed=embed)

# --- 8. USE ---
@bot.hybrid_command(name="use")
@app_commands.autocomplete(item=item_autocomplete)
async def use(ctx: commands.Context, item: str):
    await ctx.defer(thinking=True)

    user_id = ctx.author.id
    item_title = item.strip().title()

    if item_title not in LOOT_TABLES:
        return await ctx.send("❓ Item does not exist.")

    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT quantity FROM inventory
        WHERE user_id = ? AND item_name = ?
    """, (user_id, item_title))

    res = cursor.fetchone()

    if not res or res[0] <= 0:
        conn.close()
        return await ctx.send("❌ You don't have that item.")

    table = LOOT_TABLES[item_title]

    cursor.execute("""
        UPDATE inventory
        SET quantity = quantity - 1
        WHERE user_id = ? AND item_name = ?
    """, (user_id, item_title))

    rewards = []

    if "currency" in table:
        cursor.execute("""
            UPDATE users SET balance = balance + ?
            WHERE user_id = ?
        """, (table["currency"], user_id))
        rewards.append(f"{table['currency']:,} bits")

    for r in table.get("items", []):
        cursor.execute("""
            INSERT INTO inventory (user_id, item_name, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, item_name)
            DO UPDATE SET quantity = quantity + ?
        """, (user_id, r["name"], r["amount"], r["amount"]))
        rewards.append(f"{r['amount']}x {r['name']}")

    conn.commit()
    conn.close()

    await ctx.send(f"📦 Opened {item_title}:\n" + "\n".join(rewards))

# --- 9. HELP DROPDOWN ---
class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="All", emoji="📖"),
            discord.SelectOption(label="Currency", emoji="💰"),
            discord.SelectOption(label="Config", emoji="⚙️"),
        ]
        super().__init__(placeholder="Choose category", options=options)

    async def callback(self, interaction: discord.Interaction):
        cat = self.values[0]

        if cat == "All":
            text = "/daily\n/balance\n/inventory\n/use\n/help"
        elif cat == "Currency":
            text = "/daily\n/balance"
        else:
            text = "/help"

        embed = discord.Embed(title=cat, description=text, color=0x00bfff)
        await interaction.response.edit_message(embed=embed)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpSelect())

@bot.hybrid_command(name="help")
async def help_command(ctx: commands.Context):
    await ctx.defer(thinking=True)

    embed = discord.Embed(
        title="📖 GhostNet Help",
        description="Select a category below",
        color=0x00bfff
    )

    await ctx.send(embed=embed, view=HelpView())

# --- START ---
if __name__ == "__main__":
    TOKEN = os.environ.get("DISCORD_TOKEN")
    if not TOKEN:
        raise ValueError("DISCORD_TOKEN not set")

    bot.run(TOKEN)
