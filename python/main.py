import discord
from discord.ext import commands
from decouple import config

client = commands.Bot(command_prefix = "/",intents=discord.Intents.all())
botToken = config('YOUSEPPE_TOKEN')

@client.event
async def on_ready():
    print("Youseppe está despierto ;3")
    print("---------------------------")
    
@client.command()
async def hello(ctx):
    await ctx.send("haiii :3")
    
client.run(botToken)