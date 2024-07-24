import discord, os
from discord.ext import commands
from dotenv import load_dotenv

client = commands.Bot(command_prefix = "/",intents=discord.Intents.all())
TOKEN = os.getenv("YOUSEPPE_TOKEN")

@client.event
async def on_ready():
    print("Youseppe está despierto ;3")
    print("---------------------------")
    
@client.command()
async def hello(ctx):
    await ctx.send("haiii :3")
    
client.run(TOKEN)