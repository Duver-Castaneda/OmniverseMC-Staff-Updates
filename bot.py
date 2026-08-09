import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Carga las variables del archivo .env (ahi va tu token)
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Intents: permisos que necesita el bot para funcionar
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Conectado como {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands sincronizados: {len(synced)}")
    except Exception as e:
        print(f"Error al sincronizar comandos: {e}")


@bot.command()
async def ping(ctx):
    """Comando basico de prueba (prefijo !)"""
    await ctx.send(f"Pong! Latencia: {round(bot.latency * 1000)}ms")


@bot.tree.command(name="hola", description="El bot te saluda")
async def hola(interaction: discord.Interaction):
    """Comando basico de prueba (slash command)"""
    await interaction.response.send_message(f"Hola, {interaction.user.mention}!")


async def cargar_cogs():
    """Carga automaticamente todos los cogs de la carpeta /cogs"""
    for archivo in os.listdir("./cogs"):
        if archivo.endswith(".py") and archivo != "__init__.py":
            await bot.load_extension(f"cogs.{archivo[:-3]}")
            print(f"Cog cargado: {archivo}")


@bot.event
async def setup_hook():
    await cargar_cogs()


if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("No se encontro DISCORD_TOKEN en el archivo .env")
    bot.run(TOKEN)
