import json
import os

import discord
from discord import app_commands
from discord.ext import commands

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "staff_channels.json")

# Emojis del embed que se envia en el canal de staff.
# :user:, :modmail: y :adm: no rendeaban en tu captura (aparecian como texto),
# asi que aqui van con emojis normales de Discord como reemplazo.
# Si tienes los codigos reales de tus emojis personalizados (formato <:nombre:id>),
# reemplaza estos 3 valores por esos codigos.
EMOJI_STAFF_CANAL = "👥"
EMOJI_MOTIVO_CANAL = "📋"
EMOJI_RESPONSABLE_CANAL = "🛡️"

# Emojis del mensaje directo (MD). Estos si son tus codigos reales.
EMOJI_STAFF_MD = "<:staff:1536149244271001602>"
EMOJI_INFO_MD = "<:info:1536150266926334022>"


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


def puede_gestionar_rol(actor: discord.Member, rank: discord.Role) -> bool:
    """
    Verifica si 'actor' tiene jerarquia suficiente para otorgar o retirar 'rank'.
    Solo el dueno del servidor se salta esta verificacion.
    Cualquier otro usuario (incluso con permiso de Administrator) necesita que
    su rol mas alto este ESTRICTAMENTE por encima del rol que intenta gestionar
    (no se permite igual ni menor). Esto evita que dos roles con permiso de
    Administrator (por ejemplo Dev y Admin) se puedan gestionar entre si sin
    importar cual este mas arriba en la jerarquia real del servidor.
    """
    if actor.id == actor.guild.owner_id:
        return True
    return actor.top_role.position > rank.position


class StaffUpdates(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set-staff-channel", description="Define el canal donde se anuncian los cambios de staff")
    @app_commands.describe(channel="Canal donde se enviaran los anuncios de staff")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_staff_channel_cmd(self, interaction: discord.Interaction, channel: discord.TextChannel):
        set_staff_channel(interaction.guild.id, channel.id)

        embed = discord.Embed(
            title="Canal de staff configurado",
            description=f"Los cambios de staff se anunciaran en {channel.mention}.",
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

    async def _procesar_cambio(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        old_rank: discord.Role,
        new_rank: discord.Role,
        accion: str,
    ):
        """
        Logica compartida entre /promote y /demote.
        accion debe ser "Promote" o "Demote".
        """
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

        if not puede_gestionar_rol(interaction.user, old_rank):
            await interaction.response.send_message(
                f"No puedes gestionar el rol {old_rank.mention} porque esta al mismo nivel o "
                "por encima de tu rol mas alto.",
                ephemeral=True,
            )
            return

        if not puede_gestionar_rol(interaction.user, new_rank):
            await interaction.response.send_message(
                f"No puedes otorgar el rol {new_rank.mention} porque esta al mismo nivel o por "
                "encima de tu rol mas alto.",
                ephemeral=True,
            )
            return

        try:
            await user.remove_roles(old_rank, reason=f"{accion} aplicado por {interaction.user}")
            await user.add_roles(new_rank, reason=f"{accion} aplicado por {interaction.user}")
        except discord.Forbidden:
            await interaction.response.send_message(
                "No tengo permisos para gestionar esos roles. Verifica que mi rol este por encima "
                f"de {old_rank.mention} y {new_rank.mention} en la jerarquia del servidor.",
                ephemeral=True,
            )
            return

        etiqueta_es = "Ascenso" if accion == "Promote" else "Descenso"
        color = discord.Color.from_rgb(230, 70, 45)

        # ---------- Mensaje en el canal (embed) ----------
        embed = discord.Embed(
            title="📣 STAFF UPDATE",
            description=(
                f"{EMOJI_STAFF_CANAL} **STAFF:** {user.mention}\n\n"
                f"`{old_rank.name}` > `{new_rank.name}`\n\n"
                f"{EMOJI_MOTIVO_CANAL} **Motivo:** {accion}\n\n"
                f"{EMOJI_RESPONSABLE_CANAL} **Responsable:** {interaction.user}"
            ),
            color=color,
            timestamp=discord.utils.utcnow(),
        )
        await channel.send(embed=embed)

        # ---------- Mensaje directo (sin embed) ----------
        dm_texto = (
            f"{EMOJI_STAFF_MD} **Cargo Actualizado**\n"
            f"> Tu cargo como miembro del staff de **{interaction.guild.name}** ha sido "
            f"actualizado correctamente.\n"
            f" {EMOJI_INFO_MD} __**Información**__\n"
            f"> » {old_rank.name} > {new_rank.name} ({etiqueta_es})\n"
            f"> » Encargado: {interaction.user.mention}"
        )
        try:
            await user.send(dm_texto)
        except discord.Forbidden:
            pass

        await interaction.response.send_message(
            f"Anuncio enviado en {channel.mention}, roles actualizados y MD enviado.", ephemeral=True
        )

    @app_commands.command(name="promote", description="Anuncia que un usuario subio de cargo y actualiza sus roles")
    @app_commands.describe(
        user="Usuario que subio de cargo",
        old_rank="Rol anterior que se le retirara",
        new_rank="Rol nuevo (mas alto) que se le otorgara",
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def promote(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        old_rank: discord.Role,
        new_rank: discord.Role,
    ):
        await self._procesar_cambio(interaction, user, old_rank, new_rank, accion="Promote")

    @promote.error
    async def promote_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "No tienes permisos para usar este comando.", ephemeral=True
            )
        else:
            raise error

    @app_commands.command(name="demote", description="Anuncia que un usuario bajo de cargo y actualiza sus roles")
    @app_commands.describe(
        user="Usuario que bajo de cargo",
        old_rank="Rol anterior que se le retirara",
        new_rank="Rol nuevo (mas bajo) que se le otorgara",
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def demote(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        old_rank: discord.Role,
        new_rank: discord.Role,
    ):
        await self._procesar_cambio(interaction, user, old_rank, new_rank, accion="Demote")

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
