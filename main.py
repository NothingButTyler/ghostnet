import discord
from discord.ext import commands
import os
import asyncio
import random
import time
from flask import Flask
from threading import Thread

# --- 1. WEB SERVER (Anti-Idle) ---
# This keeps the bot alive on 24/7 hosting platforms like Replit
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
intents = discord.Intents.all() # Granting all permissions for reaction and member tracking
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help') # Removing default help to use our custom Terminal UI

# Database-lite: Storing target IDs and infection status in memory
ISAAC_ID = 1444073106384621631
fake_isaacs = [] 
infected_users = {} # Format: {user_id: expiry_timestamp}
global_prank = False 

# --- 3. HELPER LOGIC ---
def is_treated_as_isaac(ctx_or_msg):
    """
    Core logic to determine if a user should be blocked/pranked.
    Staff (Administrators) are always immune.
    """
    author = ctx_or_msg.author
    if author.guild_permissions.administrator: return False
    if global_prank: return True
    
    # Check if user is currently infected by !infect
    is_infected = author.id in infected_users and time.time() < infected_users[author.id]
    
    return author.id == ISAAC_ID or author.id in fake_isaacs or is_infected

# --- 4. COMMANDS ---

@bot.command(name="help")
async def help_cmd(ctx):
    """Custom help menu that changes based on user permissions."""
    if is_treated_as_isaac(ctx):
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="🛠️ CONFIG", value="`ERROR: NEURAL LINK CORRUPTED`", inline=False)
        return await ctx.reply(embed=embed)

    if ctx.author.guild_permissions.administrator:
        embed = discord.Embed(title="🛰️ GHOSTNET STAFF TERMINAL", color=0x00ff00)
        embed.add_field(name="☣️ BIOWARE", 
                        value="`!infect @user`\n`!cure @user`", inline=False)
        embed.add_field(name="🛡️ SECURITY", 
                        value="`!lockdown`\n`!unlock`\n`!system-logs @user`", inline=False)
        embed.add_field(name="🛠️ UTILITY", 
                        value="`!terminal-clear [num]`\n`!ping`\n`!shutdown` - Kill bot process", inline=False)
        await ctx.reply(content="🛡️ **Terminal Access Granted.**", embed=embed)
    else:
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="💀 COMMANDS", value="`!hack @user`\n`!ping`", inline=False)
        await ctx.reply(embed=embed)

@bot.command(name="shutdown")
@commands.has_permissions(administrator=True)
async def shutdown(ctx):
    """Safe logout to prevent 'Zombie' bot instances."""
    await ctx.reply("🛑 **SHUTTING DOWN GHOSTNET...** (Closing terminal session)")
    await bot.close()

@bot.command(name="infect")
@commands.has_permissions(administrator=True)
async def infect(ctx, member: discord.Member = None):
    """Infects a user, causing the bot to react to all their messages for 5 mins."""
    if is_treated_as_isaac(ctx): return
    if not member: return await ctx.reply("❌ Specify a host to infect.")
    
    infected_users[member.id] = time.time() + 300 # Current time + 300 seconds
    await ctx.send(f"☣️ **{member.mention} has been infected.**")

@bot.command(name="cure")
@commands.has_permissions(administrator=True)
async def cure(ctx, member: discord.Member = None):
    """Removes the infection status and restores normal bot interaction."""
    if is_treated_as_isaac(ctx): return
    if member and member.id in infected_users:
        del infected_users[member.id]
        await ctx.send(f"💊 **Infection cleared for {member.mention}.**")
        try: await member.send("🛰️ **GHOSTNET:** Connection stabilized.")
        except: pass

@bot.command(name="lockdown")
@commands.has_permissions(administrator=True)
async def lockdown(ctx):
    """Mutes the channel for @everyone for 30 seconds."""
    if is_treated_as_isaac(ctx): return
    msg = await ctx.send("`[!] WARNING: PACKET OVERLOAD`")
    await asyncio.sleep(1)
    
    # Overriding channel permissions
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await msg.edit(content="🚨 **LOCKDOWN ACTIVE.**")
    
    await asyncio.sleep(30)
    
    # Restoring channel permissions
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
    await ctx.send("🔓 **LOCKDOWN LIFTED.**")

@bot.command(name="unlock")
@commands.has_permissions(administrator=True)
async def unlock(ctx):
    """Manual override to open a channel locked by !lockdown."""
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
    await ctx.send("🔓 **MANUAL OVERRIDE SUCCESSFUL.**")

@bot.command(name="system-logs")
async def system_logs(ctx, member: discord.Member = None):
    """Generates fake surveillance logs for humans or bots."""
    if is_treated_as_isaac(ctx): return
    target = member if member else (ctx.guild.get_member(ISAAC_ID) or ctx.author)
    
    # Visual flair based on target type
    log_type = "🤖 AI DEEP-SCAN" if target.bot else "📜 SYSTEM LOGS"
    log_entry = f"[{random.randint(10,23)}:00] Data intercept on {target.name}: [OK]"
    
    embed = discord.Embed(title=log_type, description=f"```ini\n{log_entry}```", color=0x5865f2)
    await ctx.reply(embed=embed)

@bot.command()
async def ping(ctx):
    """Simple latency check. Blocks Isaac with a timeout error."""
    if is_treated_as_isaac(ctx): return await ctx.reply("`ERR_TIMEOUT`")
    await ctx.reply(f"🛰️ **LATENCY:** {round(bot.latency * 1000)}ms")

# --- 5. EVENTS ---

@bot.event
async def on_message(message):
    # CRITICAL: Prevent the bot from responding to itself (stops infinite loops)
    if message.author == bot.user:
        return

    # Infection Logic: If user is in the infection list, add the emoji
    if message.author.id in infected_users:
        if time.time() < infected_users[message.author.id]:
            try: await message.add_reaction("☣️")
            except: pass # Prevents crash if bot lacks permission to react
        else:
            # Infection has expired, remove them from the list
            del infected_users[message.author.id]

    # Required to make @bot.command() functions work alongside on_message
    await bot.process_commands(message)

# --- 6. EXECUTION ---
if __name__ == "__main__":
    keep_alive() # Starts Flask server
    bot.run(os.environ.get("DISCORD_TOKEN"))
