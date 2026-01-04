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
    # Render's default port is 10000
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

SESSION_ID = str(uuid.uuid4())[:8] # Unique tag for this run
ISAAC_ID = 1444073106384621631
infected_users = {} # {user_id: expiry_timestamp}

def is_treated_as_isaac(ctx_or_msg):
    author = ctx_or_msg.author
    if author.guild_permissions.administrator: return False
    is_infected = author.id in infected_users and time.time() < infected_users[author.id]
    return author.id == ISAAC_ID or is_infected

# --- 3. COMMANDS ---

@bot.command(name="hard-reset")
@commands.has_permissions(administrator=True)
async def hard_reset(ctx):
    """Restarts the Render service by killing the process."""
    await ctx.send(f"🚨 **REBOOTING SESSION `{SESSION_ID}`...**")
    os._exit(0)

@bot.command(name="help")
async def help_cmd(ctx):
    if is_treated_as_isaac(ctx):
        return await ctx.reply("`ERROR: NEURAL LINK CORRUPTED`")

    embed = discord.Embed(title="🛰️ GHOSTNET STAFF TERMINAL", color=0x00ff00)
    embed.add_field(name="💀 PRANK", value="`!hack` | `!spoof @user [msg]` | `!system-logs`", inline=False)
    embed.add_field(name="☣️ BIOWARE", value="`!infect @user` | `!cure @user`", inline=False)
    embed.add_field(name="🛡️ SECURITY", value="`!lockdown` | `!hard-reset` | `!terminal-clear`", inline=False)
    embed.set_footer(text=f"SESSION: {SESSION_ID} | STATUS: ACTIVE")
    await ctx.reply(embed=embed)

@bot.command(name="terminal-clear")
@commands.has_permissions(manage_messages=True)
async def terminal_clear(ctx, amount: int = 5):
    if is_treated_as_isaac(ctx): return
    await ctx.message.delete()
    await ctx.channel.purge(limit=amount)

@bot.command(name="infect")
@commands.has_permissions(administrator=True)
async def infect(ctx, member: discord.Member):
    if member.guild_permissions.administrator: return await ctx.reply("❌ `ADMIN IMMUNITY`")
    infected_users[member.id] = time.time() + 3600 
    await ctx.send(f"☣️ **{member.name} has been marked for haunting.**")

@bot.command(name="cure")
@commands.has_permissions(administrator=True)
async def cure(ctx, member: discord.Member):
    if member.id in infected_users:
        del infected_users[member.id]
        await ctx.send(f"💉 **{member.name} has been cured.**")

@bot.command(name="spoof")
@commands.has_permissions(administrator=True, manage_webhooks=True)
async def spoof(ctx, member: discord.Member, *, message: str):
    if is_treated_as_isaac(ctx): return
    await ctx.message.delete()
    webhook = await ctx.channel.create_webhook(name=f"Ghost-{member.display_name}")
    await webhook.send(content=message, username=member.display_name, avatar_url=member.display_avatar.url)
    await webhook.delete()

# --- 4. EVENTS ---

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
