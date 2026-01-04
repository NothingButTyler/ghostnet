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

# Configuration
ISAAC_ID = 1444073106384621631
fake_isaacs = [] 
infected_users = {} # {user_id: expiry_timestamp}
global_prank = False 

# --- 3. HELPER LOGIC ---
def is_treated_as_isaac(ctx_or_msg):
    """Staff are immune. Targets (Isaac/Infected) are blocked from staff commands."""
    author = ctx_or_msg.author
    if author.guild_permissions.administrator: return False
    if global_prank: return True
    is_infected = author.id in infected_users and time.time() < infected_users[author.id]
    return author.id == ISAAC_ID or author.id in fake_isaacs or is_infected

# --- 4. COMMANDS ---

@bot.command(name="spoof")
@commands.has_permissions(administrator=True, manage_webhooks=True)
async def spoof(ctx, member: discord.Member, *, message: str):
    """Identity Thief: Uses a temporary webhook to impersonate a user."""
    if is_treated_as_isaac(ctx): return
    try:
        await ctx.message.delete() # Hide the trigger command
        
        # Create a temporary webhook for the prank
        webhook = await ctx.channel.create_webhook(name=f"Ghost-{member.display_name}")
        
        # Send message as target user
        await webhook.send(
            content=message,
            username=member.display_name,
            avatar_url=member.display_avatar.url
        )
        await webhook.delete() # Self-destruct webhook
    except discord.Forbidden:
        await ctx.send("❌ `ERROR: I need 'Manage Webhooks' permission.`")
    except Exception as e:
        await ctx.send(f"⚠️ `GHOSTNET ERR: {e}`")

@bot.command(name="help")
async def help_cmd(ctx):
    """Surveillance Terminal Help Menu."""
    if is_treated_as_isaac(ctx):
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="🛠️ CONFIG", value="`ERROR: NEURAL LINK CORRUPTED`", inline=False)
        return await ctx.reply(embed=embed)

    if ctx.author.guild_permissions.administrator:
        embed = discord.Embed(title="🛰️ GHOSTNET STAFF TERMINAL", color=0x00ff00)
        embed.add_field(name="💀 PRANK", value="`!hack @user` | `!spoof @user [msg]` | `!system-logs @user`", inline=False)
        embed.add_field(name="☣️ BIOWARE", value="`!infect @user` | `!cure @user`", inline=False)
        embed.add_field(name="🛡️ SECURITY", value="`!lockdown` | `!unlock` | `!shutdown`", inline=False)
        embed.add_field(name="🛠️ UTILITY", value="`!terminal-clear [num]` | `!ping` | `!test-prank @user`", inline=False)
        
        # Bottom status bar for background features
        embed.set_footer(text="[ONLINE] GHOST-TYPING: ACTIVE | REACTION-HAUNT: ACTIVE")
        await ctx.reply(content="🛡️ **Terminal Access Granted.**", embed=embed)
    else:
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="💀 COMMANDS", value="`!hack @user` | `!ping`", inline=False)
        await ctx.reply(embed=embed)

@bot.command(name="infect")
@commands.has_permissions(administrator=True)
async def infect(ctx, member: discord.Member = None):
    if not member: return await ctx.reply("❌ Specify target.")
    infected_users[member.id] = time.time() + 300 # 5 min haunt
    await ctx.send(f"☣️ **{member.mention} has been infected.**")

@bot.command(name="cure")
@commands.has_permissions(administrator=True)
async def cure(ctx, member: discord.Member = None):
    if member and member.id in infected_users:
        del infected_users[member.id]
        await ctx.send(f"💊 **Infection cleared for {member.mention}.**")
    else:
        await ctx.reply("🔍 Subject not infected.")

@bot.command(name="lockdown")
@commands.has_permissions(administrator=True)
async def lockdown(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🚨 **CHANNEL LOCKDOWN ACTIVE.** (30s)")
    await asyncio.sleep(30)
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
    await ctx.send("🔓 **LOCKDOWN LIFTED.**")

@bot.command(name="terminal-clear")
@commands.has_permissions(manage_messages=True)
async def terminal_clear(ctx, amount: int = 5):
    await ctx.message.delete()
    await ctx.channel.purge(limit=amount)

# --- 5. EVENTS ---

@bot.event
async def on_typing(channel, user, when):
    """Ghost Typing: The bot shadows targets while they type."""
    if user == bot.user: return
    if user.id == ISAAC_ID or user.id in fake_isaacs or user.id in infected_users:
        async with channel.typing():
            await asyncio.sleep(1) # Visual shadow effect

@bot.event
async def on_message(message):
    if message.author == bot.user: return

    # Reaction haunting
    if message.author.id in infected_users:
        if time.time() < infected_users[message.author.id]:
            try: await message.add_reaction("☣️")
            except: pass
        else:
            del infected_users[message.author.id]

    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
