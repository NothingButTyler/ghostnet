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
infected_users = {} # Stores {user_id: expiry_timestamp}
global_prank = False 

# --- 3. HELPER LOGIC ---
def is_treated_as_isaac(ctx_or_msg):
    # Check if input is Context or Message
    author = ctx_or_msg.author if hasattr(ctx_or_msg, 'author') else ctx_or_msg.author
    
    if author.guild_permissions.administrator: return False
    if global_prank: return True
    
    # Check for active infection
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
        embed.add_field(name="💀 PRANK TOOLS", 
                        value="`!hack @user`\n`!test-prank [user]`\n`!infect @user` - 5min Biohazard", inline=False)
        embed.add_field(name="🛡️ SECURITY", 
                        value="`!lockdown` - Silence channel\n`!scan-network`\n`!system-logs @user`", inline=False)
        embed.add_field(name="🛠️ UTILITY", 
                        value="`!terminal-clear [num]`\n`!ping`", inline=False)
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
    
    # Set infection for 5 minutes (300 seconds)
    infected_users[member.id] = time.time() + 300
    
    embed = discord.Embed(title="☣️ INFECTION SUCCESSFUL", color=0x7800ff)
    embed.description = f"User {member.mention} has been injected with **GHOST-WARE v2.1**.\nAll outgoing packets will be flagged."
    await ctx.send(embed=embed)

@bot.command(name="lockdown")
@commands.has_permissions(administrator=True)
async def lockdown(ctx):
    if is_treated_as_isaac(ctx): return
    msg = await ctx.send("`[!] WARNING: UNAUTHORIZED PACKET OVERLOAD DETECTED`")
    await asyncio.sleep(1.5)
    for i in range(3, 0, -1):
        await msg.edit(content=f"⚠️ **GHOSTNET LOCKDOWN INITIATED: {i}...**")
        await asyncio.sleep(1)
    
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    embed = discord.Embed(
        title="🛑 CHANNEL SECURED", 
        description="```diff\n- FIREWALL: ACTIVE\n- ENCRYPTION: 4096-BIT\n```",
        color=0xff0000
    )
    embed.add_field(name="STATUS", value="`NETWORK ISOLATION COMPLETE (30S)`")
    await msg.edit(content="🚨 **TERMINAL SECURED.**", embed=embed)

    await asyncio.sleep(30)
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
    await ctx.send("🔓 **LOCKDOWN LIFTED.** Traffic resuming...")

@bot.command(name="system-logs")
async def system_logs(ctx, member: discord.Member = None):
    if is_treated_as_isaac(ctx): return
    target = member if member else (ctx.guild.get_member(ISAAC_ID) or ctx.author)
    
    human_templates = ["Packet sniffed from {user}", "Trace complete on {user}"]
    bot_templates = ["AI Subroutine intercepted from {user}", "SUDO PURGE detected"]

    log_templates = bot_templates if target.bot else human_templates
    header = f"🤖 AI DEEP-SCAN: {target.name}" if target.bot else f"📜 SYSTEM LOGS: {target.name}"
    color = 0xff00ff if target.bot else 0x5865f2

    formatted_logs = f"[{random.randint(10,23)}:00] {random.choice(log_templates).format(user=target.name)}"
    
    embed = discord.Embed(title=header, color=color)
    embed.description = f"```ini\n{formatted_logs}```"
    await ctx.reply(embed=embed)

@bot.command(name="test-prank")
@commands.has_permissions(administrator=True)
async def test_prank(ctx, member: discord.Member = None):
    target = member if member else ctx.author
    if target.id in fake_isaacs:
        fake_isaacs.remove(target.id)
        await ctx.reply(f"🔓 **RECOVERY:** `{target.name}` cleared.")
    else:
        fake_isaacs.append(target.id)
        await ctx.reply(f"☣️ **INFECTED:** `{target.name}` flagged.")

@bot.command(name="scan-network")
async def scan_network(ctx):
    if is_treated_as_isaac(ctx): return
    isaac_member = ctx.guild.get_member(ISAAC_ID)
    active_test_targets = [m for m in ctx.guild.members if m.id in fake_isaacs]
    all_threats = ([isaac_member] if isaac_member else []) + active_test_targets

    if all_threats:
        status, color = "UNSTABLE", 0xff0000
        threat_display = ", ".join([m.mention for m in all_threats])
        content_msg = f"`[SYSTEM SCAN...]` - ⚠️ ALERT: {threat_display}"
    else:
        status, color = "STABLE", 0x00ff00
        threat_display = "NONE"
        content_msg = "`[SYSTEM SCAN...]`"

    embed = discord.Embed(title="🛰️ GHOSTNET DIAGNOSTIC", color=color)
    embed.add_field(name="🔒 STATUS", value=f"`{status}`", inline=True)
    embed.add_field(name="🚨 THREATS", value=threat_display, inline=False)
    await ctx.reply(content=content_msg, embed=embed)

@bot.command()
async def ping(ctx):
    if is_treated_as_isaac(ctx): return await ctx.reply("`ERR_TIMEOUT`")
    await ctx.reply(f"🛰️ **LATENCY:** {round(bot.latency * 1000)}ms")

# --- 5. EVENTS ---

@bot.event
async def on_message(message):
    if message.author == bot.user: return

    # Infection Logic: Auto-react with Biohazard
    if message.author.id in infected_users:
        if time.time() < infected_users[message.author.id]:
            await message.add_reaction("☣️")
        else:
            del infected_users[message.author.id]

    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("DISCORD_TOKEN"))
