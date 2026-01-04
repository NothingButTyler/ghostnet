import discord
from discord.ext import commands
import os, asyncio, random, time, uuid
from flask import Flask
from threading import Thread
import google.generativeai as genai

# Setup Gemini
genai.configure(api_key=os.environ.get("GEMINI_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')


# --- 1. WEB SERVER (Improved for Render) ---
app = Flask('')
SESSION_ID = str(uuid.uuid4())[:8]

@app.route('/')
def home(): 
    return {"status": "ONLINE", "session": SESSION_ID, "bot": "GHOSTNET"}

def run():
    # Render usually uses port 10000 by default
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

ISAAC_ID = 1444073106384621631
infected_users = {} 
welcome_config = {
    "channel_id": None,
    "message": "Welcome to the terminal, {user}. Connection established."
}

# --- 3. HELPER FUNCTIONS ---
def is_treated_as_isaac(ctx_or_msg):
    author = ctx_or_msg.author
    if author.guild_permissions.administrator: return False
    is_infected = author.id in infected_users and time.time() < infected_users[author.id]
    return author.id == ISAAC_ID or is_infected

# --- 4. THE GEMINI "SAFETY SHIELD" ---
# This function runs in the background so it CANNOT freeze the bot
async def get_gemini_response(prompt):
async def get_gemini_response(prompt):
    try:
        # We use asyncio.to_thread because the genai library is "blocking"
        response = await asyncio.to_thread(model.generate_content, prompt)
        
        # Keep it short for Discord
        return response.text[:1900] 
    except Exception as e:
        print(f"GEMINI_ERROR: {e}")
        return "⚠️ [SIGNAL_LOST] AI_CORE_TIMEOUT"


# --- 5. COMMANDS ---

@bot.command(name="welcome-setup")
@commands.has_permissions(administrator=True)
async def welcome_setup(ctx, channel: discord.TextChannel):
    welcome_config["channel_id"] = channel.id
    await ctx.send(f"✅ **WELCOME PROTOCOL:** Destination set to {channel.mention}")

@bot.command(name="help")
async def help_cmd(ctx):
    if is_treated_as_isaac(ctx): return
    embed = discord.Embed(title="🛰️ GHOSTNET STAFF TERMINAL", color=0x00ff00)
    embed.add_field(name="👋 WELCOME", value="`!welcome-setup` | `!welcome-edit` | `!welcome-test`", inline=False)
    embed.add_field(name="🛡️ SECURITY", value="`!lockdown` | `!hard-reset` | `!infect`", inline=False)
    embed.set_footer(text=f"SESSION: {SESSION_ID}")
    await ctx.reply(embed=embed)

@bot.command(name="hard-reset")
@commands.has_permissions(administrator=True)
async def hard_reset(ctx):
    await ctx.send(f"🚨 **REBOOTING SESSION `{SESSION_ID}`...**")
    os._exit(0)

# --- 6. EVENTS (The Logic Hub) ---

@bot.event
async def on_message(message):
    if message.author == bot.user: return

    # 1. Check for infection reactions
    if message.author.id in infected_users:
        if time.time() < infected_users[message.author.id]:
            try: await message.add_reaction("☣️")
            except: pass

    # 2. AI Chat Trigger (Only if bot is mentioned)
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        async with message.channel.typing():
            # This is the secret! We run Gemini but don't stop the bot.
            response = await get_gemini_response(message.content)
            if response:
                await message.reply(response)

    # 3. Process regular commands
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"--- GHOSTNET {SESSION_ID} IS DEPLOYED ---")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="the Mainframe"))

if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ ERROR: No DISCORD_TOKEN found in environment variables!")
