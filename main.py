import discord
from discord.ext import commands
import os
import asyncio
import random
import time
import uuid # New: For tracking session IDs
from flask import Flask
from threading import Thread

# --- 1. WEB SERVER ---
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

# SESSION ID: Helps detect if multiple bots are running
SESSION_ID = str(uuid.uuid4())[:8]

ISAAC_ID = 1444073106384621631
fake_isaacs = [] 
infected_users = {} 
global_prank = False 

# --- 3. HELPER LOGIC ---
def is_treated_as_isaac(ctx_or_msg):
    author = ctx_or_msg.author
    if author.guild_permissions.administrator: return False
    if global_prank: return True
    is_infected = author.id in infected_users and time.time() < infected_users[author.id]
    return author.id == ISAAC_ID or author.id in fake_isaacs or is_infected

# --- 4. COMMANDS ---

@bot.command(name="hard-reset")
@commands.has_permissions(administrator=True)
async def hard_reset(ctx):
    """Kills the process entirely to fix double-messaging."""
    await ctx.send("🚨 **TERMINATING ALL GHOSTNET SESSIONS...**")
    os._exit(0) # Forcefully kills the script process

@bot.command(name="ping")
async def ping(ctx):
    """Shows Latency and Session ID to check for duplicates."""
    if is_treated_as_isaac(ctx): return await ctx.reply("`ERR_TIMEOUT`")
    await ctx.reply(f"🛰️ **LATENCY:** {round(bot.latency * 1000)}ms | **SESSION:** `{SESSION_ID}`")

@bot.command(name="spoof")
@commands.has_permissions(administrator=True, manage_webhooks=True)
async def spoof(ctx, member: discord.Member, *, message: str):
    if is_treated_as_isaac(ctx): return
    try:
        await ctx.message.delete()
        webhook = await ctx.channel.create_webhook(name=f"Ghost-{member.display_name}")
        await webhook.send(content=message, username=member.display_name, avatar_url=member.display_avatar.url)
        await webhook.delete()
    except Exception as e:
        await ctx.send(f"⚠️ `GHOSTNET ERR: {e}`")

@bot.command(name="help")
async def help_cmd(ctx):
    if is_treated_as_isaac(ctx):
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="🛠️ CONFIG", value="`ERROR: NEURAL LINK CORRUPTED`", inline=False)
        return await ctx.reply(embed=embed)

    if ctx.author.guild_permissions.administrator:
        embed = discord.Embed(title="🛰️ GHOSTNET STAFF TERMINAL", color=0x00ff00)
        embed.add_field(name="💀 PRANK", value="`!hack` | `!spoof` | `!system-logs`", inline=False)
        embed.add_field(name="☣️ BIOWARE", value="`!infect` | `!cure`", inline=False)
        embed.add_field(name="🛡️ SECURITY", value="`!lockdown` | `!hard-reset` | `!shutdown`", inline=False)
        embed.set_footer(text=f"SESSION: {SESSION_ID} | GHOST-TYPING: ACTIVE")
        await ctx.reply(embed=embed)

# --- 5. EVENTS ---

@bot.event
async def on_message(message):
    # CRITICAL: If this doesn't stop double msgs, you have two bots online.
    if message.author == bot.user:
        return

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
