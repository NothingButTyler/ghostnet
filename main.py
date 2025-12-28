import discord
from discord.ext import commands
import os
import random
import time
from flask import Flask
from threading import Thread

# 1. WEB SERVER
app = Flask('')
@app.route('/')
def home():
    return "GHOSTNET: ONLINE"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 2. BOT SETUP
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
start_time = time.time()

@bot.event
async def on_ready():
    print(f'>>> SUCCESS: {bot.user} is online.')

# 3. COMMANDS
@bot.command()
async def hack(ctx, target: discord.Member = None):
    if not target:
        await ctx.send("Specify a target to breach.")
        return
    
    msg = await ctx.send(f"```fix\n[BREACHING]: {target.name}...```")
    time.sleep(1)
    await msg.edit(content=f"```diff\n+ [SUCCESS]: {target.name} pwned.```")

@bot.command()
async def status(ctx):
    uptime = int(time.time() - start_time)
    await ctx.send(f"```yaml\nUPTIME: {uptime}s\nSTATUS: OPERATIONAL\n```")

@bot.command()
async def encrypt(ctx, *, message=None):
    if message is None:
        await ctx.send("```yaml\nERROR: No input detected for encryption.\nUSAGE: !encrypt <text>\n```")
        return

    # Converts text to a hex data stream
    hex_output = " ".join(hex(ord(c))[2:].upper() for c in message)
    
    await ctx.send(
        f"🛰️ **ENCRYPTING VIA GHOSTNET PROXY...**\n"
        f"```fix\n0x{hex_output}```"
    )


# 4. STARTUP
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("TOKEN NOT FOUND")
