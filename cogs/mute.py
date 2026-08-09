from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

from utils.history import add_infraction


class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mute", description="Silenciar temporalmente a un usuario")
    @app_commands.describe(
        user="Usuario a silenciar",
        minutes="Duracion del silencio en minutos",
        reason="Motivo del silencio",
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        minutes: int,
        reason: str,
    ):
        duration = timedelta(minutes=minutes)
        await user.timeout(duration, reason=reason)

        add_infraction(
            guild_id=interaction.guild.id,
            user_id=user.id,
            moderator_id=interaction.user.id,
            action=f"Mute ({minutes} min)",
            reason=reason,
        )

        embed = discord.Embed(title="Usuario silenciado", color=discord.Color.orange())
        embed.add_field(name="Usuario", value=user.mention, inline=True)
        embed.add_field(name="Duracion", value=f"{minutes} minutos", inline=True)
        embed.add_field(name="Moderador", value=interaction.user.mention, inline=True)
        embed.add_field(name="Motivo", value=reason, inline=False)
        await interaction.response.send_message(embed=embed)

    @mute.error
    async def mute_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "No tienes permisos para usar este comando.", ephemeral=True
            )
        else:
            raise error


async def setup(bot):
    await bot.add_cog(Mute(bot))
