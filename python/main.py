import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from decouple import config

client = commands.Bot(command_prefix = "/",intents=discord.Intents.all())
slash = SlashCommand(client, sync_commands=True)
botToken = config('YOUSEPPE_TOKEN')

@client.event
async def on_ready():
    print("Youseppe esta despierto ;3")
    print("---------------------------")

@client.event
async def on_member_join(member):
    channel = client.get_channel(1265659906996961321)
    await channel.send(f"tevacae {member.name}")

@client.event
async def on_member_leave(member):
    channel = client.get_channel(1265659906996961321)
    await channel.send(f"sacaio {member.name}")
  
    
@client.command()
@slash.slash(name="haiii", description="Enviar un saludo")
async def haiii(ctx : SlashContext):
    await ctx.send("haiii :3")


@client.command()
@slash.slash(name="byeee", description="Enviar una despedida")
async def byeee(ctx: SlashContext):
    await ctx.send("byeee :3")

client.run(botToken)