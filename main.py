import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
import pytz
from datetime import datetime, timedelta

# --- 1. LOOT TABLES (NO RANDOM) ---
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
    case_insensitive=True
)

    async def setup_hook(self):
        init_db()
        try:
            await self.tree.sync()
            print("GHOSTNET: Commands synced")
        except Exception as e:
            print(f"Sync failed: {e}")

bot = GhostNet()

# --- 5. WELCOME SYSTEM ---
async def send_welcome_dm(user: discord.User):
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO inventory (user_id, item_name, quantity)
        VALUES (?, ?, ?)
    """, (user.id, "Player Pack", 1))

    conn.commit()
    conn.close()

    embed = discord.Embed(
        title="Welcome to GHOSTNET 🪙",
        description="You received a **Player Pack** 📦! Use `/use` to open it.",
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
        cursor.execute("""
            INSERT OR REPLACE INTO users (user_id, has_joined)
            VALUES (?, 1)
        """, (user_id,))
        conn.commit()
        await send_welcome_dm(interaction.user)

    conn.close()

# --- 6. COMMANDS ---

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
    cursor.execute("""
        SELECT balance, last_daily_date, streak
        FROM users WHERE user_id = ?
    """, (user_id,))
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

@bot.hybrid_command(
    name="balance",
    aliases=["bal"],
    description="Check your bits"
)
    await ctx.defer()

    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()

    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (ctx.author.id,))
    res = cursor.fetchone()

    conn.close()

    bal = res[0] if res else 0
    await ctx.send(f"🪙 {ctx.author.display_name}, you have {bal:,} bits.")

@bot.hybrid_command(
    name="inventory",
    aliases=["inv"],
    description="View your items"
)
async def inventory(ctx: commands.Context):2
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
@app_commands.autocomplete(item=item_autocomplete)
async def use(ctx: commands.Context, item: str):
    await ctx.defer(thinking=True)

    try:
        user_id = ctx.author.id
        item_title = item.strip().title()

        conn = sqlite3.connect("economy.db")
        cursor = conn.cursor()

        # ❓ Check if item exists FIRST
        if item_title not in LOOT_TABLES:
            conn.close()

            embed = discord.Embed(
                title="❓ Unknown Item",
                description=f"**{item_title}** does not exist.",
                color=0xffa500
            )

            return await ctx.send(embed=embed)

        # Check inventory
        cursor.execute("""
            SELECT quantity
            FROM inventory
            WHERE user_id = ? AND item_name = ?
        """, (user_id, item_title))

        res = cursor.fetchone()

        # ❌ User doesn't have it
        if not res or res[0] <= 0:
            conn.close()

            embed = discord.Embed(
                title="❌ Item Not Found",
                description=f"You don’t have **{item_title}**.",
                color=0xff0000
            )

            return await ctx.send(embed=embed)

        # 📦 Use item
        table = LOOT_TABLES[item_title]

        cursor.execute("""
            UPDATE inventory
            SET quantity = quantity - 1
            WHERE user_id = ? AND item_name = ?
        """, (user_id, item_title))

        rewards_text = []

        if "currency" in table:
            cursor.execute("""
                UPDATE users
                SET balance = balance + ?
                WHERE user_id = ?
            """, (table["currency"], user_id))

            rewards_text.append(f"🪙 {table['currency']:,} Bits")

        for reward in table.get("items", []):
            cursor.execute("""
                INSERT INTO inventory (user_id, item_name, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, item_name)
                DO UPDATE SET quantity = quantity + ?
            """, (user_id, reward["name"], reward["amount"], reward["amount"]))

            rewards_text.append(f"📦 {reward['amount']}x {reward['name']}")

        conn.commit()
        conn.close()

        embed = discord.Embed(
            title=f"📦 {item_title} Opened!",
            description="\n".join(rewards_text),
            color=0xffa500
        )

        return await ctx.send(embed=embed)

    except Exception as e:
        print(f"ERROR in /use: {e}")

        embed = discord.Embed(
            title="⚠️ Error",
            description="Something went wrong.",
            color=0xff0000
        )

        return await ctx.send(embed=embed)

class HelpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="All", description="Show all commands", emoji="📖"),
            discord.SelectOption(label="Currency", description="Money commands", emoji="💰"),
            discord.SelectOption(label="Config", description="Bot settings", emoji="⚙️"),
        ]

        super().__init__(placeholder="Choose a category...", options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]

        if category == "All":
            embed = discord.Embed(title="📖 All Commands", color=0x00bfff)
            embed.description = (
                "`/daily`\n"
                "`/balance`\n"
                "`/inventory`\n"
                "`/use`\n"
                "`/help`"
            )

        elif category == "Currency":
            embed = discord.Embed(title="💰 Currency Commands", color=0x00bfff)
            embed.description = (
                "`/daily` — Claim daily bits\n"
                "`/balance` — Check balance"
            )

        elif category == "Config":
            embed = discord.Embed(title="⚙️ Config Commands", color=0x00bfff)
            embed.description = (
                "`/help` — Show help menu\n"
                # add more config commands here later
            )

        await interaction.response.edit_message(embed=embed)


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpSelect())


@bot.hybrid_command(name="help", description="View all commands")
async def help_command(ctx: commands.Context):
    await ctx.defer(thinking=True)

    embed = discord.Embed(
        title="📖 GhostNet Help",
        description="Select a category below 👇",
        color=0x00bfff
    )

    await ctx.send(embed=embed, view=HelpView())

# --- 7. START BOT ---
if __name__ == "__main__":
    TOKEN = os.environ.get("DISCORD_TOKEN")

    if not TOKEN:
        raise ValueError("DISCORD_TOKEN not set")

    bot.run(TOKEN)
