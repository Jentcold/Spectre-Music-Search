import os
import re
import asyncio
import datetime
import discord
import asyncpg
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Database connection credentials
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")  # Docker overrides this to 'postgres_db' automatically

# Parse multiple authorized developer/owner IDs from .env
OWNER_DISCORD_IDS = []
raw_owners = os.getenv("OWNER_DISCORD_IDS")
if raw_owners:
    for oid in raw_owners.split(","):
        cleaned = oid.strip()
        if cleaned.isdigit():
            OWNER_DISCORD_IDS.append(int(cleaned))

# Parse multiple search target channels from .env
TARGET_CHANNEL_IDS = []
raw_channels = os.getenv("MASHUP_CHANNEL_IDS")
if raw_channels:
    for cid in raw_channels.split(","):
        cleaned = cid.strip()
        if cleaned.isdigit():
            TARGET_CHANNEL_IDS.append(int(cleaned))

# Needed message intents permission for the bot
intents = discord.Intents.default()
intents.message_content = True

# Databse connection 
class MusicLedgerBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.db_pool = None

    async def setup_hook(self):
        print("[Database] Connecting to PostgreSQL database pool...")
        
        # backoff retry loop
        while True:
            try:
                self.db_pool = await asyncpg.create_pool(
                    user=DB_USER,
                    password=DB_PASSWORD,
                    database=DB_NAME,
                    host=DB_HOST,
                    port=5432
                )
                print("[Database] Successfully connected to PostgreSQL database pool!")
                break
            except (ConnectionRefusedError, asyncpg.exceptions.CannotConnectNowError):
                print("[Database] PostgreSQL is initializing system components... Retrying in 2 seconds...")
                await asyncio.sleep(2)
            except Exception as e:
                print(f"[Database] Unexpected container runtime intersection: {e}")
                print("[Database] Re-attempting connection sequence in 5 seconds...")
                await asyncio.sleep(5)

        await self.tree.sync()

bot = MusicLedgerBot()

# Regex strict captures
STREAM_RE = re.compile(r"(https?://(?:www\.)?untitled\.stream/library/project/[a-zA-Z0-9_]+)", re.IGNORECASE)
YOUTUBE_RE = re.compile(r"(https?://(?:www\.)?(?:youtube\.com/[^\s>)]+|youtu\.be/[^\s>)]+|youtube\.com/shorts/[a-zA-Z0-9_\-]+))", re.IGNORECASE)

VALID_AUDIO_EXTENSIONS = ('.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.aiff')

def clean_filename(filename: str, author_fallback: str = "Unknown") -> str:
    from pathlib import Path
    if not filename or not isinstance(filename, str):
        return f"{author_fallback}'s Audio Track"
    name = Path(filename).stem
    cleaned = re.sub(r"[\s_\-]+", " ", name).strip()
    if not cleaned or len(cleaned) < 1:
        return f"{author_fallback}'s Audio Track"
    return cleaned


# ---------- INTERACTIVE FILTER-ENABLED PAGINATION VIEW (embed) ----------

