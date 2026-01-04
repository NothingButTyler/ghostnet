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

# Configuration constants
ISAAC_ID = 1444073106384621631
fake_isaacs = [] 
infected_users = {} # Stores {user_id: expiry_timestamp}
global_prank = False 

# --- 3. HELPER LOGIC ---
def is_treated_as_isaac(ctx_or_msg):
    """Checks if the user is currently a target for the bot's pranks."""
    author = ctx_or_msg.author
    if author.guild_permissions.administrator: return False
    if global_prank: return True
    is_infected = author.id in infected_users and time.time() < infected_users[author.id]
    return author.id == ISAAC_ID or author.id in fake_isaacs or is_infected

# --- 4. COMMANDS ---

@bot.command(name="spoof")
@commands.has_permissions(administrator=True)
async def spoof(ctx, member: discord.Member, *, message: str):
    """Identity Thief: Impersonate a user via Webhook."""
    if is_treated_as_isaac(ctx): return
    await ctx.message.delete()
    webhook = await ctx.channel.create_webhook(name=member.display_name)
    await webhook.send(
        content=message, 
        username=member.display_name, 
        avatar_url=member.display_avatar.url
    )
    await webhook.delete()

@bot.command(name="help")
async def help_cmd(ctx):
    """Restored Terminal UI with Active Protocol Status."""
    if is_treated_as_isaac(ctx):
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="🛠️ CONFIG", value="`ERROR: NEURAL LINK CORRUPTED`", inline=False)
        return await ctx.reply(embed=embed)

    if ctx.author.guild_permissions.administrator:
        embed = discord.Embed(title="🛰️ GHOSTNET STAFF TERMINAL", color=0x00ff00)
        embed.add_field(name="☣️ BIOWARE", value="`!infect @user` | `!cure @user`", inline=True)
        embed.add_field(name="💀 PRANK", value="`!hack @user` | `!spoof @user [msg]` | `!system-logs @user`", inline=True)
        embed.add_field(name="🛡️ SECURITY", value="`!lockdown` | `!unlock` | `!shutdown`", inline=False)
        embed.add_field(name="🛠️ UTILITY", value="`!terminal-clear [num]` | `!ping` | `!test-prank @user`", inline=False)
        
        # New "Active Protocols" status indicator
        embed.add_field(name="🛰️ ACTIVE PROTOCOLS", 
                        value="`GHOST-TYPING: ENABLED`\n`REACTION-HAUNT: ENABLED`", inline=False)
        
        await ctx.reply(content="🛡️ **Terminal Access Granted.**", embed=embed)
    else:
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="💀 COMMANDS", value="`!hack @user` | `!ping`", inline=False)
        await ctx.reply(embed=embed)

# (All other commands: hack, system-logs, lockdown, terminal-clear, infect, cure remain here)

@bot.command(name="system-logs")
async def system_logs(ctx, member: discord.Member = None):
    if is_treated_as_isaac(ctx): return
    target = member if member else (ctx.guild.get_member(ISAAC_ID) or ctx.author)
    human_templates = ["Packet from {user}: 'Search: how to bypass bot'", "Keystroke captured: [REDACTED]"]
    bot_templates = ["AI Subroutine of {user} intercepted.", "Metadata scan: 'Spaghetti Code'."]
    log_templates = bot_templates if target.bot else human_templates
    selected_logs = random.sample(log_templates, min(len(log_templates), 2))
    formatted_logs = "\n".join([f"[{random.randint(10,23)}:{random.randint(10,59)}] {log.format(user=target.name)}" for log in selected_logs])
    embed = discord.Embed(title=f"📜 LOGS: {target.name}", description=f"```ini\n{formatted_logs}```", color=0x5865f2)
    await ctx.reply(embed=embed)

@bot.command(name="hack")
async def hack(ctx, member: discord.Member = None):
    if is_treated_as_isaac(ctx): return
    target = member if member else ctx.author
    msg = await ctx.send(f"🛰️ `[CONNECTING TO {target.name.upper()}...]`")
    await asyncio.sleep(1)
    for step in ["🔓 Bypassing 2FA...", "☣️ Injecting Virus..."]:
        await msg.edit(content=f"⚙️ `{step}`")
        await asyncio.sleep(1)
    embed = discord.Embed(title="✅ BREACH SUCCESSFUL", color=0x00ff00)
    embed.description = f"```diff\n+ Target: {target.name}\n+ Status: CONTROLLED\n```"
    await msg.edit(content=None, embed=embed)

@bot.command(name="terminal-clear")
@commands.has_permissions(manage_messages=True)
async def terminal_clear(ctx, amount: int = 5):
    if is_treated_as_isaac(ctx): return
    await ctx.message.delete()
    await ctx.channel.purge(limit=amount)

# --- 6. EVENTS & RUN ---

@bot.event
async def on_typing(channel, user, when):
    """Ghost Typing: The bot mirrors the typing status of targets."""
    if user == bot.user: return
    if user.id == ISAAC_ID or user.id in fake_isaacs or user.id in infected_users:
        async with channel.typing():
            await asyncio.sleep(1) 

@bot.event
async def on_message(message):
    if message.author == bot.user: return
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
