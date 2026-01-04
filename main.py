import discord
from discord.ext import commands
import os, asyncio, random, time, uuid
from flask import Flask
from threading import Thread

# --- 1. WEB SERVER (Render Port Binding) ---
app = Flask('')
@app.route('/')
def home(): return f"GHOSTNET ONLINE | SESSION: {SESSION_ID}"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. BOT SETUP ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')

SESSION_ID = str(uuid.uuid4())[:8]
ISAAC_ID = 1444073106384621631
infected_users = {} 

# Storage for Welcome Config (In a real bot, use a Database)
welcome_config = {
    "channel_id": None,
    "message": "Welcome to the terminal, {user}. Connection established."
}

def is_treated_as_isaac(ctx_or_msg):
    author = ctx_or_msg.author
    if author.guild_permissions.administrator: return False
    is_infected = author.id in infected_users and time.time() < infected_users[author.id]
    return author.id == ISAAC_ID or is_infected

# --- 3. WELCOME COMMANDS ---

@bot.command(name="welcome-setup")
@commands.has_permissions(administrator=True)
async def welcome_setup(ctx, channel: discord.TextChannel):
    """Sets the channel where welcome messages are sent."""
    welcome_config["channel_id"] = channel.id
    await ctx.send(f"✅ **WELCOME PROTOCOL:** Destination set to {channel.mention}")

@bot.command(name="welcome-edit")
@commands.has_permissions(administrator=True)
async def welcome_edit(ctx, *, new_message: str):
    """Updates the welcome text. Use {user} to mention the member."""
    welcome_config["message"] = new_message
    await ctx.send(f"📝 **PROTOCOL UPDATED:** New template stored.")

@bot.command(name="welcome-test")
@commands.has_permissions(administrator=True)
async def welcome_test(ctx):
    """Simulates a join event to test the current configuration."""
    if not welcome_config["channel_id"]:
        return await ctx.send("❌ **ERROR:** Run `!welcome-setup #channel` first.")
    
    channel = bot.get_channel(welcome_config["channel_id"])
    msg = welcome_config["message"].replace("{user}", ctx.author.mention)
    
    embed = discord.Embed(title="🛰️ INBOUND CONNECTION TEST", description=msg, color=0x00ff00)
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    await channel.send(embed=embed)
    await ctx.send("📡 **TEST PACKET SENT.**")

# --- 4. STAFF & SECURITY ---

@bot.command(name="help")
async def help_cmd(ctx):
    if is_treated_as_isaac(ctx): return
    
    embed = discord.Embed(title="🛰️ GHOSTNET STAFF TERMINAL", color=0x00ff00)
    embed.add_field(name="👋 WELCOME", value="`!welcome-setup` | `!welcome-edit` | `!welcome-test`", inline=False)
    embed.add_field(name="💀 PRANK", value="`!hack` | `!spoof` | `!system-logs`", inline=False)
    embed.add_field(name="🛡️ SECURITY", value="`!lockdown` | `!hard-reset` | `!infect`", inline=False)
    embed.set_footer(text=f"SESSION: {SESSION_ID}")
    await ctx.reply(embed=embed)

@bot.command(name="hard-reset")
@commands.has_permissions(administrator=True)
async def hard_reset(ctx):
    await ctx.send(f"🚨 **REBOOTING SESSION `{SESSION_ID}`...**")
    os._exit(0)

# --- 5. EVENTS ---

@bot.event
async def on_member_join(member):
    """Automated Welcome Event."""
    if welcome_config["channel_id"]:
        channel = bot.get_channel(welcome_config["channel_id"])
        if channel:
            msg = welcome_config["message"].replace("{user}", member.mention)
            embed = discord.Embed(title="🛰️ NEW CONNECTION DETECTED", description=msg, color=0x5865f2)
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    # Reaction haunting logic...
    if message.author.id in infected_users:
        if time.time() < infected_users[message.author.id]:
            try: await message.add_reaction("☣️")
            except: pass
    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
