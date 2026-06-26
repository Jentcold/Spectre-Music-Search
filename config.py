import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

OWNER_DISCORD_IDS = []
raw_owners = os.getenv("OWNER_DISCORD_IDS")
if raw_owners:
    for oid in raw_owners.split(","):
        cleaned = oid.strip()
        if cleaned.isdigit():
            OWNER_DISCORD_IDS.append(int(cleaned))

TARGET_CHANNEL_IDS = []
raw_channels = os.getenv("MASHUP_CHANNEL_IDS")
if raw_channels:
    for cid in raw_channels.split(","):
        cleaned = cid.strip()
        if cleaned.isdigit():
            TARGET_CHANNEL_IDS.append(int(cleaned))
