import json
import os

import discord
from discord import app_commands
from discord.ext import commands

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "staff_channels.json")


def _cargar_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _guardar_config(data):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def set_staff_channel(guild_id: int, channel_id: int):
    data = _cargar_config()
    data[str(guild_id)] = channel_id
    _guardar_config(data)


def get_staff_channel(guild_id: int):
    data = _cargar_config()
    return data.get(str(guild_id))


class StaffUpdates(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set-staff-channel", description="Define el canal donde se anuncian los ascensos de staff")
    @app_commands.describe(channel="Canal donde se enviaran los anuncios de staff")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_staff_channel_cmd(self, interaction: discord.Interaction, channel: discord.TextChannel):
        set_staff_channel(interaction.guild.id, channel.id)

        embed = discord.Embed(
            title="Canal de staff configurado",
            description=f"Los ascensos se anunciaran en {channel.mention}.",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @set_staff_channel_cmd.error
    async def set_staff_channel_cmd_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "No tienes permisos para usar este comando.", ephemeral=True
            )
        else:
            raise error

    @app_commands.command(name="promote", description="Anuncia que un usuario subio de cargo")
    @app_commands.describe(user="Usuario que subio de cargo", rank="Nombre del nuevo cargo o rango")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def promote(self, interaction: discord.Interaction, user: discord.Member, rank: str):
        channel_id = get_staff_channel(interaction.guild.id)

        if channel_id is None:
            await interaction.response.send_message(
                "Aun no se ha configurado el canal de staff. Usa /set-staff-channel primero.",
                ephemeral=True,
            )
            return

        channel = interaction.guild.get_channel(channel_id)
        if channel is None:
            await interaction.response.send_message(
                "El canal configurado ya no existe. Vuelve a configurarlo con /set-staff-channel.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="Ascenso de staff",
            description=f"{user.mention} ha subido al cargo de **{rank}**.",
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"Actualizado por {interaction.user}")

        await channel.send(embed=embed)
        await interaction.response.send_message(
            f"Anuncio enviado en {channel.mention}.", ephemeral=True
        )

    @promote.error
    async def promote_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "No tienes permisos para usar este comando.", ephemeral=True
            )
        else:
            raise error

    @app_commands.command(name="demote", description="Anuncia que un usuario bajo de cargo")
    @app_commands.describe(user="Usuario que bajo de cargo", rank="Nombre del nuevo cargo o rango")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def demote(self, interaction: discord.Interaction, user: discord.Member, rank: str):
        channel_id = get_staff_channel(interaction.guild.id)

        if channel_id is None:
            await interaction.response.send_message(
                "Aun no se ha configurado el canal de staff. Usa /set-staff-channel primero.",
                ephemeral=True,
            )
            return

        channel = interaction.guild.get_channel(channel_id)
        if channel is None:
            await interaction.response.send_message(
                "El canal configurado ya no existe. Vuelve a configurarlo con /set-staff-channel.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="Descenso de staff",
            description=f"{user.mention} ha bajado al cargo de **{rank}**.",
            color=discord.Color.orange(),
        )
        embed.set_footer(text=f"Actualizado por {interaction.user}")

        await channel.send(embed=embed)
        await interaction.response.send_message(
            f"Anuncio enviado en {channel.mention}.", ephemeral=True
        )

    @demote.error
    async def demote_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "No tienes permisos para usar este comando.", ephemeral=True
            )
        else:
            raise error


async def setup(bot):
    await bot.add_cog(StaffUpdates(bot))
