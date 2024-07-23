import discord
from discord.ext import commands

client = commands.Bot(command_prefix = "/",intents=discord.Intents.all())

@client.event
async def on_ready():
    print("Youseppe está despierto ;3")
    print("---------------------------")
    
@client.command()
async def hello(ctx):
    await ctx.send("haiii :3")
    
client.run("MTI2NTQxNjQzNzQ4OTcyOTU2Nw.GKKtCn.DJCP-Kz0x4SExn47HrnOa8EL3tlmw9SvIFdQjI")