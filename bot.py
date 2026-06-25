import asyncio

import asyncpg
import discord
from discord import app_commands
from discord.ext import commands

from checks import is_owner
from config import DATABASE_URL, TARGET_CHANNEL_IDS, TOKEN

intents = discord.Intents.default()
intents.message_content = True


class MusicLedgerBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.db_pool = None
        self._initialized = False

    async def setup_hook(self):
        pass

    async def _init_database(self):
        print("[Database] Connecting to PostgreSQL database pool...")
        while True:
            try:
                self.db_pool = await asyncpg.create_pool(dsn=DATABASE_URL)
                print("[Database] Successfully connected to PostgreSQL database pool!")
                async with self.db_pool.acquire() as conn:
                    with open("schema.sql") as f:
                        await conn.execute(f.read())
                    await conn.execute(
                        "ALTER TABLE tracked_media ADD COLUMN IF NOT EXISTS message_content TEXT NOT NULL DEFAULT '';"
                    )
                    await conn.execute(
                        "CREATE INDEX IF NOT EXISTS idx_content_trgm ON tracked_media USING gin (lower(message_content) gin_trgm_ops);"
                    )
                    print("[Database] Schema initialized.")
                self._initialized = True
                break
            except (ConnectionRefusedError, asyncpg.exceptions.CannotConnectNowError):
                print(
                    "[Database] PostgreSQL is initializing system components... Retrying in 2 seconds..."
                )
                await asyncio.sleep(2)
            except Exception as e:
                print(f"[Database] Unexpected container runtime intersection: {e}")
                print("[Database] Re-attempting connection sequence in 5 seconds...")
                await asyncio.sleep(5)


bot = MusicLedgerBot()


@bot.event
async def on_ready():
    if bot._initialized:
        return
    print(f"Logged in as {bot.user}.")
    print(
        f"[Initialization] Successfully targeted {len(TARGET_CHANNEL_IDS)} source channels: {TARGET_CHANNEL_IDS}"
    )
    await bot._init_database()
    await bot.load_extension("cogs.media")
    await bot.tree.sync()
    print("[Initialization] Commands synced.")


@bot.tree.command(
    name="reload", description="Reload the media commands cog without restarting the bot"
)
@is_owner()
async def reload_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        await bot.reload_extension("cogs.media")
        await bot.tree.sync()
        await interaction.followup.send("✅ Reloaded the `cogs.media` cog.")
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to reload cog: `{e}`")


@reload_command.error
async def reload_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    if isinstance(error, app_commands.errors.CheckFailure):
        await interaction.response.send_message(
            "❌ You are not authorized to use this command.", ephemeral=True
        )


if __name__ == "__main__":
    bot.run(TOKEN)
