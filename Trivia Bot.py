import discord
import aiohttp
import asyncio
import sqlite3
import random
from discord.ext import commands, tasks

TOKEN = "Token from Discord Developer Portal"
TRIVIA_API_URL = "Trivia API URL"

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

conn = sqlite3.connect("trivia_scores.db")
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        score INTEGER
    )
""")
conn.commit()

current_question = {}

async def fetch_trivia_question():
    async with aiohttp.ClientSession() as session:
        async with session.get(TRIVIA_API_URL) as response:
            data = await response.json()
            question_data = data["results"][0]
            
            question = question_data["question"]
            correct_answer = question_data["correct_answer"]
            options = question_data["incorrect_answers"] + [correct_answer]
            random.shuffle(options)
            
            return {
                "question": question,
                "correct_answer": correct_answer,
                "options": options
            }

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    post_trivia.start()