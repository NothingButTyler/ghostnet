import discord
from discord.ext import commands
import os
import asyncio
import random
import time
from flask import Flask
from threading import Thread

# --- 1. WEB SERVER (Anti-Idle) ---
app = Flask('')
@app.route('/')
def home(): return "GHOSTNET: ONLINE"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. BOT SETUP ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')

# Configuration for targets
ISAAC_ID = 1444073106384621631
fake_isaacs = [] 
infected_users = {} 
global_prank = False 

# --- 3. HELPER LOGIC ---
def is_treated_as_isaac(ctx_or_msg):
    """Checks if the user is a target (Isaac, Infected, or Fake). Admins are immune."""
    author = ctx_or_msg.author
    if author.guild_permissions.administrator: return False
    if global_prank: return True
    is_infected = author.id in infected_users and time.time() < infected_users[author.id]
    return author.id == ISAAC_ID or author.id in fake_isaacs or is_infected

# --- 4. COMMANDS ---

@bot.command(name="hack")
async def hack(ctx, member: discord.Member = None):
    """Restored Hack Command: Simulates a terminal breach on a target."""
    # If the target (Isaac) tries to hack someone, the bot blocks them
    if is_treated_as_isaac(ctx):
        return await ctx.reply("`[ERROR]: UNAUTHORIZED ACCESS. TERMINAL LOCKED.`")

    # Default to hacking the author if no member is mentioned
    target = member if member else ctx.author
    
    # 1. Start the simulation
    msg = await ctx.send(f"🛰️ `[CONNECTING TO {target.name.upper()}...]`")
    await asyncio.sleep(1.5)

    # 2. Visual "Step-by-Step" Hacking Progress
    steps = [
        "🔓 Bypassing 2FA...",
        "💾 Downloading local data...",
        "📂 Indexing #private-chats...",
        "🛰️ Mirroring screen packets...",
        "☣️ Injecting Ghost-Ware..."
    ]

    for step in steps:
        await msg.edit(content=f"⚙️ `{step}`")
        await asyncio.sleep(random.uniform(0.5, 1.5)) # Random delay for realism

    # 3. Final Result Embed
    embed = discord.Embed(title="✅ BREACH SUCCESSFUL", color=0x00ff00)
    embed.description = f"```diff\n+ Target: {target.name}\n+ IP: {random.randint(100,255)}.{random.randint(0,255)}.1.1\n+ Status: CONTROLLED\n```"
    embed.add_field(name="🛰️ TERMINAL", value=f"Access granted to {target.mention}'s logs.")
    embed.set_footer(text="GHOSTNET Intelligence Protocol v5.1")
    
    await msg.edit(content=None, embed=embed)

@bot.command(name="help")
async def help_cmd(ctx):
    """Custom Terminal UI for Help."""
    if is_treated_as_isaac(ctx):
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="🛠️ CONFIG", value="`ERROR: NEURAL LINK CORRUPTED`", inline=False)
        return await ctx.reply(embed=embed)

    if ctx.author.guild_permissions.administrator:
        embed = discord.Embed(title="🛰️ GHOSTNET STAFF TERMINAL", color=0x00ff00)
        embed.add_field(name="💀 BREACH TOOLS", 
                        value="`!hack @user` - Simulate breach\n`!infect @user` - 5min haunt", inline=False)
        embed.add_field(name="🛡️ SECURITY", 
                        value="`!lockdown` - Silence chat\n`!unlock` - Restore traffic", inline=False)
        await ctx.reply(content="🛡️ **Terminal Access Granted.**", embed=embed)
    else:
        # Standard Public Help
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="💀 COMMANDS", value="`!hack @user` - Attempt breach", inline=False)
        await ctx.reply(embed=embed)

# --- 5. SYSTEM COMMANDS (Admin Only) ---

@bot.command(name="shutdown")
@commands.has_permissions(administrator=True)
async def shutdown(ctx):
    """Terminates the bot process."""
    await ctx.reply("🛑 **OFFLINE.**")
    await bot.close()

@bot.command(name="infect")
@commands.has_permissions(administrator=True)
async def infect(ctx, member: discord.Member = None):
    """Starts the 5-minute reaction haunt on a user."""
    if not member: return await ctx.reply("❌ Specify target.")
    infected_users[member.id] = time.time() + 300
    await ctx.send(f"☣️ **{member.mention} flagged for monitoring.**")

# --- 6. EVENTS ---

@bot.event
async def on_message(message):
    # Prevention: Don't respond to own messages
    if message.author == bot.user:
        return

    # Infection Logic: Auto-react to every message sent by infected targets
    if message.author.id in infected_users:
        if time.time() < infected_users[message.author.id]:
            try: await message.add_reaction("☣️")
            except: pass
        else:
            del infected_users[message.author.id]

    # Required for commands to process
    await bot.process_commands(message)

# --- 7. RUN ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
