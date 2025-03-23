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

@tasks.loop(hours=24)
async def trivia_loop():
    channel = discord.utils.get(bot.get_all_channels(), name="trivia")
    if channel:
        await post_trivia(channel)

async def post_trivia(channel):
    global current_question, current_answer
    async with aiohttp.ClientSession() as session:
        async with session.get(TRIVIA_API_URL) as resp:
            data = await resp.json()
            question_data = data['results'][0]
            
            question = question_data['question']
            options = question_data['incorrect_answers'] + [question_data['correct_answer']]
            random.shuffle(options)
            
            current_question = question
            current_answer = question_data['correct_answer']
            
            message = f"**Sports Trivia Question:** {question}\nOptions: {', '.join(options)}"
            await channel.send(message)

@bot.command()
async def answer(ctx, *, user_answer: str):
    global current_answer
    if not current_answer:
        await ctx.send("No active trivia question. Please wait for the next one!")
        return
    
    if user_answer.lower() == current_answer.lower():
        await ctx.send(f"Correct, {ctx.author.mention}! 🎉")
        scores[str(ctx.author.id)] = scores.get(str(ctx.author.id), 0) + 1
    else:
        await ctx.send(f"Incorrect! The correct answer was: {current_answer}")
    
    save_scores()
    current_answer = None

@bot.command()
async def leaderboard(ctx):
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    leaderboard_text = "\n".join([f"<@{user}>: {score} points" for user, score in sorted_scores])
    await ctx.send(f"**Leaderboard:**\n{leaderboard_text}")

@bot.command()
async def hint(ctx):
    if current_answer:
        await ctx.send(f"Hint: The answer starts with '{current_answer[0]}'")
    else:
        await ctx.send("No active trivia question.")


def save_scores():
    with open("scores.json", "w") as f:
        json.dump(scores, f)

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