class SearchPagination(discord.ui.View):
    def __init__(self, keyword: str, all_results: list):
        super().__init__(timeout=120)
        self.keyword = keyword
        self.all_results = all_results  
        self.filtered_results = all_results  
        
        self.current_page = 0
        self.per_page = 6
        self.current_filter = "ALL"  
        self.update_button_states()

    def update_button_states(self):
        total_items = len(self.filtered_results)
        self.total_pages = (total_items - 1) // self.per_page + 1 if total_items > 0 else 1
        
        if self.current_page >= self.total_pages:
            self.current_page = max(0, self.total_pages - 1)

        self.prev_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page >= self.total_pages - 1

        self.filter_all.style = discord.ButtonStyle.success if self.current_filter == "ALL" else discord.ButtonStyle.secondary
        self.filter_stream.style = discord.ButtonStyle.success if self.current_filter == "STREAM" else discord.ButtonStyle.secondary
        self.filter_youtube.style = discord.ButtonStyle.success if self.current_filter == "YOUTUBE" else discord.ButtonStyle.secondary
        self.filter_file.style = discord.ButtonStyle.success if self.current_filter == "FILE" else discord.ButtonStyle.secondary

    def get_current_page_embed(self) -> discord.Embed:
        filter_labels = {"ALL": "Everything", "STREAM": "Untitled.stream", "YOUTUBE": "YouTube Links", "FILE": "Audio Files"}
        
        embed = discord.Embed(
            title=f"🔎 Unified Media Search: '{self.keyword}'",
            description=f"Showing: **{filter_labels[self.current_filter]}**\nPage {self.current_page + 1} of {self.total_pages} ({len(self.filtered_results)} filtered matches)",
            color=discord.Color.blurple()
        )
        
        if not self.filtered_results:
            embed.add_field(name="No Matches Found", value=f"No entries matched the query '{self.keyword}' here.", inline=False)
            return embed

        start_idx = self.current_page * self.per_page
        end_idx = start_idx + self.per_page
        page_items = self.filtered_results[start_idx:end_idx]
        
        for index, data in enumerate(page_items, start=start_idx + 1):
            if data['asset_type'] == "STREAM":
                type_label = "📀 `[UNTITLED.STREAM]`"
            elif data['asset_type'] == "YOUTUBE":
                type_label = "📺 `[YOUTUBE]`"
            else:
                type_label = "🎵 `[AUDIO FILE]`"

            date_val = data['date_shared'].strftime("%Y-%m-%d") if isinstance(data['date_shared'], (datetime.date, datetime.datetime)) else data['date_shared']

            value_details = (
                f"👤 **Shared by:** {data['uploader']}  •  📅 {date_val}\n"
                f"🏷️ **Type:** {type_label}\n"
            )
            if data['url'] != "N/A": 
                value_details += f"🔗 **Source Link:** [Listen Here]({data['url']})\n"
            if data['original_message_url']: 
                value_details += f"➡️ [Jump to Context Message]({data['original_message_url']})"
            # Line separator 
            embed.add_field(
                    name="\u200b",
                    value="─── ─── ─── ─── ─── ─── ─── ─── ───", 
                    inline=False
                )
            
            embed.add_field(name=f"{index}. {data['title']}", value=value_details, inline=False)
        return embed

    async def apply_filter(self, interaction: discord.Interaction, filter_type: str):
        self.current_filter = filter_type
        self.current_page = 0  
        
        if filter_type == "ALL":
            self.filtered_results = self.all_results
        else:
            self.filtered_results = [item for item in self.all_results if item['asset_type'] == filter_type]

        self.update_button_states()
        await interaction.response.edit_message(embed=self.get_current_page_embed(), view=self)

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary, row=0)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_button_states()
            await interaction.response.edit_message(embed=self.get_current_page_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.primary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_button_states()
            await interaction.response.edit_message(embed=self.get_current_page_embed(), view=self)

    @discord.ui.button(label="All", style=discord.ButtonStyle.success, row=1)
    async def filter_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.apply_filter(interaction, "ALL")

    @discord.ui.button(label="📀 Untitled", style=discord.ButtonStyle.secondary, row=1)
    async def filter_stream(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.apply_filter(interaction, "STREAM")

    @discord.ui.button(label="📺 YouTube", style=discord.ButtonStyle.secondary, row=1)
    async def filter_youtube(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.apply_filter(interaction, "YOUTUBE")

    @discord.ui.button(label="🎵 Files", style=discord.ButtonStyle.secondary, row=1)
    async def filter_file(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.apply_filter(interaction, "FILE")


# ---------- PIPELINE TO SAVE DETECTED ASSETS INTO POSTGRES ----------

async def process_and_save_message(message: discord.Message) -> int:
    from stream_meta import fetch_stream_title
    from youtube_meta import fetch_youtube_title

    if message.author.bot:
        return 0

    stream_links = STREAM_RE.findall(message.content)
    yt_links = YOUTUBE_RE.findall(message.content)
    assets_to_log = []

    for link in stream_links:
        assets_to_log.append(("STREAM", link))
    for link in yt_links:
        assets_to_log.append(("YOUTUBE", link))

    for attachment in message.attachments:
        fname = attachment.filename
        if fname and any(fname.lower().endswith(ext) for ext in VALID_AUDIO_EXTENSIONS):
            assets_to_log.append(("FILE", attachment.url, fname))

    if not assets_to_log:
        return 0

    items_saved = 0
    date_obj = message.created_at.date()

    for asset in assets_to_log:
        label = asset[0]
        url = asset[1]
        title = "Unknown Track"

        if label == "STREAM":
            fetched_title = await fetch_stream_title(url)
            title = fetched_title if fetched_title else "Removed / Private untitled.stream Album"
            await asyncio.sleep(0.5)
        elif label == "YOUTUBE":
            fetched_title = await fetch_youtube_title(url)
            if fetched_title:
                title = fetched_title
            elif "shorts/" in url.lower():
                title = "YouTube Shorts Video Match"
            else:
                title = "Removed / Unavailable YouTube Video"
            await asyncio.sleep(0.5)
        elif label == "FILE":
            title = clean_filename(asset[2], message.author.display_name)

        async with bot.db_pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO tracked_media (asset_type, url, title, uploader, date_shared, original_message_url, channel_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (original_message_url) DO NOTHING;
                    """,
                    label, url, title, message.author.display_name, date_obj, message.jump_url, message.channel.id
                )
                items_saved += 1
            except Exception as e:
                print(f"[Database Error] Failed saving track asset: {e}")
        
    return items_saved


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}.")
    print(f"[Initialization] Successfully targeted {len(TARGET_CHANNEL_IDS)} source channels: {TARGET_CHANNEL_IDS}")


@bot.event
async def on_message(message: discord.Message):
    if message.channel.id not in TARGET_CHANNEL_IDS:
        return
    await process_and_save_message(message)


# ---------- ASYNC TIMELINE SYNC ENGINE ----------

def is_owner():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id in OWNER_DISCORD_IDS
    return app_commands.check(predicate)

@bot.tree.command(name="sync", description="Scan ALL historical messages and backfill database ledger values")
@is_owner()
async def sync_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    if not TARGET_CHANNEL_IDS:
        await interaction.followup.send("Channel setup configuration is missing or invalid.")
        return

    await interaction.followup.send(f"Commencing Database Sync...")
    
    synced_count = 0
    total_scanned = 0
    
    for channel_id in TARGET_CHANNEL_IDS:
        target_channel = bot.get_channel(channel_id)
        if not target_channel:
            continue
            
        print(f"[Sync Loop] Now pulling historic entries from: #{target_channel.name}")
        
        async for message in target_channel.history(limit=None, oldest_first=False):
            total_scanned += 1
            if total_scanned % 100 == 0:
                print(f"[Sync Sweep] Evaluated {total_scanned} context frames... Inserted {synced_count} entries.")

            was_logged_count = await process_and_save_message(message)
            synced_count += was_logged_count

    await interaction.followup.send(f"✅ Database Sync Complete! Scanned {total_scanned} messages and updated **{synced_count}** entries.")

@sync_command.error
async def sync_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.CheckFailure):
        await interaction.response.send_message("❌ You are not authorized to use this command.", ephemeral=True)


# ---------- FAST ASYNC DATABASE SEARCH ----------

@bot.tree.command(name="search", description="Search all indexed assets simultaneously out of PostgreSQL")
async def search_command(interaction: discord.Interaction, keyword: str):
    await interaction.response.defer()
    
    async with bot.db_pool.acquire() as conn:
        # Lower the threshold slightly to let close fuzzy matches join the combined pool
        await conn.execute("SET LOCAL pg_trgm.similarity_threshold = 0.3;")
        
        # Combined query: pulls records matching either rule and returns them together
        sql_query = """
            SELECT asset_type, url, title, uploader, date_shared, original_message_url 
            FROM tracked_media
            WHERE (lower(title) % lower($1) OR lower(uploader) % lower($1))
               OR (lower(title) LIKE '%' || lower($1) || '%')
               OR (lower(uploader) LIKE '%' || lower($1) || '%')
            ORDER BY 
                GREATEST(similarity(lower(title), lower($1)), similarity(lower(uploader), lower($1))) DESC
            LIMIT 30;
        """
        rows = await conn.fetch(sql_query, keyword)

    if not rows:
        await interaction.followup.send(f"❌ No matching tracks found across the database for '{keyword}'.")
        return

    # Convert Postgres RecordProxy records into dictionary arrays for the UI view
    cleaned_results = [dict(row) for row in rows]

    view = SearchPagination(keyword=keyword, all_results=cleaned_results)
    await interaction.followup.send(embed=view.get_current_page_embed(), view=view)

if __name__ == "__main__":
    bot.run(TOKEN)