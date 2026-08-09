import discord
from discord import app_commands
from discord.ext import commands


class Unmute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="unmute", description="Quitar el silencio a un usuario")
    @app_commands.describe(user="Usuario a desmutear")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, user: discord.Member):
        if user.timed_out_until is None:
            await interaction.response.send_message(
                f"{user.mention} no esta silenciado.", ephemeral=True
            )
            return

        await user.timeout(None)

        embed = discord.Embed(title="Usuario desmuteado", color=discord.Color.green())
        embed.add_field(name="Usuario", value=user.mention, inline=True)
        embed.add_field(name="Moderador", value=interaction.user.mention, inline=True)
        await interaction.response.send_message(embed=embed)

    @unmute.error
    async def unmute_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "No tienes permisos para usar este comando.", ephemeral=True
            )
        else:
            raise error


async def setup(bot):
    await bot.add_cog(Unmute(bot))
