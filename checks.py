import discord
from discord import app_commands

from config import OWNER_DISCORD_IDS


def is_owner():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id in OWNER_DISCORD_IDS

    return app_commands.check(predicate)
