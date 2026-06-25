import asyncio
import logging

import asyncpg
import discord
from discord.ext import commands

from config import DATABASE_URL, GUILD_ID, TARGET_CHANNEL_IDS, TOKEN

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logging.getLogger("discord").setLevel(logging.DEBUG)
logging.getLogger("discord.http").setLevel(logging.DEBUG)
logging.getLogger("discord.gateway").setLevel(logging.DEBUG)
logging.getLogger("discord.app_commands").setLevel(logging.DEBUG)
log = logging.getLogger("bot")

intents = discord.Intents.default()
intents.message_content = True


class MusicLedgerBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.db_pool = None
        self._initialized = False
        self._guild = discord.Object(id=GUILD_ID) if GUILD_ID else None

    async def setup_hook(self):
        log.info("setup_hook: GUILD_ID=%s, _guild=%s", GUILD_ID, self._guild)

        await self._init_database()

        await self.load_extension("cogs.media")
        log.info("setup_hook: Loaded cogs.media.")

        for cmd in self.tree.get_commands():
            log.info("setup_hook: Global command registered: %s", cmd.name)
        if self._guild:
            guild_cmds = self.tree.get_commands(guild=self._guild)
            log.info(
                "setup_hook: Guild commands registered for %s: %s",
                self._guild.id,
                [c.name for c in guild_cmds] or "(none)",
            )

        synced = await self.tree.sync(guild=self._guild)
        log.info(
            "setup_hook: Synced %d commands to guild %s: %s",
            len(synced), GUILD_ID, [c.name for c in synced],
        )

    async def _init_database(self):
        log.info("[Database] Connecting to PostgreSQL database pool...")
        while True:
            try:
                self.db_pool = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=5)
                log.info("[Database] Successfully connected to PostgreSQL database pool!")
                async with self.db_pool.acquire() as conn:
                    with open("schema.sql") as f:
                        await conn.execute(f.read())
                    log.info("[Database] Schema initialized.")
                self._initialized = True
                break
            except (ConnectionRefusedError, asyncpg.exceptions.CannotConnectNowError):
                log.warning(
                    "[Database] PostgreSQL is initializing system components... Retrying in 2 seconds..."
                )
                await asyncio.sleep(2)
            except Exception as e:
                log.error("[Database] Unexpected error: %s", e, exc_info=True)
                log.info("[Database] Re-attempting connection sequence in 5 seconds...")
                await asyncio.sleep(5)


bot = MusicLedgerBot()


@bot.event
async def on_ready():
    log.info("on_ready: bot.user=%s, _initialized=%s", bot.user, bot._initialized)
    log.info(
        "on_ready: Targeting %d source channels: %s",
        len(TARGET_CHANNEL_IDS), TARGET_CHANNEL_IDS,
    )

    all_global = bot.tree.get_commands()
    log.info("on_ready: Global commands in tree: %s", [c.name for c in all_global])

    if bot._guild:
        guild_cmds = bot.tree.get_commands(guild=bot._guild)
        log.info(
            "on_ready: Guild commands in tree for %s: %s",
            bot._guild.id,
            [c.name for c in guild_cmds] or "(none)",
        )


if __name__ == "__main__":
    log.info("Starting bot...")
    bot.run(TOKEN, log_handler=None, log_level=logging.DEBUG)
