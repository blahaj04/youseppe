import discord
from discord.ext import commands
from discord import app_commands
from decouple import config

client = commands.Bot(command_prefix = "/",intents=discord.Intents.all())
botToken = config('YOUSEPPE_TOKEN')

@client.event
async def on_ready():
    print("Youseppe esta despierto ;3")
    print("---------------------------")
    await client.tree.sync()

@client.event
async def on_member_join(member):
    channel = client.get_channel(1265659906996961321)
    await channel.send(f"tevacae {member.name}")

@client.event
async def on_member_leave(member):
    channel = client.get_channel(1265659906996961321)
    await channel.send(f"sacaio {member.name}")

@client.command()
async def haiii(ctx):
    await ctx.send("haiii :3")

@client.command()
async def byeee(ctx):
    await ctx.send("byeee :3")
    
@client.command(pass_context = True)
async def play(ctx):
    if(ctx.author.voice):
        channel = ctx.message.author.voice.channel
        await channel.connect()
        print("me he unio")
    else:
        await ctx.send("No estas en un canal de voz. ¡Necesito que estes en uno para que me pueda unir >:3 !")
        

@client.command(pass_context = True)
async def stop(ctx):
    if(ctx.voice_client):
        await ctx.guild.voice_disconnect()
        print("me he salio")
    else:
        await ctx.send("No estoy en ningun canal de voz. ¿Tan mal te caigo? :(")

client.run(botToken)