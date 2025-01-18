import discord
import asyncio
from discord.ext import commands
from discord import FFmpegPCMAudio
from decouple import config
import yt_dlp
import random
from flask import Flask
from threading import Thread


botToken = config('YOUSEPPA_TOKEN')

# Define the bot with all intents
class MiBot(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync() # Sincroniza los comandos con Discord
        print("comandos internos sincronizados :3") 

intents = discord.Intents.all()
client = MiBot(command_prefix = '?', intents=intents)

isPlaying = False

# Cola de reproducción (ahora con tuplas para almacenar url y título)
queue = []


    
# Eventos-----------------------------------------------------------------------------------------
@client.event
async def on_ready():
    try:
        
        await client.tree.sync()
        print("Comandos slash sincronizados en el server")
    except Exception as e:
        print(f"Error al sincronizar comandos: {e}")
    
    if(client.command_prefix == '?'):
        print("Youseppa está despierta ;3")
        print("---------------------------")
    else:
        print("Youseppe está despierto ;3")
        print("---------------------------")
    
@client.event
async def on_member_join(member):
    channel = client.get_channel(int(config('BIENVENIDO_ID')))
    if channel:
        await channel.send(f"tevacae {member.name}")

@client.event
async def on_member_ban(member):
    channel = client.get_channel(int(config('BIENVENIDO_ID')))
    if channel:
        await channel.send(f"sacaio {member.name}")
        
# Funcinones asincronas----------------------------------------------------------------------------------


# Comandos de texto--------------------------------------------------------------------------

@client.tree.command(name= "haiii", description= "Dise haiii :3")
async def haiii(interaction: discord.Interaction):
    await interaction.response.send_message("haiii :3")

@client.tree.command(name= "byeee", description= "Dise byeee :3")
async def byeee(interaction: discord.Interaction):
    await interaction.response.send_message("byeee :3")

# Comandos de voz----------------------------------------------------------------------------


#Comandos de gestion de usuario----------------------------------------------------------------------------------
@client.tree.command(name="caracu", description="Envía a un usuario a otro canal de voz unos segundos")
async def caracu(interaction: discord.Interaction, member: discord.Member):
    # Obtén el canal de voz usando el ID
    channel = client.get_channel(int(config('CARACU_ID')))
    
    if channel is None or not isinstance(channel, discord.VoiceChannel):
        await interaction.response.send_message(f'El canal de voz con ID "{channel}" no existe o no es un canal de voz.')
        return

    if not member.voice:
        await interaction.response.send_message(f'{member.name} no está en ningún canal de voz.')
        return

    original_channel = member.voice.channel  # Guardar el canal original del miembro

    # Mueve al miembro al canal de voz especificado
    await member.move_to(channel)
    await interaction.response.send_message(f'Merecido caracu {member.name}')

    # Leer el archivo de GIFs y seleccionar uno al azar
    try:
        with open("./.txt/gifs.txt", "r") as file:
            gifs = file.readlines()
        if gifs:
            gif_url = random.choice(gifs).strip()  # Selecciona un GIF aleatorio y elimina espacios en blanco
            await interaction.followup.send(gif_url)  # Envía el enlace del GIF seleccionado
        else:
            await interaction.followup.send("No se encontraron GIFs en el archivo.")
    except FileNotFoundError:
        await interaction.followup.send("El archivo de GIFs no fue encontrado.")
    except Exception as e:
        await interaction.followup.send(f"Ocurrió un error: {e}")

    # Espera 5 segundos antes de devolver al miembro al canal original
    await asyncio.sleep(5)

    if original_channel is not None:  # Asegúrate de que el canal original sigue siendo válido
        await member.move_to(original_channel)  # Devuelve al miembro a su canal de voz original
        await interaction.followup.send(f'{member.name} ha sido devuelto a su canal original.')
        
client.run(botToken)
