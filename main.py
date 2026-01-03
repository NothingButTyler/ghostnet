import discord
from discord.ext import commands
import os
import asyncio
import random
import time
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

ISAAC_ID = 1444073106384621631
fake_isaacs = [] 
infected_users = {} # {user_id: expiry_timestamp}
global_prank = False 

# --- 3. HELPER LOGIC ---
def is_treated_as_isaac(ctx_or_msg):
    author = ctx_or_msg.author
    if author.guild_permissions.administrator: return False
    if global_prank: return True
    is_infected = author.id in infected_users and time.time() < infected_users[author.id]
    return author.id == ISAAC_ID or author.id in fake_isaacs or is_infected

# --- 4. COMMANDS ---

@bot.command(name="help")
async def help_cmd(ctx):
    if is_treated_as_isaac(ctx):
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="🛠️ CONFIG", value="`ERROR: NEURAL LINK CORRUPTED`", inline=False)
        return await ctx.reply(embed=embed)

    if ctx.author.guild_permissions.administrator:
        embed = discord.Embed(title="🛰️ GHOSTNET STAFF TERMINAL", color=0x00ff00)
        embed.add_field(name="☣️ BIOWARE", 
                        value="`!infect @user` - 5min reaction haunt\n`!cure @user` - Clear infection + DM", inline=False)
        embed.add_field(name="💀 PRANK TOOLS", 
                        value="`!hack @user` - Fake breach\n`!test-prank [user]` - Toggle Isaac status", inline=False)
        embed.add_field(name="🛡️ SECURITY", 
                        value="`!lockdown` - Silence channel\n`!unlock` - Force lift lockdown\n`!system-logs @user` - View logs", inline=False)
        embed.add_field(name="🛠️ UTILITY", 
                        value="`!terminal-clear [num]`\n`!scan-network`\n`!ping`", inline=False)
        await ctx.reply(content="🛡️ **Terminal Access Granted.**", embed=embed)
    else:
        embed = discord.Embed(title="🛰️ GHOSTNET DIRECTORY", color=0x2b2d31)
        embed.add_field(name="💀 COMMANDS", value="`!hack @user`\n`!ping`", inline=False)
        await ctx.reply(embed=embed)

@bot.command(name="infect")
@commands.has_permissions(administrator=True)
async def infect(ctx, member: discord.Member = None):
    if is_treated_as_isaac(ctx): return
    if not member: return await ctx.reply("❌ Specify a host to infect.")
    
    infected_users[member.id] = time.time() + 300 # 5 minutes
    
    embed = discord.Embed(title="☣️ INFECTION SUCCESSFUL", color=0x7800ff)
    embed.description = f"User {member.mention} has been injected with **GHOST-WARE v2.1**."
    await ctx.send(embed=embed)

@bot.command(name="cure")
@commands.has_permissions(administrator=True)
async def cure(ctx, member: discord.Member = None):
    if is_treated_as_isaac(ctx): return
    if not member: return await ctx.reply("❌ Specify a subject to cure.")
    
    if member.id in infected_users:
        del infected_users[member.id]
        
        # Public Response
        embed = discord.Embed(title="💊 ANTIVIRUS DEPLOYED", color=0x00ff00)
        embed.description = f"Infection cleared for {member.mention}."
        await ctx.send(embed=embed)
        
        # Private DM Response
        try:
            await member.send("🛰️ **GHOSTNET NOTIFICATION:** Neural link stabilized. Your connection is no longer being monitored.")
        except:
            pass # Fails if user has DMs closed
    else:
        await ctx.reply(f"🔍 `{member.name}` is not currently infected.")

@bot.command(name="lockdown")
@commands.has_permissions(administrator=True)
async def lockdown(ctx):
    if is_treated_as_isaac(ctx): return
    msg = await ctx.send("`[!] WARNING: PACKET OVERLOAD`")
    await asyncio.sleep(1)
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    
    embed = discord.Embed(title="🛑 CHANNEL SECURED", color=0xff0000)
    embed.description = "```diff\n- FIREWALL: ACTIVE\n```"
    await msg.edit(content="🚨 **LOCKDOWN ACTIVE.**", embed=embed)
    
    await asyncio.sleep(30)
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
    await ctx.send("🔓 **LOCKDOWN LIFTED.**")

@bot.command(name="unlock")
@commands.has_permissions(administrator=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
    await ctx.send("🔓 **MANUAL OVERRIDE SUCCESSFUL.**")

@bot.command(name="system-logs")
async def system_logs(ctx, member: discord.Member = None):
    if is_treated_as_isaac(ctx): return
    target = member if member else (ctx.guild.get_member(ISAAC_ID) or ctx.author)
    
    # Logic to pick between AI or Human logs
    log_type = "🤖 AI DEEP-SCAN" if target.bot else "📜 SYSTEM LOGS"
    color = 0xff00ff if target.bot else 0x5865f2
    
    log_entry = f"[{random.randint(10,23)}:00] Data intercept on {target.name}: [OK]"
    
    embed = discord.Embed(title=log_type, color=color)
    embed.description = f"```ini\n{log_entry}```"
    await ctx.reply(embed=embed)

# --- 5. EVENTS ---

@bot.event
async def on_message(message):
    if message.author == bot.user: return

    # Check for active infection reactions
    if message.author.id in infected_users:
        if time.time() < infected_users[message.author.id]:
            await message.add_reaction("☣️")
        else:
            del infected_users[message.author.id]

    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
