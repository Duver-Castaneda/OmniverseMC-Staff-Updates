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

    @app_commands.command(name="promote", description="Anuncia que un usuario subio de cargo y le otorga el rol")
    @app_commands.describe(user="Usuario que subio de cargo", rank="Rol del nuevo cargo (se le otorgara al usuario)")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def promote(self, interaction: discord.Interaction, user: discord.Member, rank: discord.Role):
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

        try:
            await user.add_roles(rank, reason=f"Ascenso aplicado por {interaction.user}")
        except discord.Forbidden:
            await interaction.response.send_message(
                "No tengo permisos para otorgar ese rol. Verifica que mi rol este por encima de "
                f"{rank.mention} en la jerarquia del servidor.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="🎉 ¡Ascenso de Staff! 🎉",
            description=(
                f"### {user.mention} ha subido de cargo\n"
                f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
            ),
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="👤 Usuario", value=user.mention, inline=True)
        embed.add_field(name="🏆 Nuevo cargo", value=rank.mention, inline=True)
        embed.add_field(name="🛡️ Actualizado por", value=interaction.user.mention, inline=False)
        embed.set_footer(
            text=f"{interaction.guild.name} • Felicidades por el ascenso",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None,
        )

        anuncio = await channel.send(content=f"🎉 {user.mention}", embed=embed)
        try:
            await anuncio.add_reaction("🎉")
            await anuncio.add_reaction("🏆")
        except discord.HTTPException:
            pass

        try:
            dm_embed = discord.Embed(
                title="🎉 ¡Felicidades por tu ascenso!",
                description=f"Has subido al cargo de {rank.mention} en **{interaction.guild.name}**.",
                color=discord.Color.gold(),
            )
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass

        await interaction.response.send_message(
            f"Anuncio enviado en {channel.mention}, rol otorgado y DM enviado.", ephemeral=True
        )

    @promote.error
    async def promote_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "No tienes permisos para usar este comando.", ephemeral=True
            )
        else:
            raise error

    @app_commands.command(name="demote", description="Anuncia que un usuario bajo de cargo y le retira el rol")
    @app_commands.describe(user="Usuario que bajo de cargo", rank="Rol del cargo que se le retirara al usuario")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def demote(self, interaction: discord.Interaction, user: discord.Member, rank: discord.Role):
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

        try:
            await user.remove_roles(rank, reason=f"Descenso aplicado por {interaction.user}")
        except discord.Forbidden:
            await interaction.response.send_message(
                "No tengo permisos para retirar ese rol. Verifica que mi rol este por encima de "
                f"{rank.mention} en la jerarquia del servidor.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="📉 Descenso de Staff",
            description=(
                f"### {user.mention} ha bajado de cargo\n"
                f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
            ),
            color=discord.Color.dark_orange(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="👤 Usuario", value=user.mention, inline=True)
        embed.add_field(name="📋 Cargo retirado", value=rank.mention, inline=True)
        embed.add_field(name="🛡️ Actualizado por", value=interaction.user.mention, inline=False)
        embed.set_footer(
            text=f"{interaction.guild.name} • Actualización de staff",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None,
        )

        await channel.send(embed=embed)

        try:
            dm_embed = discord.Embed(
                title="📋 Actualización de tu cargo",
                description=f"Has bajado del cargo de {rank.mention} en **{interaction.guild.name}**.",
                color=discord.Color.dark_orange(),
            )
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass

        await interaction.response.send_message(
            f"Anuncio enviado en {channel.mention}, rol retirado y DM enviado.", ephemeral=True
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
