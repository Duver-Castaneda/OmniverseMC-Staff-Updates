import discord
from discord import app_commands
from discord.ext import commands

from utils.history import add_infraction


class Warn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="warn", description="Advertir a un usuario")
    @app_commands.describe(user="Usuario a advertir", reason="Motivo de la advertencia")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        entry = add_infraction(
            guild_id=interaction.guild.id,
            user_id=user.id,
            moderator_id=interaction.user.id,
            action="Warn",
            reason=reason,
        )

        embed = discord.Embed(title="Usuario advertido", color=discord.Color.yellow())
        embed.add_field(name="Usuario", value=user.mention, inline=True)
        embed.add_field(name="Moderador", value=interaction.user.mention, inline=True)
        embed.add_field(name="Motivo", value=reason, inline=False)
        await interaction.response.send_message(embed=embed)

        try:
            await user.send(f"Fuiste advertido en **{interaction.guild.name}**.\nMotivo: {reason}")
        except discord.Forbidden:
            pass

    @warn.error
    async def warn_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "No tienes permisos para usar este comando.", ephemeral=True
            )
        else:
            raise error


async def setup(bot):
    await bot.add_cog(Warn(bot))
