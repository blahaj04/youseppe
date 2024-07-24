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
   


@client.event(name="haiii", description="Enviar un saludo")
async def haiii(interaction: discord.Interaction):
    await interaction.response.send_message("haiii :3")

@client.event(name="byeee", description="Enviar una despedida")
async def byeee(interaction: discord.Interaction):
    await interaction.response.send_message("byeee :3")

client.run(botToken)