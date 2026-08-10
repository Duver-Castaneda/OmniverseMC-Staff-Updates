import json
import os

import discord
from discord import app_commands
from discord.ext import commands

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "staff_channels.json")

# Emojis usados tanto en el embed del canal como en el mensaje directo (MD).
EMOJI_STAFF = "<:staff:1536149244271001602>"
EMOJI_INFO = "<:info:1536150266926334022>"
EMOJI_HIGH = "<:High:1534591103037345904>"

# Alias para el embed del canal (misma referencia, distinto nombre por claridad)
EMOJI_STAFF_CANAL = EMOJI_STAFF
EMOJI_MOTIVO_CANAL = EMOJI_INFO
EMOJI_RESPONSABLE_CANAL = EMOJI_HIGH

# Alias para el mensaje directo (MD)
EMOJI_STAFF_MD = EMOJI_STAFF
EMOJI_INFO_MD = EMOJI_INFO
EMOJI_HIGH_MD = EMOJI_HIGH


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

        if old_rank.id == new_rank.id:
            await interaction.response.send_message(
                "El rol anterior y el rol nuevo no pueden ser el mismo.",
                ephemeral=True,
            )
            return

        if old_rank not in user.roles:
            await interaction.response.send_message(
                f"{user.mention} no tiene actualmente el rol {old_rank.mention}, no se puede "
                "procesar este cambio.",
                ephemeral=True,
            )
            return

        if accion == "Promote" and new_rank.position <= old_rank.position:
            await interaction.response.send_message(
                f"{new_rank.mention} no esta por encima de {old_rank.mention}. Para un ascenso el "
                "rol nuevo debe ser superior al anterior.",
                ephemeral=True,
            )
            return

        if accion == "Demote" and new_rank.position >= old_rank.position:
            await interaction.response.send_message(
                f"{new_rank.mention} no esta por debajo de {old_rank.mention}. Para un descenso el "
                "rol nuevo debe ser inferior al anterior.",
                ephemeral=True,
            )
            return

        try:
            await user.remove_roles(old_rank, reason=f"{accion} aplicado por {interaction.user}")
        except discord.HTTPException:
            await interaction.response.send_message(
                "No pude retirar el rol anterior. Verifica que mi rol este por encima de "
                f"{old_rank.mention} en la jerarquia del servidor.",
                ephemeral=True,
            )
            return

        try:
            await user.add_roles(new_rank, reason=f"{accion} aplicado por {interaction.user}")
        except discord.HTTPException:
            # El retiro del rol anterior ya se aplico: revertimos para no dejar
            # al usuario sin ningun rol de staff.
            try:
                await user.add_roles(old_rank, reason="Rollback automatico tras fallo al otorgar el nuevo rol")
            except discord.HTTPException:
                pass
            await interaction.response.send_message(
                "No pude otorgar el rol nuevo, asi que reverti el cambio. Verifica que mi rol este "
                f"por encima de {new_rank.mention} en la jerarquia del servidor.",
                ephemeral=True,
            )
            return

        etiqueta_es = "Ascenso" if accion == "Promote" else "Descenso"
        color = discord.Color.from_rgb(230, 70, 45)

        # ---------- Mensaje en el canal (embed, con campos separados para que se vea mas largo) ----------
        # El titulo grande va en la descripcion con "# " porque el campo title
        # de un embed no interpreta markdown (el "#" se veria como texto plano ahi).
        embed = discord.Embed(
            description="# 📣 STAFF UPDATE",
            color=color,
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(
            name=f"{EMOJI_STAFF_CANAL} STAFF",
            value=f"{user.mention}\n\n`{old_rank.name}` > `{new_rank.name}`",
            inline=False,
        )
        embed.add_field(
            name=f"{EMOJI_MOTIVO_CANAL} Motivo",
            value=accion,
            inline=False,
        )
        embed.add_field(
            name=f"{EMOJI_RESPONSABLE_CANAL} Responsable",
            value=str(interaction.user),
            inline=False,
        )
        await channel.send(embed=embed)

        # ---------- Mensaje directo (como embed, mismo contenido y espacios) ----------
        dm_embed = discord.Embed(
            title=f"{EMOJI_STAFF_MD} Cargo Actualizado",
            description=(
                f"> Tu cargo como miembro del staff de **{interaction.guild.name}** ha sido "
                f"actualizado correctamente.\n"
                f"\n"
                f"{EMOJI_INFO_MD} __**Información**__\n"
                f"\n"
                f"> » `{old_rank.name}` > `{new_rank.name}` ({etiqueta_es})\n"
                f"> » {EMOJI_HIGH_MD} Encargado: {interaction.user.mention}"
            ),
            color=color,
        )
        try:
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass

        await interaction.response.send_message(
            f"Anuncio enviado en {channel.mention}, roles actualizados y MD enviado.", ephemeral=True
        )

    async def _procesar_ingreso(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        new_rank: discord.Role,
        rank_ingreso: str,
    ):
        """
        Logica para /ingreso. A diferencia de /promote y /demote, aqui no hay
        old_rank que retirar: el usuario es nuevo en el staff y solo se le
        otorga new_rank. rank_ingreso es el texto que se muestra como "rol
        anterior" en el embed (por defecto "User").
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

        if not puede_gestionar_rol(interaction.user, new_rank):
            await interaction.response.send_message(
                f"No puedes otorgar el rol {new_rank.mention} porque esta al mismo nivel o por "
                "encima de tu rol mas alto.",
                ephemeral=True,
            )
            return

        if user.get_role(new_rank.id) is not None:
            await interaction.response.send_message(
                f"{user.mention} ya tiene el rol {new_rank.mention}.",
                ephemeral=True,
            )
            return

        try:
            await user.add_roles(new_rank, reason=f"Ingreso aplicado por {interaction.user}")
        except discord.HTTPException:
            await interaction.response.send_message(
                "No tengo permisos para gestionar ese rol. Verifica que mi rol este por encima "
                f"de {new_rank.mention} en la jerarquia del servidor.",
                ephemeral=True,
            )
            return

        color = discord.Color.from_rgb(230, 70, 45)

        # ---------- Mensaje en el canal (embed, con campos separados para que se vea mas largo) ----------
        embed = discord.Embed(
            description="# 📣 STAFF UPDATE",
            color=color,
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(
            name=f"{EMOJI_STAFF_CANAL} STAFF",
            value=f"{user.mention}\n\n`{rank_ingreso}` > `{new_rank.name}`",
            inline=False,
        )
        embed.add_field(
            name=f"{EMOJI_MOTIVO_CANAL} Motivo",
            value="Ingreso",
            inline=False,
        )
        embed.add_field(
            name=f"{EMOJI_RESPONSABLE_CANAL} Responsable",
            value=str(interaction.user),
            inline=False,
        )
        await channel.send(embed=embed)

        # ---------- Mensaje directo (como embed, mismo contenido y espacios) ----------
        dm_embed = discord.Embed(
            title=f"{EMOJI_STAFF_MD} Cargo Actualizado",
            description=(
                f"> Tu cargo como miembro del staff de **{interaction.guild.name}** ha sido "
                f"actualizado correctamente.\n"
                f"\n"
                f"{EMOJI_INFO_MD} __**Información**__\n"
                f"\n"
                f"> » `{rank_ingreso}` > `{new_rank.name}`\n"
                f"> » {EMOJI_HIGH_MD} Encargado: {interaction.user.mention}"
            ),
            color=color,
        )
        try:
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass

        await interaction.response.send_message(
            f"Anuncio enviado en {channel.mention}, rol otorgado y MD enviado.", ephemeral=True
        )

    @app_commands.command(name="ingreso", description="Anuncia el ingreso de un nuevo miembro al staff y le otorga su rol")
    @app_commands.describe(
        user="Usuario que ingresa al staff",
        new_rank="Rol que se le otorgara",
        rank_ingreso="Texto a mostrar como rol anterior (por defecto: 'User')",
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def ingreso(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        new_rank: discord.Role,
        rank_ingreso: str = "User",
    ):
        await self._procesar_ingreso(interaction, user, new_rank, rank_ingreso)

    @ingreso.error
    async def ingreso_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "No tienes permisos para usar este comando.", ephemeral=True
            )
        else:
            raise error

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
