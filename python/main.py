import discord
from discord.ext import commands
client = commands.Bot(command_prefix = '/')

@client.event
async def on_ready():
    print("Youseppe está despierto ;3")
    print("---------------------------")
    
@client.command()
async def isAwaken(ctx):
    await ctx.send("haiii :3")
    
client.run('MTI2NTQxNjQzNzQ4OTcyOTU2Nw.G651uw.2fP-EK2dqiwV0sTmXMLrwbzSKbnG7LqDJrwNXY')