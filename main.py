import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
import random
import sys
from flask import Flask, jsonify
from flask_cors import CORS
from threading import Thread
import google.generativeai as genai

# --- 1. DATABASE ARCHITECTURE ---
def init_db():
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS blacklist (user_id INTEGER PRIMARY KEY, reason TEXT)")
    conn.commit()
    conn.close()
    print("🛰️ DATABASE: economy.db verified.")

# --- 2. DASHBOARD API ---
app = Flask('')
CORS(app)

@app.route('/')
def home():
    return "GHOSTNET CORE: ONLINE"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- 3. BOT CORE SETUP ---
class GhostNet(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        init_db()
        await self.tree.sync()
        print("🛰️ GHOSTNET: Systems synchronized.")

bot = GhostNet()

# --- 4. EXECUTION ---
if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_KEY")
    if api_key:
        genai.configure(api_key=api_key)
    
    Thread(target=run_web, daemon=True).start()
    
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("❌ CRITICAL: DISCORD_TOKEN missing in environment.")
