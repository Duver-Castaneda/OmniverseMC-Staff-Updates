import discord
from discord import app_commands
from discord.ext import commands


class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="unban", description="Desbanear a un usuario por su ID")
    @app_commands.describe(user_id="ID del usuario a desbanear")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str):
        try:
            user_id_int = int(user_id)
        except ValueError:
            await interaction.response.send_message("Ese ID no es valido.", ephemeral=True)
            return

        try:
            ban_entry = await interaction.guild.fetch_ban(discord.Object(id=user_id_int))
        except discord.NotFound:
            await interaction.response.send_message(
                "Ese usuario no esta baneado.", ephemeral=True
            )
            return

        await interaction.guild.unban(ban_entry.user, reason=f"Desbaneado por {interaction.user}")

        embed = discord.Embed(title="Usuario desbaneado", color=discord.Color.green())
        embed.add_field(name="Usuario", value=f"{ban_entry.user}", inline=True)
        embed.add_field(name="Moderador", value=interaction.user.mention, inline=True)
        await interaction.response.send_message(embed=embed)

    @unban.error
    async def unban_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "No tienes permisos para usar este comando.", ephemeral=True
            )
        else:
            raise error


async def setup(bot):
    await bot.add_cog(Unban(bot))
